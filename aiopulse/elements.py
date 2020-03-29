"""Elements that hang off the hub."""
import aiopulse.utils as utils
import aiopulse.const as const


class Roller:
    """Representation of a Roller blind."""

    def __init__(self, hub, roller_id):
        """Init a new roller blind."""
        self.hub = hub
        self.id = roller_id
        self.name = None
        self.serial = None
        self.room_id = None
        self.room = None
        self.battery = None
        self.closed_percent = None
        self.flags = 0
        self.update_callback = None

    def __str__(self):
        """Returns string representation of roller."""
        return (
            "Name: {} ID: {} Serial: {} Room: {} Closed %: {} Battery %: {}"
            " Flags: {:08b}"
        ).format(
            self.name,
            self.id,
            self.serial,
            self.room.name,
            self.closed_percent,
            self.battery,
            self.flags,
        )

    def set_callback(self, callback):
        """Add a callback for device updates."""
        self.update_callback = callback

    def notify_callback(self):
        """Tell callback that device has been updated."""
        if self.update_callback:
            self.update_callback()

    async def move_to(self, percent):
        """Send command to move the roller to a percentage closed."""
        message = (
            bytes.fromhex("0000000000000101")
            + bytes.fromhex("0600")
            + utils.pack_int(self.id, 6)
            + bytes.fromhex("03010100")
            + bytes.fromhex("190401030001")
            + utils.pack_int(percent, 2)
            + bytes.fromhex("ff")
        )
        await self.hub.send_payload(
            const.COMMAND_MOVE_TO, bytes.fromhex("2201"), message
        )

    async def move_up(self):
        """Send command to move the roller to fully open."""
        message = (
            bytes.fromhex("0000000000000101")
            + bytes.fromhex("0600")
            + utils.pack_int(self.id, 6)
            + bytes.fromhex("03010100")
            + bytes.fromhex("10")
            + bytes.fromhex("ff")
        )
        await self.hub.send_payload(const.COMMAND_MOVE, bytes.fromhex("2201"), message)

    async def move_stop(self):
        """Send command to stop the roller."""
        message = (
            bytes.fromhex("0000000000000101")
            + bytes.fromhex("0600")
            + utils.pack_int(self.id, 6)
            + bytes.fromhex("03010100")
            + bytes.fromhex("11")
            + bytes.fromhex("ff")
        )
        await self.hub.send_payload(const.COMMAND_MOVE, bytes.fromhex("2201"), message)

    async def move_down(self):
        """Send command to move the roller to fully closed."""
        message = (
            bytes.fromhex("0000000000000101")
            + bytes.fromhex("0600")
            + utils.pack_int(self.id, 6)
            + bytes.fromhex("03010100")
            + bytes.fromhex("12")
            + bytes.fromhex("ff")
        )
        await self.hub.send_payload(const.COMMAND_MOVE, bytes.fromhex("2201"), message)


class Room:
    """Representation of a Room."""

    def __init__(self, hub, room_id):
        """Init a new room."""
        self.hub = hub
        self.id = room_id
        self.icon = None
        self.name = None
        self.update_callback = None

    def __str__(self):
        """Returns string representation of roller."""
        return "Name: {} ID: {} Icon: {}".format(self.name, self.id[0:4], self.icon)

    def set_callback(self, callback):
        """Add a callback for device updates."""
        self.update_callback = callback

    def notify_callback(self):
        """Tell callback that device has been updated."""
        if self.update_callback:
            self.update_callback()

    async def move_to(self, percent):
        """Send command to move the roller to a percentage closed."""
        message = (
            bytes.fromhex("0000000000000101")
            + bytes.fromhex("0600")
            + utils.pack_int(self.id, 6)
            + bytes.fromhex("03010100")
            + bytes.fromhex("190401030001")
            + utils.pack_int(percent, 2)
            + bytes.fromhex("ff")
        )
        await self.hub.send_payload(
            const.COMMAND_MOVE_TO, bytes.fromhex("2201"), message
        )

    async def move_up(self):
        """Send command to move the roller to fully open."""
        message = (
            bytes.fromhex("0000000000000101")
            + bytes.fromhex("0600")
            + utils.pack_int(self.id, 6)
            + bytes.fromhex("03010100")
            + bytes.fromhex("10")
            + bytes.fromhex("ff")
        )
        await self.hub.send_payload(const.COMMAND_MOVE, bytes.fromhex("2201"), message)

    async def move_stop(self):
        """Send command to stop the roller."""
        message = (
            bytes.fromhex("0000000000000101")
            + bytes.fromhex("0600")
            + utils.pack_int(self.id, 6)
            + bytes.fromhex("03010100")
            + bytes.fromhex("11")
            + bytes.fromhex("ff")
        )
        await self.hub.send_payload(const.COMMAND_MOVE, bytes.fromhex("2201"), message)

    async def move_down(self):
        """Send command to move the roller to fully closed."""
        message = (
            bytes.fromhex("0000000000000101")
            + bytes.fromhex("0600")
            + utils.pack_int(self.id, 6)
            + bytes.fromhex("03010100")
            + bytes.fromhex("12")
            + bytes.fromhex("ff")
        )
        await self.hub.send_payload(const.COMMAND_MOVE, bytes.fromhex("2201"), message)


class Scene:
    """Representation of a Scene."""

    def __init__(self, hub, scene_id):
        """Init a new scene."""
        self.hub = hub
        self.id = scene_id
        self.icon = None
        self.name = None

    def __str__(self):
        """Returns string representation of roller."""
        return "Name: {} ID: {} Icon: {}".format(self.name, self.id[0:4], self.icon)