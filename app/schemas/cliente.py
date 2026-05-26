"""Pydantic contracts for the client ingestion flow.

These schemas act as the system's boundary validators — every
``POST /clientes`` payload is checked here before any business
logic runs. The ``EmailStr`` type guarantees RFC-compliant email
format, and ``Field(ge=0)`` prevents negative asset values from
reaching the database or Pipefy.
"""
from pydantic import BaseModel, EmailStr, Field


class ClienteCreate(BaseModel):
    """Input contract for creating a new client.

    Why separate Create from Response:
    The incoming payload carries only user-supplied fields; the
    response later adds server-assigned ``status`` and ``prioridade``.
    This prevents callers from injecting state they shouldn't control.
    """
    cliente_nome: str = Field(..., min_length=1, max_length=200)
    cliente_email: EmailStr
    tipo_solicitacao: str = Field(..., min_length=1, max_length=100)
    valor_patrimonio: float = Field(..., ge=0)


class ClienteResponse(BaseModel):
    """Output contract returned after a successful client creation.

    ``prioridade`` is intentionally ``None`` at creation time — it
    is only set later when a webhook triggers the priority calculation.
    """
    cliente_nome: str
    cliente_email: str
    tipo_solicitacao: str
    valor_patrimonio: float
    status: str
    prioridade: str | None
    pipefy_card_id: str | None
