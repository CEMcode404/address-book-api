"""Business logic for managing addresses."""

import logging

from app.models import Address
from app.repositories import AddressRepository
from app.schemas import AddressCreate, AddressUpdate
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


    def update_address(self, address_id: int, data: AddressUpdate) -> Address:
        """Apply a partial update to an existing address.

        Only fields explicitly included in the request are changed.

        Raises:
            AddressNotFoundError: If no address has the given ID.
        """
        address = self.get_address(address_id)
        changes = data.model_dump(exclude_unset=True)

        for field, value in changes.items():
            setattr(address, field, value)

        address = self.repository.save(address)
        logger.info("Updated address id=%s fields=%s", address_id, sorted(changes))
        return address


    def delete_address(self, address_id: int) -> None:
        """Delete an address by ID.

        Raises:
            AddressNotFoundError: If no address has the given ID.
        """
        address = self.get_address(address_id)
        self.repository.delete(address)
        logger.info("Deleted address id=%s", address_id)


    