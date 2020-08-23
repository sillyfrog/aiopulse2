"""Rollease Acmeda Automate Pulse asyncio protocol implementation."""
import logging

from aiopulse.hub import Hub
from aiopulse.elements import Roller
from aiopulse.errors import (
    CannotConnectException,
    NotConnectedException,
    NotRunningException,
    InvalidResponseException,
)
from aiopulse.const import UpdateType

__all__ = [
    "Hub",
    "Roller",
    "CannotConnectException",
    "NotConnectedException",
    "NotRunningException",
    "InvalidResponseException",
    "UpdateType",
]
__version__ = "0.5.0"

_LOGGER = logging.getLogger(__name__)
