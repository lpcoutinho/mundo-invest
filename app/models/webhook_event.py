"""SQLAlchemy model and repository for the ``webhook_events`` table.

Why a separate table for webhook events:
Each incoming webhook event carries a unique ``event_id`` that serves
as the idempotency key. Storing processed events allows the system
to reject duplicate deliveries with ``409 Conflict`` without relying
on an external cache or distributed lock.
"""
from datetime import datetime
from sqlalchemy import String, DateTime, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import Base
from app.schemas.webhook import WebhookEventCreate


class WebhookEventModel(Base):
    """Represents a processed Pipefy webhook event in the ``webhook_events`` table.

    ``event_id`` is the primary key — it is the idempotency token
    that prevents duplicate processing of the same webhook delivery.

    ``processed_at`` is set automatically by the database at insert
    time so that operators can audit when each event was handled.
    """
    __tablename__ = "webhook_events"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    card_id: Mapped[str] = mapped_column(String, nullable=False)
    cliente_email: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class WebhookEventRepository:
    """Data-access layer for ``WebhookEventModel``.

    Every public method is a single, self-contained unit of work
    so that service orchestrators can compose them without worrying
    about transaction boundaries.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists(self, event_id: str) -> bool:
        """Check whether a webhook event has already been processed.

        This is the core of the idempotency guarantee — the service
        layer calls ``exists`` *before* processing and raises
        ``IdempotencyConflictException`` if the event is a duplicate.
        """
        result = await self._session.execute(
            select(WebhookEventModel).where(WebhookEventModel.event_id == event_id)
        )
        return result.scalar_one_or_none() is not None

    async def create(self, data: WebhookEventCreate) -> WebhookEventModel:
        """Record a processed webhook event so future duplicates are rejected."""
        model = WebhookEventModel(**data.model_dump())
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model
