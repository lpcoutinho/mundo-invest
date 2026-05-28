"""Smoke test for the ``/health`` endpoint.

This is the minimal test that confirms the application can start
and respond to requests. It deliberately avoids database fixtures
so it can run even when the database is unreachable.
"""
from httpx import AsyncClient, ASGITransport
from app.main import app


async def test_health_returns_healthy():
    """``GET /health`` should return ``200`` with status ``"healthy"``.

    This is the first assertion the CI pipeline makes after
    starting the server — if this fails, the deployment is
    aborted before any traffic is routed.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "healthy"
        assert body["version"] == "0.1.0"
