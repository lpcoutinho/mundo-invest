"""Integration tests for ``ClienteRepository`` against SQLite in-memory.

These tests exercise the data-access layer directly, bypassing both
the HTTP router and the service orchestrator, so that repository
logic can be validated in isolation (F.I.R.S.T. principle).
"""
from sqlalchemy.ext.asyncio import AsyncSession
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
