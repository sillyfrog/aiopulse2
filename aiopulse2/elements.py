"""Elements that hang off the hub."""
import time
from typing import Callable, List

from .hub import Hub
from .const import MOVING_DOWN, MOVING_UP, STOPPED


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
        self.action = STOPPED
        self.online = True
        self.update_callbacks: List[Callable] = []

    def __str__(self):
        """Returns string representation of roller."""
        if self.action == MOVING_DOWN:
            actiontxt = "down"
        elif self.action == MOVING_UP:
            actiontxt = "up"
        else:
            actiontxt = "stopped"
        return (
            "Name: {!r} ID: {} Type: {} Target %: {} Closed %: {} Tilt %: {} Signal RSSI: {} Battery: {}v Action: {}"
        ).format(
            self.name,
            self.id,
            self.devicetype,
            self.target_closed_percent,
            self.closed_percent,
            self.tilt_percent,
            self.signal,
            self.battery,
            actiontxt,
        )

    @property
    def moving(self):
        return self._moving

    @moving.setter
    def moving(self, new_val):
        self._moving = new_val
        if self._moving:
            if self.action == STOPPED:
                # Guess as to the direction
                if self.closed_percent > 50:
                    self.action = MOVING_UP
                else:
                    self.action = MOVING_DOWN
        else:
            if self.action != STOPPED:
                self.action = STOPPED
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
            self.action = MOVING_DOWN
        elif percent < currentpcg:
            self.action = MOVING_UP
        else:
            self.action = STOPPED
        self.target_closed_percent = percent
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
