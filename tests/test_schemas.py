"""Unit tests for Pydantic schemas, domain exceptions, and error handlers.

These tests validate the system's boundary contracts without
touching the database or HTTP stack, making them the fastest
layer in the test suite.
"""
from pydantic import ValidationError
import pytest
from fastapi import Request
from app.schemas.cliente import ClienteCreate, ClienteResponse
from app.schemas.responses import SuccessResponse, ErrorDetail
from app.errors.exceptions import (
    EntityNotFoundException,
    IdempotencyConflictException,
)
from app.errors.handlers import domain_error_handler


class TestClienteCreateSchema:
    """Input validation rules for ``POST /clientes``."""

    def test_valid_payload(self):
        """All required fields with valid data should create successfully."""
        data = ClienteCreate(
            cliente_nome="João Silva",
            cliente_email="joao@example.com",
            tipo_solicitacao="Atualização cadastral",
            valor_patrimonio=250000.0,
        )
        assert data.cliente_nome == "João Silva"
        assert data.cliente_email == "joao@example.com"

    def test_invalid_email_raises_error(self):
        """Non-RFC emails should be rejected by Pydantic's ``EmailStr``."""
        with pytest.raises(ValidationError):
            ClienteCreate(
                cliente_nome="João Silva",
                cliente_email="not-an-email",
                tipo_solicitacao="Atualização cadastral",
                valor_patrimonio=250000.0,
            )

    def test_missing_field_raises_error(self):
        """Omitting a required field should produce a ``ValidationError``."""
        with pytest.raises(ValidationError):
            ClienteCreate(
                cliente_nome="João Silva",
                cliente_email="joao@example.com",
                tipo_solicitacao="Atualização cadastral",
            )

    def test_negative_patrimonio_raises_error(self):
        """``valor_patrimonio`` should be non-negative (``ge=0``)."""
        with pytest.raises(ValidationError):
            ClienteCreate(
                cliente_nome="João Silva",
                cliente_email="joao@example.com",
                tipo_solicitacao="Atualização cadastral",
                valor_patrimonio=-100.0,
            )


class TestClienteResponseSchema:
    """Output contract for client data returned by the API."""

    def test_valid_response(self):
        """All fields should be present, including nullable ``prioridade``."""
        data = ClienteResponse(
            cliente_nome="João Silva",
            cliente_email="joao@example.com",
            tipo_solicitacao="Atualização cadastral",
            valor_patrimonio=250000.0,
            status="Aguardando Análise",
            prioridade=None,
        )
        assert data.status == "Aguardando Análise"


class TestResponseSchemas:
    """Generic success/error response wrappers."""

    def test_success_response(self):
        """``SuccessResponse`` should wrap data with ``success: true``."""
        resp = SuccessResponse(data={"key": "value"})
        assert resp.success is True
        assert resp.data == {"key": "value"}

    def test_error_detail(self):
        """``ErrorDetail`` should carry both a human message and a machine code."""
        error = ErrorDetail(message="Not found", code="NOT_FOUND")
        assert error.message == "Not found"
        assert error.code == "NOT_FOUND"


class TestDomainExceptions:
    """Domain exception hierarchy and message formatting."""

    def test_entity_not_found_message(self):
        """``EntityNotFoundException`` should include entity type and identifier."""
        exc = EntityNotFoundException("Cliente", "email@test.com")
        assert "Cliente" in str(exc.message)
        assert exc.code == "ENTITY_NOT_FOUND"

    def test_idempotency_conflict_message(self):
        """``IdempotencyConflictException`` should include the duplicate ``event_id``."""
        exc = IdempotencyConflictException("evt_123")
        assert "evt_123" in str(exc.message)
        assert exc.code == "IDEMPOTENCY_CONFLICT"


class TestErrorHandler:
    """Global exception handler → HTTP status mapping."""

    async def test_entity_not_found_returns_404(self):
        """``EntityNotFoundException`` should produce a ``404`` JSON response."""
        exc = EntityNotFoundException("Cliente", "test@example.com")
        scope = {"type": "http", "method": "GET", "path": "/"}
        request = Request(scope)
        response = await domain_error_handler(request, exc)

        assert response.status_code == 404
        body = response.body.decode()
        assert "ENTITY_NOT_FOUND" in body
        assert "test@example.com" in body

    async def test_idempotency_conflict_returns_409(self):
        """``IdempotencyConflictException`` should produce a ``409`` JSON response."""
        exc = IdempotencyConflictException("evt_dup")
        scope = {"type": "http", "method": "POST", "path": "/"}
        request = Request(scope)
        response = await domain_error_handler(request, exc)

        assert response.status_code == 409
        body = response.body.decode()
        assert "IDEMPOTENCY_CONFLICT" in body
        assert "evt_dup" in body
