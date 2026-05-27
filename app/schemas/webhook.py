"""Pydantic contract for the Pipefy webhook ingestion flow.

Why a dedicated schema for the webhook:
The incoming ``POST /webhooks/pipefy/card-updated`` payload carries
different fields than the client creation endpoint. Keeping them in
separate files prevents coupling between the two flows and makes
each schema's responsibility explicit.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class WebhookEventCreate(BaseModel):
    """Input contract for a Pipefy card-updated webhook event.

    ``event_id`` is the idempotency key — the system rejects duplicate
    ``event_id`` values with ``409 Conflict`` so that network retries
    or Pipefy replays do not produce duplicate processing.

    ``timestamp`` is expected as an ISO-8601 string (e.g.
    ``"2026-05-18T12:00:00Z"``) which Pydantic parses into a
    ``datetime`` instance automatically.
    """
    event_id: str = Field(..., min_length=1)
    card_id: str = Field(..., min_length=1)
    cliente_email: str = Field(..., min_length=1)
    timestamp: datetime
