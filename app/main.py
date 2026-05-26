"""FastAPI application entry-point.

Initialises the API, registers routers, and installs the global
exception handler. The ``/health`` endpoint is defined here because
it must be available before any versioned router — ALB and API Gateway
health checks target this path regardless of routing rules.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.settings import settings
from app.models.database import engine, Base
from app.errors.handlers import domain_error_handler
from app.errors.exceptions import DomainError
from app.api.v1.clientes import router as clientes_router
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,
)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
# logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on startup, dispose engine on shutdown.

    Why ``lifespan`` instead of ``@app.on_event``:
    The lifespan context manager is the recommended pattern in FastAPI
    0.115+ — it guarantees cleanup even when the event loop is
    interrupted by a signal.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Mundo Invest Backend",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_exception_handler(DomainError, domain_error_handler)
app.include_router(clientes_router)


@app.get("/health")
async def health_check() -> dict:
    """Return service and connectivity status.

    Used by load balancers (ALB target group health checks) and
    the CI/CD smoke-test pipeline to confirm the application
    has started and can accept requests.
    """
    return {"status": "healthy", "version": "0.1.0"}
