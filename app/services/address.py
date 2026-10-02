"""Business logic for managing addresses."""

import logging

from app.models import Address
from app.repositories import AddressRepository
from app.schemas import AddressCreate

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