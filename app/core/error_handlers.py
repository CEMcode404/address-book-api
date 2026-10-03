"""Translate exceptions into consistent JSON error responses."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import NotFoundError

logger = logging.getLogger(__name__)


async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Return a 404 with a message describing what was not found."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected errors and return a generic 500 without internal details."""
    logger.exception("Unhandled error during %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the application."""
    app.add_exception_handler(NotFoundError, not_found_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
