"""Generic API response wrappers.

Every endpoint in this system returns one of two shapes so that
front-end consumers and API Gateway response-mapping templates
can rely on a uniform contract:
  - Success: ``{ "success": true, "data": { ... } }``
  - Error:   ``{ "success": false, "error": { "message": "...", "code": "..." } }``
"""
from pydantic import BaseModel
from typing import Generic, TypeVar

DataT = TypeVar("DataT")


class SuccessResponse(BaseModel, Generic[DataT]):
    """Wraps a successful payload with a top-level success flag.

    Using ``Generic[DataT]`` lets FastAPI infer the response schema
    for each endpoint from its return type, keeping the OpenAPI spec
    precise without manual annotations.
    """
    success: bool = True
    data: DataT


class ErrorDetail(BaseModel):
    """Machine-readable error information.

    ``code`` is a domain-scoped constant (e.g. ``ENTITY_NOT_FOUND``)
    so that clients can handle errors programmatically rather than
    parsing human-oriented ``message`` strings.
    """
    message: str
    code: str


class ErrorResponse(BaseModel):
    """Standard error body returned by the global exception handler."""
    success: bool = False
    error: ErrorDetail
