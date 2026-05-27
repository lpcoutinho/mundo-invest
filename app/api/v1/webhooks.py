"""Thin router for ``POST /webhooks/pipefy/card-updated`` — processes Pipefy card updates.

This endpoint simulates receiving a webhook from Pipefy when a card
is updated. It calculates the client's priority based on their
invested assets and updates both the local database and the Pipefy
card status.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.webhook import WebhookEventCreate
from app.schemas.responses import SuccessResponse
from app.models.database import get_session
from app.core.settings import settings
from app.services.pipefy_graphql_client import PipefyGraphQLClient
from app.services.webhook_processing_service import WebhookProcessingService

router = APIRouter(prefix="/webhooks/pipefy", tags=["Webhooks"])


@router.post(
    "/card-updated",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Simulate Pipefy card-updated webhook with idempotency and priority calculation",
)
async def card_updated(
    payload: WebhookEventCreate,
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse:
    """Process a Pipefy card-updated webhook event.

    The flow is:
        1. Check idempotency (reject duplicate ``event_id`` with 409)
        2. Look up the client by email (404 if not found)
        3. Calculate priority based on ``valor_patrimonio``
        4. Simulate ``updateCardField`` mutations on Pipefy
        5. Update local database status and priority
        6. Record the event for future idempotency checks

    Returns ``200`` with the processing result including the
    calculated ``prioridade`` and updated ``status``.
    """
    pipefy = PipefyGraphQLClient(settings.PIPEFY_PIPE_ID)
    service = WebhookProcessingService(session, pipefy)
    result = await service.execute(payload)
    return SuccessResponse(data=result)
