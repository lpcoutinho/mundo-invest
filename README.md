# 🏦 Mundo Invest — Client Management & Pipefy Integration

Sistema interno para gestão de clientes e integração com Pipefy via GraphQL.

## Stack

- **Runtime:** Python 3.12+ FastAPI (async)
- **Banco:** PostgreSQL 16 (dev) / SQLite em memória (testes)
- **ORM:** SQLAlchemy 2.0 (assíncrono)
- **Pipefy:** Mutations GraphQL estruturadas via dataclasses
- **Testes:** Pytest + HTTPX AsyncClient
- **Infra (produção):** AWS Lambda + API Gateway + DynamoDB (OpenTofu)

## Pré-requisitos

- Python 3.10+
- Docker (apenas para banco PostgreSQL local)

## Setup

```bash
# 1. Clonar repositório
git clone <repo-url> && cd mundo-invest-backend

# 2. Criar ambiente virtual
python -m venv .venv && source .venv/bin/activate

# 3. Instalar dependências
pip install -e ".[dev]"

# 4. Subir banco PostgreSQL (opcional — testes usam SQLite)
docker compose up -d

# 5. Rodar servidor
uvicorn app.main:app --reload --port 8000

# 6. Swagger UI
open http://localhost:8000/docs
```

## Testes

```bash
pytest -v --cov=app
```

## Exemplos de Requisição

### Criar Cliente

```bash
curl -X POST http://localhost:8000/clientes/ \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_nome": "João Silva",
    "cliente_email": "joao.silva@example.com",
    "tipo_solicitacao": "Atualização cadastral",
    "valor_patrimonio": 250000
  }'
```

Response: `201 Created`
```json
{
  "success": true,
  "data": {
    "cliente_nome": "João Silva",
    "cliente_email": "joao.silva@example.com",
    "tipo_solicitacao": "Atualização cadastral",
    "valor_patrimonio": 250000.0,
    "status": "Aguardando Análise",
    "prioridade": null
  }
}
```

### Simular Webhook Pipefy

```bash
curl -X POST http://localhost:8000/webhooks/pipefy/card-updated \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_123",
    "card_id": "card_456",
    "cliente_email": "joao.silva@example.com",
    "timestamp": "2026-05-18T12:00:00Z"
  }'
```

Response: `200 OK`
```json
{
  "success": true,
  "data": {
    "cliente_email": "joao.silva@example.com",
    "prioridade": "prioridade_alta",
    "status": "Processado"
  }
}
```

### Idempotência (event_id duplicado)

```bash
curl -X POST http://localhost:8000/webhooks/pipefy/card-updated \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_123",
    "card_id": "card_456",
    "cliente_email": "joao.silva@example.com",
    "timestamp": "2026-05-18T12:00:00Z"
  }'
```

Response: `409 Conflict`
```json
{
  "success": false,
  "error": {
    "message": "Webhook event 'evt_123' has already been processed.",
    "code": "IDEMPOTENCY_CONFLICT"
  }
}
```

## Arquitetura de Camadas

```
HTTP Request
    ↓
Router (thin, 3-10 linhas)
    ↓
Pydantic Validator (schemas)
    ↓
Service Orchestrator (regras de negócio + Pipefy mutations)
    ↓
Repository (SQLAlchemy → PostgreSQL)
    ↓
Global Exception Handler → JSON Response
```

## ☁️ Visão de Produção (AWS)

**Arquitetura escolhida: Serverless (Lambda + API Gateway + DynamoDB)**

| Componente | Serviço AWS | Função |
|------------|-------------|--------|
| **API** | API Gateway REST | Expõe `POST /clientes` e `POST /webhooks/pipefy/card-updated` com throttling |
| **Runtime** | AWS Lambda (Python 3.12 + Mangum) | Executa FastAPI, escala sob demanda |
| **Banco** | DynamoDB (On-Demand) | Tabela `clientes` (PK: email), tabela `webhook_events` (PK: event_id, TTL 7 dias) |
| **Idempotência** | DynamoDB `ConditionExpression` | `attribute_not_exists(event_id)` no `PutItem` — operação atômica, sem locks |
| **Infra** | OpenTofu | Módulos separados para staging/production |
| **Custo** | ~$0/mês ocioso | Pay-per-execution, scale-to-zero |

**Justificativa da escolha Serverless:**
1. Sistema interno = tráfego esporádico. Lambda scale-to-zero elimina custo ocioso.
2. DynamoDB `ConditionExpression` garante idempotência sem transações distribuídas.
3. Zero gerenciamento de pool de conexões (DynamoDB é HTTP-based).
4. Deploy simples: FastAPI + `Mangum` = uma Lambda function.

---

## Estrutura do Projeto

```
app/
  api/v1/       → Endpoints (clientes.py, webhooks.py)
  schemas/      → Pydantic models (cliente.py, webhook.py, responses.py)
  models/       → SQLAlchemy ORM + Repositories (cliente.py, webhook_event.py)
  services/     → Regras de negócio + Pipefy GraphQL
  errors/       → Exceções de domínio + handlers
  main.py       → Bootstrap FastAPI
tests/          → Pytest (SQLite em memória, Pipefy mockado)
```
