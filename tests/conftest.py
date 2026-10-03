"""Shared pytest fixtures: an isolated in-memory database and a test client."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide a fresh, empty in-memory database for each test."""
    # StaticPool reuses a single connection, so every session sees the same
    # in-memory database (otherwise each connection would get its own).
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Provide a test client whose requests use the test database."""
    app.dependency_overrides[get_db] = lambda: db_session
    # Not used as a context manager, so the app's startup (init_db) doesn't run
    # and the real database file is never created or modified.
    yield TestClient(app)
    app.dependency_overrides.clear()
