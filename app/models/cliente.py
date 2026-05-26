"""SQLAlchemy model and repository for the ``clientes`` table.

Why model + repository in the same file:
The repository is the only consumer of the model's ORM API.
Keeping them together preserves SRP (one domain concept per file)
without scattering model definitions across many modules.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import Base
from app.schemas.cliente import ClienteCreate
from app.errors.exceptions import EntityNotFoundException


class ClienteModel(Base):
    """Represents a client record in the ``clientes`` table.

    ``status`` defaults to ``"Aguardando Análise"`` at creation
    and is later updated to ``"Processado"`` when a webhook event
    confirms processing. ``prioridade`` is ``NULL`` until the
    webhook-driven business rule calculates it.
    """
    __tablename__ = "clientes"

    cliente_email: Mapped[str] = mapped_column(String, primary_key=True)
    cliente_nome: Mapped[str] = mapped_column(String, nullable=False)
    tipo_solicitacao: Mapped[str] = mapped_column(String, nullable=False)
    valor_patrimonio: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="Aguardando Análise"
    )
    prioridade: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )


class ClienteRepository:
    """Data-access layer for ``ClienteModel``.

    Every public method is a single, self-contained unit of work
    so that service orchestrators can compose them without worrying
    about transaction boundaries.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ClienteCreate) -> ClienteModel:
        """Persist a new client with ``status = "Aguardando Análise"``.

        Why the default status is set here rather than in the service:
        The repository is the single authority on initial state,
        so we don't have to remember to set it in every service
        that creates a client.
        """
        model = ClienteModel(**data.model_dump(), status="Aguardando Análise")
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model

    async def get_by_email(self, email: str) -> ClienteModel | None:
        """Look up a client by email.

        Returns ``None`` instead of raising when not found so that
        callers (services) can decide the appropriate error handling.
        """
        result = await self._session.execute(
            select(ClienteModel).where(ClienteModel.cliente_email == email)
        )
        return result.scalar_one_or_none()

    async def update_status_and_priority(
        self, email: str, status: str, prioridade: str
    ) -> ClienteModel:
        """Update a client's processing status and calculated priority.

        Raises:
            EntityNotFoundException: If no client exists with the given email.
        """
        model = await self.get_by_email(email)
        if model is None:
            raise EntityNotFoundException("Cliente", email)
        model.status = status
        model.prioridade = prioridade
        await self._session.commit()
        await self._session.refresh(model)
        return model
