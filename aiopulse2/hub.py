"""Acmeda Pulse Hub Interface."""
import asyncio
import functools
import json
import logging
import ssl
import time
from typing import Any, Callable, List, Optional

import async_timeout
import websockets

from . import const
from . import elements
from . import errors

_LOGGER = logging.getLogger(__name__)

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


class Hub:
    """Representation of an Acmeda Pulse v2 Hub."""

    def __init__(
        self, host: str, loop: Optional[asyncio.events.AbstractEventLoop] = None
    ):
        """Init the hub."""
        self.loop: asyncio.events.AbstractEventLoop = (loop or asyncio.get_event_loop())
        self.handshake = asyncio.Event()
        self.response_task = None
        self.running = False
        self.connected = False
        self.lasterrorlog = None
        self.serialok = False
        self.lastserialerror = None

        self.name = "Automate Pulse v2 Hub"
        self.id = None
        self.host = host
        self.wsuri = "wss://{}:443/rpc".format(self.host)
        self.mac_address = None
        self.firmware_ver = None
        self.model = None

        self.ws = None

        self.rollers = {}
        self.unknown_rollers = set()
        self.serialrunning = False

        self.handshake.clear()
        self.update_callbacks: List[Callable] = []
        self.heartbeatinterval = 2

    def __str__(self):
        """Returns string representation of the hub."""
        return (
            f"Name: {self.name!r} "
            f"ID: {self.id} "
            f"Host: {self.host} "
            f"MAC: {self.mac_address} "
            f"Firmware Version: {self.firmware_ver} "
            f"Model: {self.model} "
        )

    def callback_subscribe(self, callback: Callable):
        """Add a callback for hub updates."""
        self.update_callbacks.append(callback)

    def callback_unsubscribe(self, callback: Callable):
        """Remove a callback for hub updates."""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)

    def async_add_job(
        self, target: Callable[..., Any], *args: Any
    ) -> Optional[asyncio.Future]:
        """Add a job from within the event loop.

        This method must be run in the event loop.

        target: target to call.
        args: parameters for method to call.
        """
        task = None

        # Check for partials to properly determine if coroutine function
        check_target = target
        while isinstance(check_target, functools.partial):
            check_target = check_target.func

        if asyncio.iscoroutine(check_target):
            task = self.loop.create_task(target)  # type: ignore
        elif asyncio.iscoroutinefunction(check_target):
            task = self.loop.create_task(target(*args))
        else:
            task = self.loop.run_in_executor(None, target, *args)  # type: ignore

        return task

    def notify_callback(self, update_type=None):
        """Tell callback that the hub has been updated."""
        for callback in self.update_callbacks:
            self.async_add_job(callback, update_type)

    async def disconnect(self):
        """Disconnect from the hub."""
        _LOGGER.debug(f"{self.host}: Disconnecting")
        if self.ws:
            await self.ws.close()
        self.handshake.clear()
        _LOGGER.info(f"{self.host}: Disconnected")

    def response_parse(self, response: str):
        """Decode response."""
        for name, matcher in const.ALL_RESPONSES.items():
            match = matcher.match(response)
            if match:
                _LOGGER.debug(
                    f"{self.host}: Received response: {name} "
                    f"content: {match.groups()}"
                )
                handler = getattr(self, "handle_" + name.lower(), "")
                if handler:
                    handler(**match.groupdict())
                else:
                    _LOGGER.debug(f"No handler for {name}")
                return
        _LOGGER.debug(f"No match for: {response}")

    def handle_device_query_position_response(
        self, id: str, closedpercent: str, tiltpercent: str, signal: str
    ):
        self.rollers[id].closed_percent = int(closedpercent)
        self.rollers[id].tilt_percent = int(tiltpercent)
        self.rollers[id].set_signal(signal)

    def handle_device_query_name_response(self, id: str, name: str):
        self.rollers[id].name = name
        self.unknown_rollers.discard(id)
        self.rollers[id].notify_callback()

    async def serialrunner(self):
        """The running to get all required information from the hub

        This will exit when complete.
        """
        self.serialrunning = True
        try:
            while self.unknown_rollers:
                reader, writer = await asyncio.open_connection(self.host, port=1487)
                # Send off a request for all of the unknown rollers
                for rollerid in self.unknown_rollers:
                    buf = const.DEVICE_QUERY_NAME.format(id=rollerid)
                    writer.write(buf.encode())
                while True:
                    with async_timeout.timeout(3):
                        response = await reader.readuntil(b";")
                    if len(response) > 0:
                        _LOGGER.debug(f"recv < {response}")
                        self.response_parse(response.decode())
                    else:
                        break
                # Nothing has happened for > 30 seconds, disconnet
                writer.close()
                # Sleep 10 seconds to wait for things to settle down before maybe trying again
                await asyncio.sleep(10)
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            _LOGGER.info(f"Error in serial running: {e}")
        self.serialrunning = False

    async def runserial(self):
        """Runs a 'serial' connection to the hub to get additional information"""
        if self.serialrunning:
            # Already running, don't start again
            return
        self.serialrunning = True
        asyncio.create_task(self.serialrunner())

    async def send_payload(self, jscommand: dict):
        """Send payload to the hub

        See sendws for details.
        """
        if not self.running:
            raise errors.NotRunningException
        await self.handshake.wait()
        await self.sendws(jscommand)

    async def sendws(self, jscommand: dict):
        """Send jscommand over the websocket

        jscommand must be a Python dict, that will be converted to JSON
        """
        try:
            await self.ws.send(json.dumps(jscommand))
        except websockets.WebSocketException as e:
            _LOGGER.error("Error sending payload: {}".format(e))
            self.handshake.clear()

    async def heartbeat(self):
        while self.ws and self.ws.open:
            await self.sendws(
                {"method": "shadow", "src": "app", "id": int(time.time())}
            )
            await asyncio.sleep(self.heartbeatinterval)

    async def wsconsumer(self, msg: str):
        jsmsg = json.loads(msg)
        # print(json.dumps(jsmsg, indent="  "))
        if "result" not in jsmsg or "reported" not in jsmsg["result"]:
            _LOGGER.info(f"Got unknown WS response: {msg}")
            return
        self.connected = True
        if self.lasterrorlog is not None:
            _LOGGER.info(f"Connected to {self.host}")
            self.lasterrorlog = None
        data = jsmsg["result"]["reported"]
        self.name = data["name"]
        self.id = data["hubId"]
        self.mac_address = data["mac"]
        self.firmware_ver = data["firmware"]["version"]
        self.model = data["mfi"]["model"]

        for rollerid, roller in data["shades"].items():
            fresh = False
            if rollerid not in self.rollers:
                self.rollers[rollerid] = elements.Roller(self, rollerid)
                self.unknown_rollers.add(rollerid)
                fresh = True
                await self.runserial()
            newvals = {
                "signal": roller["rs"],
                "moving": not roller["is"],
                "online": roller["ol"],
                "closed_percent": int(roller["mp"]),
            }
            batteryinfo = const.WS_ROLLER_VOLTAGE.match(roller["vo"])
            if batteryinfo:
                newvals["battery"] = float(batteryinfo.group("voltage"))
                if fresh:
                    newvals["devicetypeshort"] = batteryinfo.group("type")
                    newvals["devicetype"] = const.TYPES.get(batteryinfo.group("type"))
                    newvals["version"] = batteryinfo.group("version")

            # Update the roller object, and track if there were any changes
            updated = False
            for attr, val in newvals.items():
                if getattr(self.rollers[rollerid], attr) != val:
                    setattr(self.rollers[rollerid], attr, val)
                    updated = True

            if updated:
                self.rollers[rollerid].notify_callback()

    async def run(self):
        """Start hub by connecting then awaiting for messages.

        Runs until the stop() method is called.
        """
        if self.running:
            _LOGGER.warning(f"{self.host}: Already running")
            return
        self.running = True

        while self.running:
            try:
                async with websockets.connect(self.wsuri, ssl=ssl_context) as websocket:
                    self.ws = websocket
                    asyncio.create_task(self.heartbeat())
                    self.handshake.set()
                    async for message in websocket:
                        await self.wsconsumer(message)
            except Exception as e:
                self.ws = None
                if self.lasterrorlog != errors.CannotConnectException:
                    _LOGGER.error("Websocket Connection closed: {}".format(e))
                    self.lasterrorlog = errors.CannotConnectException
                self.connected = False
                await asyncio.sleep(10)

        _LOGGER.debug(f"{self.host}: Stopped")

    async def test(self):
        """Connect to the hub once, and check we get a valid response

        Will raise an exception if unable to connect and get a response, or True
        if connection succeeded.
        """
        async with websockets.connect(self.wsuri, ssl=ssl_context) as websocket:
            self.ws = websocket
            asyncio.create_task(self.heartbeat())
            self.handshake.set()
            async for message in websocket:
                await self.wsconsumer(message)
                if self.connected:
                    return True
                else:
                    raise errors.InvalidResponseException

    async def stop(self):
        """Tell hub to stop and await for it to disconnect."""
        if not self.running:
            _LOGGER.warning(f"{self.host}: Already stopped")
            return
        _LOGGER.debug(f"{self.host}: Stopping")
        self.running = False
        await self.disconnect()
