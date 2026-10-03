"""HTTP endpoints for managing addresses."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Address
from app.repositories import AddressRepository
from app.schemas import AddressCreate, AddressResponse, AddressUpdate
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


@router.get(
    "",
    response_model=list[AddressResponse],
    summary="List addresses",
)
def list_addresses(
    service: AddressServiceDep,
    skip: Annotated[int, Query(ge=0, description="Number of addresses to skip")] = 0,
    limit: Annotated[
        int, Query(ge=1, le=100, description="Maximum number of addresses to return")
    ] = 20,
) -> list[Address]:
    """List addresses, paginated with ``skip`` and ``limit``."""
    return service.list_addresses(skip=skip, limit=limit)


@router.patch(
    "/{address_id}",
    response_model=AddressResponse,
    summary="Update an address",
    responses={status.HTTP_404_NOT_FOUND: {"description": "Address not found"}},
)
def update_address(
    address_id: AddressId, data: AddressUpdate, service: AddressServiceDep
) -> Address:
    """Partially update an address. Only the fields provided are changed."""
    return service.update_address(address_id, data)


@router.delete(
    "/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an address",
    responses={status.HTTP_404_NOT_FOUND: {"description": "Address not found"}},
)
def delete_address(address_id: AddressId, service: AddressServiceDep) -> None:
    """Delete an address by its ID."""
    service.delete_address(address_id)