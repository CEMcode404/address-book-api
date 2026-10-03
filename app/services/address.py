"""Business logic for managing addresses."""

import logging
import math

from geopy.distance import geodesic

from app.core.exceptions import AddressNotFoundError
from app.models import Address
from app.repositories import AddressRepository
from app.schemas import AddressCreate, AddressUpdate

logger = logging.getLogger(__name__)

# Slightly less than the real length of one degree of latitude (~110.6–111.7 km),
# so the bounding box is always at least as large as the search circle.
KM_PER_DEGREE = 110.0


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

    def find_nearby(
        self,
        latitude: float,
        longitude: float,
        distance_km: float,
        skip: int = 0,
        limit: int = 20,
    ) -> list[tuple[Address, float]]:
        """Find addresses within a distance of a point, sorted nearest first.

        A rough bounding box narrows the candidates in the database, then
        geopy's geodesic distance gives the exact result.

        Returns:
            Pairs of (address, distance in km).
        """
        lat_delta = distance_km / KM_PER_DEGREE
        min_lat, max_lat = latitude - lat_delta, latitude + lat_delta

        # Longitude degrees shrink toward the poles, so the box is widened using
        # the latitude closest to a pole. If the box reaches a pole or crosses the
        # 180° meridian, longitude can't be bounded simply, so it's skipped.
        lon_range: tuple[float, float] | None = None
        if -90 < min_lat and max_lat < 90:
            widest_lat = max(abs(min_lat), abs(max_lat))
            lon_delta = lat_delta / math.cos(math.radians(widest_lat))
            min_lon, max_lon = longitude - lon_delta, longitude + lon_delta
            if -180 <= min_lon and max_lon <= 180:
                lon_range = (min_lon, max_lon)

        candidates = self.repository.list_within_bounds(
            min_lat=max(min_lat, -90), max_lat=min(max_lat, 90), lon_range=lon_range
        )

        origin = (latitude, longitude)
        results = []
        # Exact distances are computed in Python, so all candidates in the bounding
        # box are loaded before sorting and paginating. Fine for this scale; for large
        # datasets, a spatial database (SpatiaLite/PostGIS) would do this in SQL.
        for address in candidates:
            distance = geodesic(origin, (address.latitude, address.longitude)).km
            if distance <= distance_km:
                results.append((address, distance))

        results.sort(key=lambda item: item[1])
        logger.info(
            "Nearby search at (%s, %s) within %s km: %d of %d candidates matched",
            latitude,
            longitude,
            distance_km,
            len(results),
            len(candidates),
        )
        # Paginate after sorting, so pages follow nearest-first order.
        return results[skip : skip + limit]
