"""Tests for service-layer orchestrators and Pipefy mutation builders.

These sit between the pure unit tests (schemas, exceptions) and
full integration tests (endpoints). They exercise business logic
and external integration points while still running against an
in-memory database.
"""
from app.services.pipefy_graphql_client import CreateCardMutation, PipefyGraphQLClient
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
            pipe_id=123,
            title="João Silva - Atualização cadastral",
            fields_attributes=[
                {"field_id": "cliente_nome", "field_value": "João Silva"},
                {"field_id": "cliente_email", "field_value": "joao@example.com"},
                {"field_id": "valor_patrimonio", "field_value": "250000"},
            ],
        )
        result = mutation.build()
        assert "mutation {" in result
        assert "createCard" in result
        assert "pipe_id: 123" in result
        assert "João Silva - Atualização cadastral" in result
        assert "cliente_nome" in result
        assert "cliente_email" in result
        assert "valor_patrimonio" in result
        assert "id title" in result


class TestPipefyGraphQLClient:
    """Simulated Pipefy HTTP client."""

    async def test_send_create_card_returns_mock_response(self):
        """The client should return a dict matching Pipefy's real response shape.

        The mock response includes ``id`` and ``title`` fields so that
        callers (the ingestion service) can process the result without
        branching on simulation vs. production.
        """
        client = PipefyGraphQLClient()
        result = await client.send_create_card(
            nome="João Silva",
            email="joao@example.com",
            patrimonio=250000.0,
            tipo_solicitacao="Atualização cadastral",
        )
        assert "data" in result
        assert result["data"]["createCard"]["card"]["id"] is not None
        assert "João Silva" in result["data"]["createCard"]["card"]["title"]
        assert "Atualização cadastral" in result["data"]["createCard"]["card"]["title"]


class TestClientIngestionService:
    """End-to-end orchestration of the client registration flow."""

    async def test_execute_creates_cliente_and_returns_response(self, session):
        """``execute`` should persist the client and return a ``ClienteResponse``.

        This test exercises the full service layer — validation schema,
        database repository, and Pipefy client — using the in-memory
        SQLite engine from ``conftest.py``.
        """
        service = ClientIngestionService(session)
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
