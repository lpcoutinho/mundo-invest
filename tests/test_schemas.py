from app.schemas.cliente import ClienteCreate, ClienteResponse
from app.schemas.responses import SuccessResponse, ErrorDetail
from app.errors.exceptions import EntityNotFoundException, IdempotencyConflictException
from pydantic import ValidationError
import pytest


class TestClienteCreateSchema:
    def test_valid_payload(self):
        data = ClienteCreate(
            cliente_nome="João Silva",
            cliente_email="joao@example.com",
            tipo_solicitacao="Atualização cadastral",
            valor_patrimonio=250000.0,
        )
        assert data.cliente_nome == "João Silva"
        assert data.cliente_email == "joao@example.com"

    def test_invalid_email_raises_error(self):
        with pytest.raises(ValidationError):
            ClienteCreate(
                cliente_nome="João Silva",
                cliente_email="not-an-email",
                tipo_solicitacao="Atualização cadastral",
                valor_patrimonio=250000.0,
            )

    def test_missing_field_raises_error(self):
        with pytest.raises(ValidationError):
            ClienteCreate(
                cliente_nome="João Silva",
                cliente_email="joao@example.com",
                tipo_solicitacao="Atualização cadastral",
            )

    def test_negative_patrimonio_raises_error(self):
        with pytest.raises(ValidationError):
            ClienteCreate(
                cliente_nome="João Silva",
                cliente_email="joao@example.com",
                tipo_solicitacao="Atualização cadastral",
                valor_patrimonio=-100.0,
            )


class TestClienteResponseSchema:
    def test_valid_response(self):
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
    def test_success_response(self):
        resp = SuccessResponse(data={"key": "value"})
        assert resp.success is True
        assert resp.data == {"key": "value"}

    def test_error_detail(self):
        error = ErrorDetail(message="Not found", code="NOT_FOUND")
        assert error.message == "Not found"
        assert error.code == "NOT_FOUND"


class TestDomainExceptions:
    def test_entity_not_found_message(self):
        exc = EntityNotFoundException("Cliente", "email@test.com")
        assert "Cliente" in str(exc.message)
        assert exc.code == "ENTITY_NOT_FOUND"

    def test_idempotency_conflict_message(self):
        exc = IdempotencyConflictException("evt_123")
        assert "evt_123" in str(exc.message)
        assert exc.code == "IDEMPOTENCY_CONFLICT"
