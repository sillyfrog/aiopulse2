"""Acmeda Pulse Hub and Rollers Interfaces."""
# Note, these are in the same file to prevent circular imports
import asyncio
import functools
import json
import logging
import ssl
import time
from typing import Any, Callable, Dict, List, Optional

import async_timeout
import websockets

from . import const, errors
from .const import MovingAction

_LOGGER = logging.getLogger(__name__)

# The minimum version above which we can trust the "ol" (online) value. Below this
# version, the roller will always be reported as online
ONLINE_MIN_VERSION = 13

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


class Hub:
    """Representation of an Acmeda Pulse v2 Hub."""

    def __init__(
        self, host: str, delay_callbacks: bool = True, propagate_callbacks: bool = False
    ):
        """Init the hub.

        host: The IP address / hostname of hub
        delay_callbacks: If True (default), no callbacks will be called until the
            inital hub sync is complete, getting details such as the device name
        propagate_callbacks: If True, when there is a change to the hub, all roller
            callbacks are also notified.
        """
        self.loop = asyncio.get_event_loop()
        self.handshake = asyncio.Event()
        self.delay_callbacks = delay_callbacks
        self.propagate_callbacks = propagate_callbacks
        self.response_task = None
        self.running = False
        self.connected = False
        self.lasterrorlog = None
        self.serialok = False
        self.lastserialerror = None

        self.name = None
        self.id = None
        self.host = host
        self.wsuri = "wss://{}:443/rpc".format(self.host)
        self.mac_address = None
        self.firmware_ver = None
        self.model = None

        self.ws = None

        self.rollers = {}
        self.unknown_rollers = set()
        self.rollers_known = asyncio.Event()
        self.rollers_known.clear()
        self.serialrunning = False
        self.sent_details_request = set()
        self.payload_queue = []

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
        if callback not in self.update_callbacks:
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

    def notify_callback(self):
        """Tell callback that the hub has been updated."""
        if self.delay_callbacks and (self.unknown_rollers or len(self.rollers) == 0):
            return
        for callback in self.update_callbacks:
            self.async_add_job(callback, self)
        if self.propagate_callbacks:
            for roller in self.rollers.values():
                roller.notify_callback()

    async def disconnect(self):
        """Disconnect from the hub."""
        _LOGGER.debug("%s: Disconnecting", self.host)
        if self.ws:
            await self.ws.close()
        self.handshake.clear()
        _LOGGER.info("%s: Disconnected", self.host)

    def response_parse(self, response: str):
        """Decode response."""
        for name, matcher in const.ALL_RESPONSES.items():
            match = matcher.match(response)
            if match:
                _LOGGER.debug(
                    "%s: Received response: %s content: %s",
                    self.host,
                    name,
                    match.groups(),
                )
                handler = getattr(self, "handle_" + name.lower(), "")
                if handler:
                    handler(**match.groupdict())
                else:
                    _LOGGER.debug("No handler for %s", name)
                return
        _LOGGER.debug("No match for: %s", response)

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
        if not self.unknown_rollers:
            # The list of unknown_rollers is empty
            self.rollers_known.set()
            self.notify_callback()

    async def serialrunner(self):
        """The running to get all required information from the hub

        This will exit when complete.
        """
        self.serialrunning = True
        try:
            while self.unknown_rollers:
                self.rollers_known.clear()  # We have some unknown rollers
                reader, writer = await asyncio.open_connection(self.host, port=1487)
                # Send off a request for all of the unknown rollers
                for rollerid in self.unknown_rollers:
                    buf = const.DEVICE_QUERY_NAME.format(id=rollerid)
                    writer.write(buf.encode())
                while True:
                    with async_timeout.timeout(3):
                        response = await reader.readuntil(b";")
                    if len(response) > 0:
                        _LOGGER.debug("recv < %s", response)
                        self.response_parse(response.decode())
                    else:
                        break
                # Nothing has happened for > 30 seconds, disconnet
                writer.close()
                # Sleep 10 seconds to wait for things to settle down before maybe trying again
                await asyncio.sleep(10)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            pass
        except Exception as e:
            _LOGGER.info("Error in serial running: %s", e)
        self.serialrunning = False

    async def runserial(self):
        """Runs a 'serial' connection to the hub to get additional information"""
        if self.serialrunning:
            # Already running, don't start again
            return
        self.serialrunning = True
        asyncio.create_task(self.serialrunner())

    async def send_payload(self, jscommand: Dict):
        """Send payload to the hub

        See sendws for details.
        """
        if not self.running:
            raise errors.NotRunningException
        await self.handshake.wait()
        await self.sendws(jscommand)

    async def sendws(self, jscommand: Dict) -> bool:
        """Send jscommand over the websocket

        jscommand must be a Python dict, that will be converted to JSON
        Returns True on success
        """
        if self.ws:
            try:
                with async_timeout.timeout(10):
                    await self.ws.send(json.dumps(jscommand))
                return True
            except (websockets.WebSocketException, asyncio.TimeoutError) as e:
                _LOGGER.warn("Error sending payload: %s", e)
                self.handshake.clear()
        return False

    async def heartbeat(self):
        reset_request_counter = 3600 / self.heartbeatinterval
        while self.running:
            if self.ws and self.ws.open and self.handshake.is_set():
                if self.payload_queue:
                    payload = self.payload_queue.pop(0)
                    success = await self.sendws(payload)
                    if not success:
                        self.payload_queue.append(payload)
                await self.sendws(
                    {"method": "shadow", "src": "app", "id": int(time.time())}
                )
            await asyncio.sleep(self.heartbeatinterval)
            reset_request_counter -= 1
            if reset_request_counter <= 0:
                # About once an hour allow a request to be made to the hub to get the
                # rollers details again
                self.sent_details_request.clear()
                reset_request_counter = 3600 / self.heartbeatinterval

    def applychanges(self, obj: Any, newvalues: Dict[str, Any]) -> bool:
        """Applies and reports changes from newvals to the attributes of obj

        Returns True if there were any changes, False otherwise.
        """
        updated = False
        for attr, val in newvalues.items():
            if getattr(obj, attr) != val:
                setattr(obj, attr, val)
                updated = True
        return updated

    async def wsconsumer(self, msg: str):
        jsmsg = json.loads(msg)
        if "result" not in jsmsg or "reported" not in jsmsg["result"]:
            _LOGGER.info("Got unknown WS response: %s", msg)
            return
        if not self.connected:
            self.connected = True
            self.notify_callback()
        if self.lasterrorlog is not None:
            _LOGGER.info("Connected to %s", self.host)
            self.lasterrorlog = None
        data = jsmsg["result"]["reported"]
        _LOGGER.debug("Got payload: %s", data)
        newvals = {
            "name": data["name"],
            "id": data["hubId"],
            "mac_address": data["mac"],
            "firmware_ver": data["firmware"]["version"],
            "model": data["mfi"]["model"],
        }
        hubchanges = self.applychanges(self, newvals)

        for rollerid, roller in data["shades"].items():
            if rollerid not in self.rollers:
                self.rollers[rollerid] = Roller(self, rollerid)
                self.unknown_rollers.add(rollerid)
                await self.runserial()
                hubchanges = True

            newvals = {
                "signal": roller.get("rs"),
                "moving": not roller.get("is", True),
                "online": roller.get("ol", False),
                "closed_percent": int(roller.get("mp", 100)),
            }
            if "vo" not in roller:
                # The voltage and version key is missing, request more details if
                # not already sent. If this request is not made, it will typically
                # be sent through with in about 20 minutes
                if rollerid not in self.sent_details_request:
                    self.payload_queue.append(
                        {
                            "method": "shadow",
                            "args": {
                                "desired": {"shades": {rollerid: {"query": True}}},
                                "timeStamp": time.time(),
                            },
                        }
                    )
                    self.sent_details_request.add(rollerid)
            else:
                batteryinfo = const.WS_ROLLER_VOLTAGE.match(roller["vo"])
                if batteryinfo:
                    newvals["battery"] = float(batteryinfo.group("voltage"))
                    newvals["devicetypeshort"] = batteryinfo.group("type")
                    newvals["devicetype"] = const.TYPES.get(batteryinfo.group("type"))
                    newvals["version"] = batteryinfo.group("version")

            try:
                version = int(newvals.get("version") or self.rollers[rollerid].version)
                if version < ONLINE_MIN_VERSION:
                    newvals["online"] = True
            except Exception:
                pass

            if self.applychanges(self.rollers[rollerid], newvals):
                self.rollers[rollerid].notify_callback()

        if hubchanges:
            self.notify_callback()

    async def run(self):
        """Start hub by connecting then awaiting for messages.

        Runs until the stop() method is called.
        """
        if self.running:
            _LOGGER.warning("%s: Already running", self.host)
            return
        self.running = True

        asyncio.create_task(self.heartbeat())
        while self.running:
            try:
                async with websockets.connect(self.wsuri, ssl=ssl_context) as websocket:
                    self.ws = websocket
                    self.handshake.set()
                    async for message in websocket:
                        await self.wsconsumer(message)
            except Exception as e:
                self.ws = None
                if self.running and self.lasterrorlog != errors.CannotConnectException:
                    _LOGGER.warning("Websocket Connection closed: %s", e)
                    self.lasterrorlog = errors.CannotConnectException
                self.connected = False
                self.notify_callback()
                if self.running:
                    await asyncio.sleep(10)

        _LOGGER.debug("%s: Stopped", self.host)

    async def test(self, update_devices=False):
        """Connect to the hub once, and check we get a valid response

        update_devices: if True, will wait until the initial full update is complete
        and the rollers have had their initial information populated.
        Will raise an exception if unable to connect and get a response, or True
        if connection succeeded.
        """
        self.running = True
        async with websockets.connect(self.wsuri, ssl=ssl_context) as websocket:
            self.ws = websocket
            asyncio.create_task(self.heartbeat())
            self.handshake.set()
            async for message in websocket:
                await self.wsconsumer(message)
                if self.connected:
                    self.running = False
                    break
                else:
                    raise errors.InvalidResponseException
        # Now connected, wait for the initial device listing to be populated
        if update_devices:
            await self.rollers_known.wait()
        self.ws = None
        self.connected = False
        return True

    async def stop(self):
        """Tell hub to stop and await for it to disconnect."""
        if not self.running:
            _LOGGER.warning("%s: Already stopped", self.host)
            return
        _LOGGER.debug("%s: Stopping", self.host)
        self.running = False
        await self.disconnect()


class Roller:
    """Representation of a Roller blind."""

    def __init__(self, hub: Hub, roller_id: str):
        """Init a new roller blind."""
        self.hub = hub
        self.id = roller_id
        self.name = None
        self.devicetypeshort = None
        self.devicetype = None
        self.battery = None
        self.target_closed_percent = None
        self.closed_percent = None
        self.tilt_percent = None
        self.signal = None
        self.version = None
        self._moving = False
        self.action = MovingAction.stopped
        self.online = False
        self.update_callbacks: List[Callable] = []

    def __str__(self):
        """Returns string representation of roller."""
        if self.action == MovingAction.down:
            actiontxt = "down"
        elif self.action == MovingAction.up:
            actiontxt = "up"
        else:
            actiontxt = "stopped"
        return (
            "Name: {!r} ID: {} Type: {} Target %: {} Closed %: {} Tilt %: {} Signal RSSI: {} Battery: {}v Battery %: {} Action: {}"
        ).format(
            self.name,
            self.id,
            self.devicetype,
            self.target_closed_percent,
            self.closed_percent,
            self.tilt_percent,
            self.signal,
            self.battery,
            self.battery_percent,
            actiontxt,
        )

    @property
    def battery_percent(self):
        """A rough approximation base on the app vs voltage levels read.

        Returns None if they devicetype is not D (DC motor), as there is no battery.

        Should be updated if a better solution is found.
        """
        if not self.has_battery or not self.battery:
            return None
        percent = int(27.4 * self.battery - 255)
        if percent < 0:
            percent = 0
        elif percent > 100:
            percent = 100
        return percent

    @property
    def has_battery(self):
        """True if device appears to be battery operated"""
        return self.devicetypeshort == "D"

    @property
    def moving(self):
        return self._moving

    @moving.setter
    def moving(self, new_val):
        self._moving = new_val
        if self._moving:
            if self.action == MovingAction.stopped:
                # Guess as to the direction
                if self.closed_percent > 50:
                    self.action = MovingAction.up
                else:
                    self.action = MovingAction.down
        else:
            if self.action != MovingAction.stopped:
                self.action = MovingAction.stopped
            self.target_closed_percent = self.closed_percent

    def callback_subscribe(self, callback: Callable):
        """Add a callback for hub updates."""
        if callback not in self.update_callbacks:
            self.update_callbacks.append(callback)

    def callback_unsubscribe(self, callback: Callable):
        """Remove a callback for hub updates."""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)

    def notify_callback(self):
        """Tell callback that device has been updated."""
        if self.hub.delay_callbacks and self.name is None:
            return
        for callback in self.update_callbacks:
            self.hub.async_add_job(callback, self)

    def set_signal(self, signal: str):
        """Sets the signal as an int from a hex value"""
        if type(signal) is not int:
            signal = int(signal, 16)
        self.signal = signal

    async def move_to(self, percent: int):
        """Send command to move the roller to a percentage closed."""
        currentpcg = self.closed_percent
        if currentpcg is None:
            currentpcg = 50
        if percent > currentpcg:
            self.action = MovingAction.down
        elif percent < currentpcg:
            self.action = MovingAction.up
        else:
            self.action = MovingAction.stopped
        self._moving = True
        self.target_closed_percent = percent
        self.notify_callback()
        await self.hub.send_payload(
            {
                "method": "shadow",
                "args": {
                    "desired": {"shades": {self.id: {"movePercent": int(percent)}}},
                    "timeStamp": time.time(),
                },
            }
        )

    async def move_up(self):
        """Send command to move the roller to fully open."""
        await self.move_to(0)

    async def move_down(self):
        """Send command to move the roller to fully closed."""
        await self.move_to(100)

    async def move_stop(self):
        """Send command to stop the roller."""
        await self.hub.send_payload(
            {
                "method": "shadow",
                "args": {
                    "desired": {"shades": {self.id: {"stopShade": True}}},
                    "timeStamp": time.time(),
                },
            }
        )
