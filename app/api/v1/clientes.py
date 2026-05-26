"""Thin router for ``POST /clientes`` — registers a client and maps it to Pipefy.

Why a separate router file:
Keeps the endpoint definition close to its input/output schemas and
prevents ``main.py`` from growing beyond a single screen of code.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.cliente import ClienteCreate, ClienteResponse
from app.schemas.responses import SuccessResponse
from app.models.database import get_session
from app.services.client_ingestion_service import ClientIngestionService

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.post(
    "/",
    response_model=SuccessResponse[ClienteResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client and simulate Pipefy card creation",
)
async def create_cliente(
    payload: ClienteCreate,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse[ClienteResponse]:
    """Persist a new client with status ``"Aguardando Análise"`` and
    simulate a Pipefy ``createCard`` mutation.

    The request follows this layered path:
        Router → ClientIngestionService → ClienteRepository + PipefyGraphQLClient

    Returns ``201`` with the persisted client data including the
    server-assigned ``status`` field.
    """
    service = ClientIngestionService(session)
    result = await service.execute(payload)
    return SuccessResponse(data=result)
