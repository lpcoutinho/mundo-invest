import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture(scope="function")
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    from app.models.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def session(engine):
    SessionFactory = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionFactory() as s:
        yield s


@pytest.fixture(scope="function")
async def client(session):
    from app.models.database import get_session
    async def override_get_session():
        yield session
    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
