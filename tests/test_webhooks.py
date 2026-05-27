"""Tests for webhook event persistence and the ``POST /webhooks/pipefy/card-updated`` endpoint.

Why a separate test file for webhooks:
The webhook flow (Fluxo 2) has distinct entities and business rules
from the client creation flow (Fluxo 1). Separating them prevents
test files from growing beyond a single screen and keeps the test
suite organised by domain concept.
"""
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.webhook import WebhookEventCreate
from app.models.webhook_event import WebhookEventRepository


class TestWebhookEventRepository:
    """Repository-level data persistence for the ``webhook_events`` table."""

    async def test_create_webhook_event(self, session: AsyncSession):
        """A valid ``WebhookEventCreate`` should persist all fields."""
        repo = WebhookEventRepository(session)
        data = WebhookEventCreate(
            event_id="evt_001",
            card_id="card_001",
            cliente_email="joao@example.com",
            timestamp=datetime(2026, 5, 18, 12, 0, 0),
        )
        model = await repo.create(data)
        assert model.event_id == "evt_001"
        assert model.card_id == "card_001"
        assert model.cliente_email == "joao@example.com"
        assert model.processed_at is not None

    async def test_exists_returns_true(self, session: AsyncSession):
        """``exists`` should return ``True`` when the event has been recorded."""
        repo = WebhookEventRepository(session)
        data = WebhookEventCreate(
            event_id="evt_002",
            card_id="card_002",
            cliente_email="maria@example.com",
            timestamp=datetime(2026, 5, 18, 12, 0, 0),
        )
        await repo.create(data)
        assert await repo.exists("evt_002") is True

    async def test_exists_returns_false(self, session: AsyncSession):
        """``exists`` should return ``False`` for an unknown ``event_id``."""
        repo = WebhookEventRepository(session)
        assert await repo.exists("evt_unknown") is False


class TestWebhookEndpoint:
    """Integration tests for ``POST /webhooks/pipefy/card-updated`` via HTTP."""

    async def test_webhook_high_priority(self, client: AsyncClient):
        """``valor_patrimonio >= 200k`` should result in ``prioridade_alta``."""
        await client.post("/clientes/", json={
            "cliente_nome": "João Silva",
            "cliente_email": "joao@example.com",
            "tipo_solicitacao": "Atualização cadastral",
            "valor_patrimonio": 250000.0,
        })
        response = await client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_001",
            "card_id": "card_001",
            "cliente_email": "joao@example.com",
            "timestamp": "2026-05-18T12:00:00Z",
        })
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["prioridade"] == "prioridade_alta"
        assert body["data"]["status"] == "Processado"

    async def test_webhook_normal_priority(self, client: AsyncClient):
        """``valor_patrimonio < 200k`` should result in ``prioridade_normal``."""
        await client.post("/clientes/", json={
            "cliente_nome": "Maria Souza",
            "cliente_email": "maria@example.com",
            "tipo_solicitacao": "Atualização cadastral",
            "valor_patrimonio": 50000.0,
        })
        response = await client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_002",
            "card_id": "card_002",
            "cliente_email": "maria@example.com",
            "timestamp": "2026-05-18T12:00:00Z",
        })
        assert response.status_code == 200
        assert response.json()["data"]["prioridade"] == "prioridade_normal"

    async def test_webhook_idempotency_returns_409(self, client: AsyncClient):
        """Re-processing the same ``event_id`` should return ``409 Conflict``."""
        await client.post("/clientes/", json={
            "cliente_nome": "Carlos Lima",
            "cliente_email": "carlos@example.com",
            "tipo_solicitacao": "Atualização cadastral",
            "valor_patrimonio": 300000.0,
        })
        payload = {
            "event_id": "evt_dup",
            "card_id": "card_dup",
            "cliente_email": "carlos@example.com",
            "timestamp": "2026-05-18T12:00:00Z",
        }
        response1 = await client.post("/webhooks/pipefy/card-updated", json=payload)
        assert response1.status_code == 200

        response2 = await client.post("/webhooks/pipefy/card-updated", json=payload)
        assert response2.status_code == 409
        assert response2.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"

    async def test_webhook_client_not_found_returns_404(self, client: AsyncClient):
        """A webhook for a non-existent client should return ``404``."""
        response = await client.post("/webhooks/pipefy/card-updated", json={
            "event_id": "evt_404",
            "card_id": "card_404",
            "cliente_email": "nonexistent@example.com",
            "timestamp": "2026-05-18T12:00:00Z",
        })
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "ENTITY_NOT_FOUND"
