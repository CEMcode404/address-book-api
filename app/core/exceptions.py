"""Domain exceptions raised by the service layer.

These are independent of HTTP; they are translated into HTTP
responses by the handlers in ``app.core.error_handlers``.
"""


class AppError(Exception):
    """Base class for expected application errors."""


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""


class AddressNotFoundError(NotFoundError):
    """Raised when an address with the given ID does not exist."""

    def __init__(self, address_id: int) -> None:
        self.address_id = address_id
        super().__init__(f"Address with id {address_id} not found")