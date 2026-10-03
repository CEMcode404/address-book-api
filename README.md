# Address Book API

A REST API for managing an address book, built with **FastAPI** and **SQLite**.
Users can create, read, update, and delete addresses with geographic coordinates,
and search for addresses within a given distance of a location.

## Quick start

```bash
git clone https://github.com/CEMcode404/address-book-api.git
cd address-book-api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --reload-dir app
```

Then open http://127.0.0.1:8000/docs to try the API.

These commands are for macOS/Linux. On Windows, or for a step-by-step explanation,
see [Getting started](#getting-started).

## Features

- **CRUD operations** for addresses (create, read, list, partial update, delete)
- **Nearby search**: find addresses within a radius of a point, sorted nearest first,
  using accurate geodesic distances
- **Validation** of all input (coordinate ranges, required fields, text lengths)
- **Pagination** on list and search endpoints
- **Structured logging** and consistent JSON error responses
- **Interactive API docs** via Swagger UI
- **API integration tests** with an isolated in-memory database

## Tech stack

| Purpose            | Library                     |
| ------------------ | --------------------------- |
| Web framework      | FastAPI + Uvicorn           |
| Database / ORM     | SQLite + SQLAlchemy 2.0     |
| Validation         | Pydantic v2                 |
| Configuration      | pydantic-settings           |
| Distance math      | geopy (geodesic distance)   |
| Testing            | pytest + FastAPI TestClient |
| Linting/formatting | Ruff                        |

## Requirements

- Python **3.12** (3.10 or newer is required for the type-hint syntax used)
- Git

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/CEMcode404/address-book-api.git
cd address-book-api
```

### 2. Create and activate a virtual environment

macOS / Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

Windows (PowerShell):

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
uvicorn app.main:app --reload --reload-dir app
```

The database file (`address_book.db`) and its tables are created automatically on startup.

### 5. Open the API docs

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

All endpoints can be tried directly from Swagger UI; example values are pre-filled.

## Configuration

Settings have sensible defaults, so no configuration is needed to run the app.
To override them, copy the example file and edit it:

```bash
cp .env.example .env
```

| Variable       | Default                       | Description                                            |
| -------------- | ----------------------------- | ------------------------------------------------------ |
| `DATABASE_URL` | `sqlite:///./address_book.db` | SQLAlchemy database URL                                |
| `LOG_LEVEL`    | `INFO`                        | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

## API endpoints

| Method   | Endpoint            | Description                                 |
| -------- | ------------------- | ------------------------------------------- |
| `POST`   | `/addresses`        | Create an address                           |
| `GET`    | `/addresses`        | List addresses (paginated)                  |
| `GET`    | `/addresses/nearby` | Find addresses within a distance of a point |
| `GET`    | `/addresses/{id}`   | Get an address by ID                        |
| `PATCH`  | `/addresses/{id}`   | Partially update an address                 |
| `DELETE` | `/addresses/{id}`   | Delete an address                           |
| `GET`    | `/health`           | Health check                                |

The assignment required create, update, delete, and the nearby search. Get and list
were added so the API is complete and easy to verify.

### Examples

Create an address:

```bash
curl -X POST http://127.0.0.1:8000/addresses \
  -H "Content-Type: application/json" \
  -d '{"name": "Home", "street": "123 Rizal Street", "city": "Manila", "country": "Philippines", "latitude": 14.5995, "longitude": 120.9842}'
```

Find addresses within 10 km of a point:

```bash
curl "http://127.0.0.1:8000/addresses/nearby?latitude=14.5995&longitude=120.9842&distance_km=10"
```

Each result includes a `distance_km` field, and results are sorted nearest first.

Update only the city:

```bash
curl -X PATCH http://127.0.0.1:8000/addresses/1 \
  -H "Content-Type: application/json" \
  -d '{"city": "Quezon City"}'
```

### Validation rules

- `latitude` must be between -90 and 90; `longitude` between -180 and 180
- `name`, `street`, `city`, and `country` are required and cannot be blank
- `state` and `postal_code` are optional
- Updates are partial: omitted fields are unchanged, optional fields can be cleared
  with `null`, and required fields cannot be set to `null`
- Search radius (`distance_km`) must be greater than 0 and at most 20,000 km

## Running the tests

```bash
pytest -v
```

Tests run against a fresh in-memory SQLite database for each test, so they never
touch `address_book.db`.

## Development

Install development tools (includes Ruff):

```bash
pip install -r requirements-dev.txt
```

Lint and format:

```bash
ruff check . --fix
ruff format .
```

## Project structure

```
app/
├── main.py                  # App creation, startup, router registration
├── core/
│   ├── config.py            # Settings from environment variables / .env
│   ├── database.py          # Engine, session, and table creation
│   ├── error_handlers.py    # Maps exceptions to JSON error responses
│   ├── exceptions.py        # Domain exceptions
│   └── logging_config.py    # Logging setup
├── models/address.py        # SQLAlchemy table definition
├── schemas/address.py       # Pydantic request/response schemas
├── repositories/address.py  # Database queries
├── services/address.py      # Business logic and distance calculation
└── routers/address.py       # HTTP endpoints
tests/
├── conftest.py              # Test database and client fixtures
└── test_addresses.py        # API integration tests
```

## Architecture and design decisions

**Layered structure.** Each layer has one responsibility:

- **Routers** handle HTTP only: parsing requests, status codes, and response shapes.
- **Services** contain business logic, such as not-found checks, partial updates,
  and the distance search. They have no knowledge of HTTP.
- **Repositories** contain database queries only.

The layering is intentionally lightweight for the scope of the project: no abstract
base classes or dependency-injection containers. Files are named by resource
(`address.py`) inside folders named by layer.

**Error handling.** Services raise domain exceptions (e.g. `AddressNotFoundError`).
These form a hierarchy, so one handler per category (e.g. `NotFoundError` → 404)
covers all of its subclasses. A catch-all handler logs unexpected errors with a full
traceback and returns a generic message, so internal details never reach clients.
Validation errors use FastAPI's built-in 422 responses.

**Nearby search.** SQLite has no geographic functions, so the search works in two steps:

1. An indexed **bounding-box** query narrows the candidates in SQL. The box is
   calculated conservatively so it is never smaller than the search circle. Near the
   poles or across the 180° meridian, the longitude filter is skipped.
2. Exact **geodesic distances** are calculated with geopy, then filtered, sorted, and
   paginated.

**Timestamps** are stored in UTC.

## Possible improvements

- **Spatial database.** The nearby search loads all candidates inside the bounding box
  before sorting and paginating, which is fine at this scale. For large datasets,
  SpatiaLite or PostGIS would allow spatial indexing and SQL-side sorting and
  pagination. They were left out because they require native libraries that
  complicate setup.
- **Migrations.** Tables are created with `create_all`, which doesn't alter existing
  tables. Alembic would handle schema changes on existing databases.
- **Authentication.** Addresses are personal data; a production version should
  require authentication and give each user their own address book.
- **Timezone-aware responses.** SQLite doesn't store timezone information, so
  timestamps are returned without a UTC marker.
- **Docker and CI** to run the tests and linting on every push.