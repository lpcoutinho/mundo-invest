"""SQLAlchemy async engine, session factory, and declarative base.

Why async:
This system is I/O-bound (HTTP calls to Pipefy via GraphQL).
An async engine lets the event loop handle concurrent requests
without allocating a thread per connection.
"""
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.settings import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models.

    Every model in ``app/models/`` inherits from this so that
    ``Base.metadata.create_all()`` can discover and create tables
    automatically at startup.
    """


engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """FastAPI dependency that yields a database session.

    Usage in routers:
        ``session: AsyncSession = Depends(get_session)``

    The session is automatically closed when the request ends,
    and the generator pattern lets FastDI handle cleanup even
    when an exception occurs mid-request.
    """
    async with SessionFactory() as session:
        yield session
