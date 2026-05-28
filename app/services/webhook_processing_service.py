"""Orchestrator for the ``POST /webhooks/pipefy/card-updated`` flow.

This service coordinates five operations as a single logical unit:
idempotency check → client lookup → priority calculation →
Pipefy card update → local status update → event recording.

Why sequential instead of parallel:
Each step depends on the previous one (e.g. we cannot update
the local status before looking up the client), and the idempotency
check must happen first to prevent duplicate processing.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.webhook import WebhookEventCreate
from app.models.cliente import ClienteRepository
from app.models.webhook_event import WebhookEventRepository
from app.services.priority_calculator import PriorityCalculator
from app.services.pipefy_graphql_client import PipefyGraphQLClient
from app.errors.exceptions import IdempotencyConflictException, EntityNotFoundException

logger = logging.getLogger(__name__)


class WebhookProcessingService:
    """Orchestrates webhook event processing for Pipefy card updates.

    Each ``execute`` call is idempotent with respect to ``event_id``:
    if the same event is submitted twice, the second call raises
    ``IdempotencyConflictException`` and the database is not modified.
    """

    def __init__(self, session: AsyncSession, pipefy: PipefyGraphQLClient) -> None:
        self._cliente_repo = ClienteRepository(session)
        self._webhook_repo = WebhookEventRepository(session)
        self._pipefy = pipefy

    async def execute(self, data: WebhookEventCreate) -> dict:
        """Process a webhook event and return the processing result.

        The steps are intentionally ordered to minimise wasted work:
        the idempotency check and client lookup happen before any
        Pipefy API call.

        Returns:
            A dict with ``cliente_email``, ``prioridade``, and ``status``.
        """
        if await self._webhook_repo.exists(data.event_id):
            raise IdempotencyConflictException(data.event_id)

        cliente = await self._cliente_repo.get_by_email(data.cliente_email)
        if cliente is None:
            raise EntityNotFoundException("Cliente", data.cliente_email)

        prioridade = PriorityCalculator.calculate(cliente.valor_patrimonio)

        await self._pipefy.send_update_card_fields(
            card_id=data.card_id,
            fields=[
                ("updateStatus", "status", "Processado"),
                ("updatPrioridade", "prioridade", prioridade),
            ],
        )

        await self._cliente_repo.update_status_and_priority(
            email=data.cliente_email,
            status="Processado",
            prioridade=prioridade,
        )

        await self._webhook_repo.create(data)

        return {
            "cliente_email": data.cliente_email,
            "prioridade": prioridade,
            "status": "Processado",
        }
