"""Data access layer for addresses. Contains database queries only."""

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