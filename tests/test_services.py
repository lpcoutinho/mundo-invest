"""Tests for service-layer orchestrators and Pipefy mutation builders.

These sit between the pure unit tests (schemas, exceptions) and
full integration tests (endpoints). They exercise business logic
and external integration points while still running against an
in-memory database.
"""
import pytest
from app.services.pipefy_graphql_client import CreateCardMutation, UpdateCardFieldsMutation, PipefyGraphQLClient
from app.services.priority_calculator import PriorityCalculator
from app.services.client_ingestion_service import ClientIngestionService
from app.schemas.cliente import ClienteCreate


class TestCreateCardMutation:
    """Pipefy ``createCard`` mutation string builder.

    Why test mutation strings:
    The official Pipefy API expects an exact GraphQL syntax.
    Testing the built string catches structural regressions
    (missing brackets, wrong field names, etc.) before they
    reach production.
    Reference: https://developers.pipefy.com/reference/cards#card-mutations
    """

    def test_build_contains_create_card(self):
        """The built mutation should contain the ``createCard`` operation."""
        mutation = CreateCardMutation(
            pipe_id="307173097",
            title="João Silva - Atualização cadastral",
            fields_attributes=[
                {"field_id": "cliente_nome", "field_value": "João Silva"},
                {"field_id": "cliente_email", "field_value": "joao@example.com"},
                {"field_id": "tipo_solicitacao", "field_value": "Atualização cadastral"},
                {"field_id": "valor_patrimonio", "field_value": "250000"},
            ],
        )
        result = mutation.build()
        assert "mutation {" in result
        assert "createCard" in result
        assert 'pipe_id: "307173097"' in result
        assert "João Silva - Atualização cadastral" in result
        assert "cliente_nome" in result
        assert "cliente_email" in result
        assert "tipo_solicitacao" in result
        assert "valor_patrimonio" in result
        assert "id title" in result


class TestUpdateCardFieldsMutation:
    """Pipefy multi-field ``updateCardField`` mutation builder with aliases.

    This mutation replaces two separate calls with a single GraphQL
    request using operation aliases:
      mutation {
        updateStatus: updateCardField(...) { card { id } }
        updatPrioridade: updateCardField(...) { card { id } }
      }
    """

    def test_build_contains_both_aliases(self):
        """The built mutation should contain both aliased operations."""
        mutation = UpdateCardFieldsMutation(
            card_id="1357045729",
            field_updates=[
                ("updateStatus", "status", "Processado"),
                ("updatPrioridade", "prioridade", "prioridade_alta"),
            ],
        )
        result = mutation.build()
        assert "mutation {" in result
        assert "updateStatus" in result
        assert "updatPrioridade" in result
        assert "updateCardField" in result
        assert "1357045729" in result
        assert "status" in result
        assert "prioridade" in result
        assert "Processado" in result
        assert "prioridade_alta" in result


class TestPriorityCalculator:
    """Business rule for priority assignment based on ``valor_patrimonio``.

    The threshold is ``200_000.0``:
    - ``>= 200k`` → ``"prioridade_alta"``
    - ``< 200k`` → ``"prioridade_normal"``
    """

    def test_high_priority_when_patrimonio_above_threshold(self):
        """``valor_patrimonio >= 200_000`` should return ``"prioridade_alta"``."""
        assert PriorityCalculator.calculate(250000.0) == "prioridade_alta"

    def test_high_priority_when_patrimonio_at_threshold(self):
        """``valor_patrimonio == 200_000`` should return ``"prioridade_alta"``."""
        assert PriorityCalculator.calculate(200000.0) == "prioridade_alta"

    def test_normal_priority_when_patrimonio_below_threshold(self):
        """``valor_patrimonio < 200_000`` should return ``"prioridade_normal"``."""
        assert PriorityCalculator.calculate(50000.0) == "prioridade_normal"


class TestPipefyGraphQLClient:
    """Simulated Pipefy HTTP client."""

    async def test_send_create_card_returns_mock_response(self):
        """The client should return a dict matching Pipefy's real response shape.

        The mock response includes ``id`` and ``title`` fields so that
        callers (the ingestion service) can process the result without
        branching on simulation vs. production.
        """
        client = PipefyGraphQLClient("307173097")
        result = await client.send_create_card(
            nome="João Silva",
            email="joao@example.com",
            patrimonio=250000.0,
            tipo_solicitacao="Atualização cadastral",
        )
        assert "data" in result
        assert result["data"]["createCard"]["card"]["id"] == "1357045729"
        assert "João Silva" in result["data"]["createCard"]["card"]["title"]
        assert "Atualização cadastral" in result["data"]["createCard"]["card"]["title"]

    async def test_send_update_card_fields_returns_mock_response(self):
        """The client should return a dict with aliased operation keys."""
        client = PipefyGraphQLClient("307173097")
        result = await client.send_update_card_fields(
            card_id="1357045729",
            fields=[
                ("updateStatus", "status", "Processado"),
                ("updatPrioridade", "prioridade", "prioridade_alta"),
            ],
        )
        assert "data" in result
        assert result["data"]["updateStatus"]["card"]["id"] == "1357045729"
        assert result["data"]["updatPrioridade"]["card"]["id"] == "1357045729"


class TestClientIngestionService:
    """End-to-end orchestration of the client registration flow."""

    async def test_execute_creates_cliente_and_returns_response(self, session):
        """``execute`` should persist the client and return a ``ClienteResponse``.

        This test exercises the full service layer — validation schema,
        database repository, and Pipefy client — using the in-memory
        SQLite engine from ``conftest.py``.
        """
        service = ClientIngestionService(session, PipefyGraphQLClient("307173097"))
        data = ClienteCreate(
            cliente_nome="João Silva",
            cliente_email="joao@example.com",
            tipo_solicitacao="Atualização cadastral",
            valor_patrimonio=250000.0,
        )
        result = await service.execute(data)

        assert result.cliente_email == "joao@example.com"
        assert result.cliente_nome == "João Silva"
        assert result.status == "Aguardando Análise"
        assert result.valor_patrimonio == 250000.0
        assert result.prioridade is None
        assert result.pipefy_card_id == "1357045729"

    async def test_pipefy_card_id_is_persisted(self, session):
        """``pipefy_card_id`` should be saved in the database after creation."""
        from app.models.cliente import ClienteRepository

        service = ClientIngestionService(session, PipefyGraphQLClient("307173097"))
        data = ClienteCreate(
            cliente_nome="Maria Souza",
            cliente_email="maria@example.com",
            tipo_solicitacao="Atualização cadastral",
            valor_patrimonio=100000.0,
        )
        await service.execute(data)

        repo = ClienteRepository(session)
        model = await repo.get_by_email("maria@example.com")
        assert model is not None
        assert model.pipefy_card_id == "1357045729"


class TestWebhookProcessingService:
    """End-to-end orchestration of the webhook processing flow (Fluxo 2).

    Each test creates a client first via ``ClienteRepository``, then
    invokes ``WebhookProcessingService.execute()`` and asserts the
    processing result — covering priority calculation, idempotency,
    and error paths.
    """

    async def _create_cliente(self, session, email: str, patrimonio: float) -> None:
        """Helper to seed a test client without going through HTTP."""
        from app.models.cliente import ClienteRepository
        repo = ClienteRepository(session)
        await repo.create(ClienteCreate(
            cliente_nome="Test User",
            cliente_email=email,
            tipo_solicitacao="Atualização cadastral",
            valor_patrimonio=patrimonio,
        ))

    async def test_high_priority_for_high_patrimonio(self, session):
        """Patrimônio >= 200k should result in ``prioridade_alta``."""
        await self._create_cliente(session, "joao@example.com", 250000.0)
        from app.services.webhook_processing_service import WebhookProcessingService
        from app.schemas.webhook import WebhookEventCreate

        service = WebhookProcessingService(session, PipefyGraphQLClient("307173097"))
        result = await service.execute(WebhookEventCreate(
            event_id="evt_001",
            card_id="card_001",
            cliente_email="joao@example.com",
            timestamp="2026-05-18T12:00:00Z",
        ))
        assert result["prioridade"] == "prioridade_alta"
        assert result["status"] == "Processado"

    async def test_normal_priority_for_low_patrimonio(self, session):
        """Patrimônio < 200k should result in ``prioridade_normal``."""
        await self._create_cliente(session, "maria@example.com", 50000.0)
        from app.services.webhook_processing_service import WebhookProcessingService
        from app.schemas.webhook import WebhookEventCreate

        service = WebhookProcessingService(session, PipefyGraphQLClient("307173097"))
        result = await service.execute(WebhookEventCreate(
            event_id="evt_002",
            card_id="card_002",
            cliente_email="maria@example.com",
            timestamp="2026-05-18T12:00:00Z",
        ))
        assert result["prioridade"] == "prioridade_normal"
        assert result["status"] == "Processado"

    async def test_duplicate_event_id_raises_conflict(self, session):
        """Re-processing the same ``event_id`` should raise ``IdempotencyConflictException``."""
        await self._create_cliente(session, "dup@example.com", 250000.0)
        from app.services.webhook_processing_service import WebhookProcessingService
        from app.schemas.webhook import WebhookEventCreate
        from app.errors.exceptions import IdempotencyConflictException

        service = WebhookProcessingService(session, PipefyGraphQLClient("307173097"))
        event = WebhookEventCreate(
            event_id="evt_dup",
            card_id="card_dup",
            cliente_email="dup@example.com",
            timestamp="2026-05-18T12:00:00Z",
        )
        await service.execute(event)

        with pytest.raises(IdempotencyConflictException) as exc_info:
            await service.execute(event)
        assert "evt_dup" in str(exc_info.value.message)

    async def test_missing_client_raises_not_found(self, session):
        """A webhook for a non-existent client should raise ``EntityNotFoundException``."""
        from app.services.webhook_processing_service import WebhookProcessingService
        from app.schemas.webhook import WebhookEventCreate
        from app.errors.exceptions import EntityNotFoundException

        service = WebhookProcessingService(session, PipefyGraphQLClient("307173097"))

        with pytest.raises(EntityNotFoundException) as exc_info:
            await service.execute(WebhookEventCreate(
                event_id="evt_404",
                card_id="card_404",
                cliente_email="nonexistent@example.com",
                timestamp="2026-05-18T12:00:00Z",
            ))
        assert "nonexistent@example.com" in str(exc_info.value.message)
