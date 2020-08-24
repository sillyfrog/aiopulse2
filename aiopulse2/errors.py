"""Error classes of aiopulse module."""


class HubBaseException(Exception):
    """Base Exception for protocol."""

    pass


class NotConnectedException(HubBaseException):
    """Exception thrown when the hub isn't connected."""

    pass


class NotRunningException(HubBaseException):
    """Exception thrown when the hub isn't running."""

    pass


class CannotConnectException(HubBaseException):
    """Exception thrown when a socket connection cannot be made."""

    pass


class InvalidResponseException(HubBaseException):
    """Exception thrown when an invalid response is received."""

    pass
