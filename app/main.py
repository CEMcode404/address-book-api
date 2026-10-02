"""Application entry point: creates and configures the FastAPI app."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  # Registers ORM models with Base before init_db()
from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import setup_logging
from app.routers import address

setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Run startup and shutdown logic for the application."""
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    init_db()
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Create, update, and delete addresses with coordinates, "
        "and search for addresses within a given distance."
    ),
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"], summary="Health check")
def health_check() -> dict[str, str]:
    """Return a simple status to confirm the API is running."""
    return {"status": "ok"}

app.include_router(address.router)