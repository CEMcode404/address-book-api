"""API integration tests for the address endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.address import get_address_service

HOME = {
    "name": "Home",
    "street": "123 Rizal Street",
    "city": "Manila",
    "state": "Metro Manila",
    "postal_code": "1000",
    "country": "Philippines",
    "latitude": 14.5995,
    "longitude": 120.9842,
}
OFFICE = {
    "name": "Office",
    "street": "6750 Ayala Avenue",
    "city": "Makati",
    "country": "Philippines",
    "latitude": 14.5547,
    "longitude": 121.0244,
}
CEBU = {
    "name": "Cebu",
    "street": "1 Osmeña Boulevard",
    "city": "Cebu City",
    "country": "Philippines",
    "latitude": 10.3157,
    "longitude": 123.8854,
}


def create(client: TestClient, payload: dict) -> dict:
    """Create an address through the API and return the response body."""
    response = client.post("/addresses", json=payload)
    assert response.status_code == 201
    return response.json()


def nearby(client: TestClient, latitude: float, longitude: float, **params):
    """Call the nearby search endpoint."""
    return client.get(
        "/addresses/nearby",
        params={"latitude": latitude, "longitude": longitude, **params},
    )


# --- Health ---------------------------------------------------------------


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- Create ---------------------------------------------------------------


def test_create_address_returns_201_with_generated_fields(client: TestClient) -> None:
    body = create(client, HOME)
    assert isinstance(body["id"], int)
    assert body["name"] == "Home"
    assert body["created_at"]
    assert body["updated_at"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latitude", 90.1),
        ("latitude", -90.1),
        ("longitude", 180.1),
        ("longitude", -180.1),
        ("name", "   "),
        ("city", ""),
    ],
)
def test_create_address_rejects_invalid_values(
    client: TestClient, field: str, value: object
) -> None:
    response = client.post("/addresses", json={**HOME, field: value})
    assert response.status_code == 422


def test_create_address_requires_mandatory_fields(client: TestClient) -> None:
    payload = {key: value for key, value in HOME.items() if key != "city"}
    response = client.post("/addresses", json=payload)
    assert response.status_code == 422


# --- Get ------------------------------------------------------------------


def test_get_address(client: TestClient) -> None:
    created = create(client, HOME)
    response = client.get(f"/addresses/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_address_returns_404(client: TestClient) -> None:
    response = client.get("/addresses/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Address with id 999 not found"}


def test_get_address_rejects_non_positive_id(client: TestClient) -> None:
    assert client.get("/addresses/0").status_code == 422


# --- List -----------------------------------------------------------------


def test_list_addresses_is_paginated(client: TestClient) -> None:
    home = create(client, HOME)
    office = create(client, OFFICE)

    all_ids = [a["id"] for a in client.get("/addresses").json()]
    assert all_ids == [home["id"], office["id"]]

    page = client.get("/addresses", params={"skip": 1, "limit": 1}).json()
    assert [a["id"] for a in page] == [office["id"]]


# --- Update ---------------------------------------------------------------


def test_update_changes_only_provided_fields(client: TestClient) -> None:
    created = create(client, HOME)
    response = client.patch(f"/addresses/{created['id']}", json={"city": "Pasig"})

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Pasig"
    assert body["street"] == HOME["street"]
    assert body["latitude"] == HOME["latitude"]


def test_update_can_clear_optional_field(client: TestClient) -> None:
    created = create(client, HOME)
    response = client.patch(f"/addresses/{created['id']}", json={"state": None})
    assert response.status_code == 200
    assert response.json()["state"] is None


def test_update_rejects_null_for_required_field(client: TestClient) -> None:
    created = create(client, HOME)
    response = client.patch(f"/addresses/{created['id']}", json={"city": None})
    assert response.status_code == 422


def test_update_missing_address_returns_404(client: TestClient) -> None:
    response = client.patch("/addresses/999", json={"city": "Pasig"})
    assert response.status_code == 404


# --- Delete ---------------------------------------------------------------


def test_delete_address(client: TestClient) -> None:
    created = create(client, HOME)

    response = client.delete(f"/addresses/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/addresses/{created['id']}").status_code == 404


def test_delete_missing_address_returns_404(client: TestClient) -> None:
    assert client.delete("/addresses/999").status_code == 404


# --- Nearby search --------------------------------------------------------


def test_nearby_returns_matches_sorted_by_distance(client: TestClient) -> None:
    home = create(client, HOME)
    office = create(client, OFFICE)
    create(client, CEBU)

    response = nearby(client, HOME["latitude"], HOME["longitude"], distance_km=10)

    assert response.status_code == 200
    results = response.json()
    assert [r["id"] for r in results] == [home["id"], office["id"]]
    assert results[0]["distance_km"] == 0
    assert results[1]["distance_km"] == pytest.approx(6.58, abs=0.01)


def test_nearby_excludes_addresses_outside_radius(client: TestClient) -> None:
    home = create(client, HOME)
    create(client, OFFICE)

    results = nearby(client, HOME["latitude"], HOME["longitude"], distance_km=1).json()
    assert [r["id"] for r in results] == [home["id"]]


def test_nearby_is_paginated(client: TestClient) -> None:
    create(client, HOME)
    office = create(client, OFFICE)

    results = nearby(
        client, HOME["latitude"], HOME["longitude"], distance_km=10, skip=1, limit=1
    ).json()
    assert [r["id"] for r in results] == [office["id"]]


@pytest.mark.parametrize(
    ("stored", "query"),
    [
        ((0.0, 179.95), (0.0, -179.95)),
        ((89.9, 0.0), (89.9, 180.0)),
    ],
    ids=["across-180-meridian", "near-north-pole"],
)
def test_nearby_handles_geographic_edge_cases(
    client: TestClient, stored: tuple[float, float], query: tuple[float, float]
) -> None:
    create(client, {**HOME, "latitude": stored[0], "longitude": stored[1]})
    results = nearby(client, *query, distance_km=25).json()
    assert len(results) == 1


@pytest.mark.parametrize(
    "params",
    [
        {"latitude": 91, "longitude": 0, "distance_km": 10},
        {"latitude": 0, "longitude": 181, "distance_km": 10},
        {"latitude": 0, "longitude": 0, "distance_km": 0},
        {"latitude": 0, "longitude": 0},
    ],
    ids=["bad-latitude", "bad-longitude", "zero-distance", "missing-distance"],
)
def test_nearby_rejects_invalid_query(client: TestClient, params: dict) -> None:
    response = client.get("/addresses/nearby", params=params)
    assert response.status_code == 422


# --- Unexpected errors ----------------------------------------------------


def test_unexpected_error_returns_generic_500() -> None:
    class BrokenService:
        def get_address(self, address_id: int) -> None:
            raise RuntimeError("secret internal failure")

    app.dependency_overrides[get_address_service] = lambda: BrokenService()
    try:
        # By default TestClient re-raises server errors; disable that to see
        # the actual response a client would receive.
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/addresses/1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {
        "detail": "An unexpected error occurred. Please try again later."
    }
    assert "secret" not in response.text
