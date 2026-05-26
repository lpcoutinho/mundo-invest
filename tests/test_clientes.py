from sqlalchemy.ext.asyncio import AsyncSession
from app.models.cliente import ClienteRepository
from app.schemas.cliente import ClienteCreate


class TestClienteRepository:
    async def test_create_cliente(self, session: AsyncSession):
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
        repo = ClienteRepository(session)
        model = await repo.get_by_email("notfound@example.com")
        assert model is None
