"""Shared fixtures for the test suite.

Why SQLite in-memory instead of PostgreSQL:
Tests must be self-contained and fast. SQLite in ``:memory:`` mode
starts in microseconds and requires no Docker dependency, letting
developers run the full suite with a single ``pytest`` command.

Each fixture has function scope so that every test starts with a
clean database, guaranteeing independence (F.I.R.S.T. principle).
"""
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture(scope="function")
async def engine():
    """Create a fresh SQLite in-memory database for each test.

    Tables are created once per fixture invocation and destroyed
    when the engine is disposed, ensuring zero state leakage
    between tests.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    from app.models.database import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def session(engine):
    """Provide a transactional database session.

    The session is bound to the in-memory engine and each call
    to this fixture gets an independent session with a clean
    transaction boundary.
    """
    SessionFactory = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionFactory() as s:
        yield s


@pytest.fixture(scope="function")
async def client(session):
    """Provide an HTTPX AsyncClient wired to the FastAPI app.

    Why manual dependency override instead of a real server:
    Using ``ASGITransport`` avoids port conflicts and startup delay,
    while ``dependency_overrides`` injects the test session so that
    every request hits the same in-memory database.
    """
    from app.models.database import get_session
    async def override_get_session():
        yield session
    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
