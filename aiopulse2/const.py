"""Acmeda Pulse Hub constants."""
import re
from enum import Enum

UpdateType = Enum("UpdateType", "info rollers rooms scenes timers")

HUB_NAME = "!000NAME?;"
HUB_NAME_RESPONSE = re.compile(r"!000NAME(?P<name>.+);")

HUB_PING = HUB_NAME  # there is no known ping, so just use the NAME command

HUB_SERIAL = "!000SN?;"
HUB_SERIAL_RESPONSE = re.compile(r"!000SN(?P<serial>.+);")

HUB_QUERY_DEVICES = "!000v?;"
HUB_QUERY_DEVICE_RESPONSE = re.compile(
    r"!(?P<id>\w{3})v(?P<devicetype>\w)(?P<version>\d{2});"
)

DEVICE_QUERY_NAME = "!{id:3}NAME?;"
DEVICE_QUERY_NAME_RESPONSE = re.compile(r"!(?P<id>\w{3})NAME(?P<name>.+);")

DEVICE_QUERY_POSITION = "!{id:3}r?;"
DEVICE_QUERY_POSITION_RESPONSE = re.compile(
    r"!(?P<id>\w{3})r(?P<closedpercent>\d{3})b(?P<tiltpercent>\d{3}),R(?P<signal>[0-9A-F]{2});"
)

DEVICE_MOVE_TO_POSITION = "!{id:3}m{closedpercent:03d};"
DEVICE_MOVE_TO_POSITION_RESPONSE = re.compile(
    r"!(?P<id>\w{3})m(?P<closedpercent>\d{3}),R(?P<signal>[0-9A-F]{2});"
)

WS_ROLLER_VOLTAGE = re.compile(
    r"(?P<voltage>[\.0-9]+)(?P<type>[A-Z])(?P<version>\d{2})"
)

ALL_RESPONSES = {}
# This build the ALL_RESPONSES dict by looking at the globals in the context
# of the module. More work at start, but less chance of human error
for var, value in dict(globals()).items():
    if var.endswith("_RESPONSE"):
        ALL_RESPONSES[var] = value

TYPES = {
    "A": "AC motor",
    "U": "AC motor (U)",
    "B": "Hub/Gateway",
    "C": "Curtain motor",
    "D": "DC motor",
    "S": "Socket",
    "L": "Lighting devices",
}

MovingAction = Enum("MovingAction", "stopped up down")
