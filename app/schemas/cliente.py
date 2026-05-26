from pydantic import BaseModel, EmailStr, Field


class ClienteCreate(BaseModel):
    cliente_nome: str = Field(..., min_length=1, max_length=200)
    cliente_email: EmailStr
    tipo_solicitacao: str = Field(..., min_length=1, max_length=100)
    valor_patrimonio: float = Field(..., ge=0)


class ClienteResponse(BaseModel):
    cliente_nome: str
    cliente_email: str
    tipo_solicitacao: str
    valor_patrimonio: float
    status: str
    prioridade: str | None
