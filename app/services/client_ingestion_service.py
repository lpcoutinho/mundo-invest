"""Orchestrator for the ``POST /clientes`` flow.

This service sits between the HTTP router and the data/network layers,
coordinating two operations — local persistence and Pipefy card creation —
as a single logical unit of work.
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.cliente import ClienteCreate, ClienteResponse
from app.models.cliente import ClienteRepository
from app.services.pipefy_graphql_client import PipefyGraphQLClient

logger = logging.getLogger(__name__)


class ClientIngestionService:
    """Orchestrates client registration and Pipefy card mapping.

    Why split ``repository`` and ``pipefy`` into separate collaborators:
    Each has a distinct failure mode (database vs. network) and lifecycle.
    Separating them makes testing easier — we can mock the Pipefy client
    without affecting database assertions, and vice versa.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._repository = ClienteRepository(session)
        self._pipefy = PipefyGraphQLClient()

    async def execute(self, data: ClienteCreate) -> ClienteResponse:
        """Register a new client and simulate the corresponding Pipefy card.

        The flow is intentionally sequential — we persist locally first
        so that the client record exists even if the Pipefy call fails.
        """
        model = await self._repository.create(data)
        pipefy_response = await self._pipefy.send_create_card(
            nome=data.cliente_nome,
            email=data.cliente_email,
            patrimonio=data.valor_patrimonio,
            tipo_solicitacao=data.tipo_solicitacao,
        )
        pipefy_card_id = pipefy_response.get("data", {}).get("createCard", {}).get("card", {}).get("id")
        logger.debug("Pipefy card created: %s", pipefy_card_id)
        return ClienteResponse(
            cliente_nome=model.cliente_nome,
            cliente_email=model.cliente_email,
            tipo_solicitacao=model.tipo_solicitacao,
            valor_patrimonio=model.valor_patrimonio,
            status=model.status,
            prioridade=model.prioridade,
            pipefy_card_id=pipefy_card_id,
        )
