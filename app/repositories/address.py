"""Data access layer for addresses. Contains database queries only."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Address


class AddressRepository:
    """Performs database operations on the ``addresses`` table."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, address: Address) -> Address:
        """Insert a new address and return it with its generated fields."""
        self.db.add(address)
        self.db.commit()
        self.db.refresh(address)
        return address

    def get(self, address_id: int) -> Address | None:
        """Return the address with the given ID, or None if it doesn't exist."""
        return self.db.get(Address, address_id)

    def list_all(self, skip: int = 0, limit: int = 20) -> list[Address]:
        """Return a page of addresses ordered by ID."""
        stmt = select(Address).order_by(Address.id).offset(skip).limit(limit)
        return list(self.db.scalars(stmt))

    def save(self, address: Address) -> Address:
        """Persist changes made to an existing address."""
        self.db.commit()
        self.db.refresh(address)
        return address

    def delete(self, address: Address) -> None:
        """Remove an address from the database."""
        self.db.delete(address)
        self.db.commit()

    def list_within_bounds(
        self,
        min_lat: float,
        max_lat: float,
        lon_range: tuple[float, float] | None = None,
    ) -> list[Address]:
        """Return addresses inside a latitude range and, if given, a longitude range.

        The longitude range is omitted when the search area can't be described by a
        single range (near a pole or across the 180° meridian).
        """
        stmt = select(Address).where(Address.latitude.between(min_lat, max_lat))
        if lon_range is not None:
            stmt = stmt.where(Address.longitude.between(*lon_range))
        return list(self.db.scalars(stmt))
