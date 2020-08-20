"""Acmeda Pulse Hub constants."""
from enum import Enum
import re

UpdateType = Enum("UpdateType", "info rollers rooms scenes timers")

HUB_NAME = "!000NAME?;"
HUB_NAME_RESPONSE = re.compile(r"!000NAME(?P<name>.+);")

HUB_PING = HUB_NAME  # there is no known ping, so just use the NAME command

HUB_SERIAL = "!000SN?;"
HUB_SERIAL_RESPONSE = re.compile(r"!000SN(?P<serial>.+);")


ALL_RESPONSES = {}
# This build the ALL_RESPONSES dict by looking at the globals in the context
# of the module. More work at start, but less chance of human error
for var, value in dict(globals()).items():
    if var.endswith("_RESPONSE"):
        ALL_RESPONSES[var] = value

HEADER = bytes.fromhex("00000003")
COMMAND_DISCOVER = bytes.fromhex("03000003")
RESPONSE_DISCOVER = bytes.fromhex("57000004")

COMMAND_CONNECT = bytes.fromhex("03000006")
RESPONSE_CONNECT = bytes.fromhex("0f000007")

COMMAND_LOGIN = bytes.fromhex("0f000008")
RESPONSE_LOGIN = bytes.fromhex("04000009")

# COMMAND_PING = bytes.fromhex("03000015")
# RESPONSE_PING = bytes.fromhex("03000016")

COMMAND_SETID = bytes.fromhex("28000090")
RESPONSE_SETID = bytes.fromhex("03000091")

COMMAND_UNKNOWN1 = bytes.fromhex("23000090")
RESPONSE_UNKNOWN1 = bytes.fromhex("28000091")

COMMAND_GET_HUB_INFO = bytes.fromhex("1e000090")
RESPONSE_GET_HUB_INFO = bytes.fromhex("4a000091")

COMMAND_MOVE_TO = bytes.fromhex("34000090")
RESPOSE_MOVE_TO = bytes.fromhex("34000091")

COMMAND_MOVE = bytes.fromhex("2d000090")

GET_ROOMS = bytes.fromhex("01000091")
GET_ROLLERS = bytes.fromhex("03000091")
