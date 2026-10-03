"""Business logic for managing addresses."""

import logging

from app.models import Address
from app.repositories import AddressRepository
from app.schemas import AddressCreate
from app.core.exceptions import AddressNotFoundError

logger = logging.getLogger(__name__)


class AddressService:
    """Coordinates address operations between the API and the repository."""

    def __init__(self, repository: AddressRepository) -> None:
        self.repository = repository

    def create_address(self, data: AddressCreate) -> Address:
        """Create and store a new address."""
        address = self.repository.add(Address(**data.model_dump()))
        logger.info("Created address id=%s", address.id)
        return address

    def get_address(self, address_id: int) -> Address:
        """Return an address by ID.

        Raises:
            AddressNotFoundError: If no address has the given ID.
        """
        address = self.repository.get(address_id)
        if address is None:
            logger.warning("Address not found: id=%s", address_id)
            raise AddressNotFoundError(address_id)
        return address

    def list_addresses(self, skip: int = 0, limit: int = 20) -> list[Address]:
        """Return a page of addresses."""
        return self.repository.list_all(skip=skip, limit=limit)