"""FastAPI application entry-point.

Initialises the API, registers routers, and installs the global
exception handler. The ``/health`` endpoint is defined here because
it must be available before any versioned router — ALB and API Gateway
health checks target this path regardless of routing rules.
"""
from fastapi import FastAPI
from app.core.settings import settings

app = FastAPI(
    title="Mundo Invest Backend",
    version="0.1.0",
    debug=settings.DEBUG,
)


@app.get("/health")
async def health_check() -> dict:
    """Return service and connectivity status.

    Used by load balancers (ALB target group health checks) and
    the CI/CD smoke-test pipeline to confirm the application
    has started and can accept requests.
    """
    return {"status": "healthy", "version": "0.1.0"}
