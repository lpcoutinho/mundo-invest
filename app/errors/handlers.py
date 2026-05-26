"""Global FastAPI exception handler that converts domain errors to
standardised HTTP responses.

Registered once in ``main.py`` so that every controller can raise
a ``DomainError`` subclass without worrying about serialization.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from app.errors.exceptions import (
    DomainError,
    EntityNotFoundException,
    IdempotencyConflictException,
)

# Mapping from exception type to semantic HTTP status code.
# Adding a new domain exception only requires a new entry here;
# no controller or service changes are needed.
_STATUS_MAP: dict[type[DomainError], int] = {
    EntityNotFoundException: 404,
    IdempotencyConflictException: 409,
}


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Convert a ``DomainError`` into a standardised JSON error response.

    Why a single handler instead of per-exception decorators:
    A central mapping ensures consistent response structure across
    the entire API without repeating serialisation logic in each route.
    """
    status_code = next(
        (code for exc_type, code in _STATUS_MAP.items() if isinstance(exc, exc_type)),
        400,
    )
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {"message": exc.message, "code": exc.code},
        },
    )
