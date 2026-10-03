"""Database setup: engine, session factory, and declarative base."""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# Allow SQLite connections to be shared across FastAPI's worker threads.
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """Base class that all ORM models inherit from."""


def init_db() -> None:
    """Create all database tables that don't exist yet."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized (%s)", settings.database_url)


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for a single request.

    Used as a FastAPI dependency. The session is always closed
    after the request finishes, even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
