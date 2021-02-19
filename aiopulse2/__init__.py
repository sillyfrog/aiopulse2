"""Rollease Acmeda Automate Pulse asyncio protocol implementation."""
import logging

from .const import MovingAction, UpdateType
from .devices import Hub, Roller
from .errors import (
    CannotConnectException,
    InvalidResponseException,
    NotConnectedException,
    NotRunningException,
)

__all__ = [
    "Hub",
    "Roller",
    "CannotConnectException",
    "NotConnectedException",
    "NotRunningException",
    "InvalidResponseException",
    "UpdateType",
    "MovingAction",
]
__version__ = "0.6.0"

_LOGGER = logging.getLogger(__name__)
