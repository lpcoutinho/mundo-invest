class DomainError(Exception):
    def __init__(self, message: str, code: str) -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class EntityNotFoundException(DomainError):
    def __init__(self, entity: str, identifier: str) -> None:
        super().__init__(
            message=f"{entity} with identifier '{identifier}' not found.",
            code="ENTITY_NOT_FOUND",
        )


class IdempotencyConflictException(DomainError):
    def __init__(self, event_id: str) -> None:
        super().__init__(
            message=f"Webhook event '{event_id}' has already been processed.",
            code="IDEMPOTENCY_CONFLICT",
        )
