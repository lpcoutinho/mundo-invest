"""Domain exceptions that cross layer boundaries.

Each exception carries a machine-readable ``code`` so that the
global error handler can map it to an HTTP status without
coupling business logic to HTTP concepts.
"""
from typing import final


class DomainError(Exception):
    """Base for all domain-level errors.

    Why a custom hierarchy instead of built-in exceptions:
    The global handler in ``errors/handlers.py`` catches only
    ``DomainError`` subclasses, preventing implementation details
    (like SQLAlchemy errors) from leaking to the HTTP layer.
    """
    def __init__(self, message: str, code: str) -> None:
        self.message = message
        self.code = code
        super().__init__(message)


@final
class EntityNotFoundException(DomainError):
    """Raised when a required entity cannot be found by its identifier.

    Example:
        When ``ClienteRepository.update_status_and_priority`` is called
        with an email that does not exist in the database.
    """
    def __init__(self, entity: str, identifier: str) -> None:
        super().__init__(
            message=f"{entity} with identifier '{identifier}' not found.",
            code="ENTITY_NOT_FOUND",
        )


@final
class IdempotencyConflictException(DomainError):
    """Raised when a webhook event has already been processed.

    Idempotency is guaranteed by rejecting duplicate ``event_id``
    values rather than silently succeeding, so callers can detect
    and investigate unexpected replays.
    """
    def __init__(self, event_id: str) -> None:
        super().__init__(
            message=f"Webhook event '{event_id}' has already been processed.",
            code="IDEMPOTENCY_CONFLICT",
        )
