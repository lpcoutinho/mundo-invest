"""Integration tests for ``ClienteRepository`` and ``POST /clientes`` endpoint.

Repository tests exercise the data-access layer directly (bypassing HTTP).
Endpoint tests exercise the full stack: router → service → repository → SQLite.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from app.models.cliente import ClienteRepository
from app.schemas.cliente import ClienteCreate


class TestClienteRepository:
    """Repository-level data persistence for the ``clientes`` table."""

    async def test_create_cliente(self, session: AsyncSession):
        """A valid ``ClienteCreate`` should persist with status ``"Aguardando Análise"``.

        Why this matters:
        The default status is assigned by the repository, not the service.
        If the default changes here, every test that relies on the
        initial status must be updated.
        """
        repo = ClienteRepository(session)
        data = ClienteCreate(
            cliente_nome="João Silva",
            cliente_email="joao@example.com",
            tipo_solicitacao="Atualização cadastral",
            valor_patrimonio=250000.0,
        )
        model = await repo.create(data)
        assert model.cliente_email == "joao@example.com"
        assert model.cliente_nome == "João Silva"
        assert model.status == "Aguardando Análise"
        assert model.valor_patrimonio == 250000.0
        assert model.pipefy_card_id is None

    async def test_get_by_email_found(self, session: AsyncSession):
        """``get_by_email`` should return the model when the email exists."""
        repo = ClienteRepository(session)
        data = ClienteCreate(
            cliente_nome="Maria Souza",
            cliente_email="maria@example.com",
            tipo_solicitacao="Atualização cadastral",
            valor_patrimonio=100000.0,
        )
        await repo.create(data)
        model = await repo.get_by_email("maria@example.com")
        assert model is not None
        assert model.cliente_nome == "Maria Souza"

    async def test_get_by_email_not_found(self, session: AsyncSession):
        """``get_by_email`` should return ``None`` for non-existent emails.

        Why ``None`` instead of raising:
        The caller (the service layer) decides the appropriate error
        handling strategy. Returning ``None`` keeps the repository
        agnostic to HTTP semantics.
        """
        repo = ClienteRepository(session)
        model = await repo.get_by_email("notfound@example.com")
        assert model is None


class TestClienteEndpoint:
    """Integration tests for ``POST /clientes/`` via HTTP."""

    async def test_create_with_valid_payload_returns_201(self, client: AsyncClient):
        """A valid payload should return ``201`` with status ``"Aguardando Análise"``."""
        response = await client.post(
            "/clientes/",
            json={
                "cliente_nome": "João Silva",
                "cliente_email": "joao@example.com",
                "tipo_solicitacao": "Atualização cadastral",
                "valor_patrimonio": 250000.0,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["success"] is True
        assert body["data"]["status"] == "Aguardando Análise"
        assert body["data"]["cliente_email"] == "joao@example.com"
        assert body["data"]["prioridade"] is None
        assert body["data"]["pipefy_card_id"] is not None

    async def test_create_with_invalid_email_returns_422(self, client: AsyncClient):
        """An invalid email should return ``422``."""
        response = await client.post(
            "/clientes/",
            json={
                "cliente_nome": "João Silva",
                "cliente_email": "not-an-email",
                "tipo_solicitacao": "Atualização cadastral",
                "valor_patrimonio": 250000.0,
            },
        )
        assert response.status_code == 422

    async def test_create_with_missing_field_returns_422(self, client: AsyncClient):
        """A payload missing required fields should return ``422``."""
        response = await client.post(
            "/clientes/",
            json={"cliente_nome": "João Silva"},
        )
        assert response.status_code == 422

    async def test_create_with_negative_patrimonio_returns_422(self, client: AsyncClient):
        """A negative ``valor_patrimonio`` should return ``422``."""
        response = await client.post(
            "/clientes/",
            json={
                "cliente_nome": "João Silva",
                "cliente_email": "joao@example.com",
                "tipo_solicitacao": "Atualização cadastral",
                "valor_patrimonio": -100.0,
            },
        )
        assert response.status_code == 422
