"""HTTP endpoints for managing addresses."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
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
AddressId = Annotated[int, Path(gt=0, description="The ID of the address")]


@router.post(
    "",
    response_model=AddressResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an address",
)
def create_address(data: AddressCreate, service: AddressServiceDep) -> Address:
    """Create a new address with its coordinates."""
    return service.create_address(data)


@router.get(
    "/{address_id}",
    response_model=AddressResponse,
    summary="Get an address",
    responses={status.HTTP_404_NOT_FOUND: {"description": "Address not found"}},
)
def get_address(address_id: AddressId, service: AddressServiceDep) -> Address:
    """Retrieve a single address by its ID."""
    return service.get_address(address_id)