"""HTTP endpoints for managing addresses."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Address
from app.repositories import AddressRepository
from app.schemas import AddressCreate, AddressResponse
from app.services import AddressService

router = APIRouter(prefix="/addresses", tags=["Addresses"])


def get_address_service(db: Annotated[Session, Depends(get_db)]) -> AddressService:
    """Build an AddressService with a database session for the current request."""
    return AddressService(AddressRepository(db))


AddressServiceDep = Annotated[AddressService, Depends(get_address_service)]


@router.post(
    "",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an address",
)
def create_address(data: AddressCreate, service: AddressServiceDep) -> Address:
    """Create a new address with its coordinates."""
    return service.create_address(data)