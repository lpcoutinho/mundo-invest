from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, func, select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import Base
from app.schemas.cliente import ClienteCreate
from app.errors.exceptions import EntityNotFoundException


class ClienteModel(Base):
    __tablename__ = "clientes"

    cliente_email: Mapped[str] = mapped_column(String, primary_key=True)
    cliente_nome: Mapped[str] = mapped_column(String, nullable=False)
    tipo_solicitacao: Mapped[str] = mapped_column(String, nullable=False)
    valor_patrimonio: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="Aguardando Análise")
    prioridade: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())


class ClienteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ClienteCreate) -> ClienteModel:
        model = ClienteModel(**data.model_dump(), status="Aguardando Análise")
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return model

    async def get_by_email(self, email: str) -> ClienteModel | None:
        result = await self._session.execute(
            select(ClienteModel).where(ClienteModel.cliente_email == email)
        )
        return result.scalar_one_or_none()

    async def update_status_and_priority(
        self, email: str, status: str, prioridade: str
    ) -> ClienteModel:
        model = await self.get_by_email(email)
        if model is None:
            raise EntityNotFoundException("Cliente", email)
        model.status = status
        model.prioridade = prioridade
        await self._session.commit()
        await self._session.refresh(model)
        return model
