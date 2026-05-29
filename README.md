# 🏦 Mundo Invest — Client Management & Pipefy Integration

Sistema interno para gestão de clientes e integração com Pipefy via GraphQL.

## Stack

- **Runtime:** Python 3.12+ FastAPI (async)
- **Banco:** PostgreSQL 16 (dev) / SQLite em memória (testes) / RDS PostgreSQL (produção)
- **ORM:** SQLAlchemy 2.0 (assíncrono)
- **Pipefy:** Mutations GraphQL estruturadas via dataclasses
- **Testes:** Pytest + HTTPX AsyncClient
- **Infra (produção):** AWS Lambda + API Gateway + RDS + DynamoDB (OpenTofu)
- **Local dev:** Floci (AWS emulator) + Docker Compose

## Pré-requisitos

- Python 3.10+
- Docker (para banco PostgreSQL local e Floci)
- OpenTofu >= 1.5.0 (para deploy na AWS)

## Setup

### Opção 1: Desenvolvimento Local (Recomendado)

```bash
# 1. Clonar repositório
git clone <repo-url> && cd mundo-invest-backend

# 2. Criar ambiente virtual
python -m venv .venv && source .venv/bin/activate

# 3. Instalar dependências
pip install -e ".[dev]"

# 4. Subir Floci + PostgreSQL + App
docker compose up --build

# 5. A API estará disponível em
open http://localhost:8000/docs
```

### Opção 2: Produção AWS

```bash
# 1. Configurar backend OpenTofu (primeira vez)
cd infrastructure
tofu init

# 2. Planejar deploy
tofu plan -var-file=environments/prod.tfvars \
    -var="database_username=admin" \
    -var="database_password=SecurePassword123" \
    -var="vpc_id=vpc-xxx" \
    -var="private_subnet_ids=[\"subnet-xxx\",\"subnet-yyy\"]" \
    -var="database_subnet_ids=[\"subnet-xxx\",\"subnet-yyy\"]"

# 3. Aplicar
tofu apply -var-file=environments/prod.tfvars \
    -var="database_username=admin" \
    -var="database_password=SecurePassword123" \
    -var="vpc_id=vpc-xxx" \
    -var="private_subnet_ids=[\"subnet-xxx\",\"subnet-yyy\"]" \
    -var="database_subnet_ids=[\"subnet-xxx\",\"subnet-yyy\"]"
```

## Testes

### Testes Unitários (SQLite em memória)

```bash
pytest -v --cov=app
```

### Testes de Integração (Floci)

```bash
# 1. Subir Floci
docker compose up --build

# 2. Rodar testes contra PostgreSQL
DATABASE_URL="postgresql+asyncpg://app:app123@localhost:5433/mundo_invest?sslmode=disable" \
pytest -v --cov=app
```

## Exemplos de Requisição

### Criar Cliente

**Local (Docker Compose):**
```bash
curl -X POST http://localhost:8000/clientes \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_nome": "João Silva",
    "cliente_email": "joao.silva@example.com",
    "tipo_solicitacao": "Atualização cadastral",
    "valor_patrimonio": 250000
  }'
```

**Produção (API Gateway):**
```bash
curl -X POST https://api-id.execute-api.us-east-1.amazonaws.com/prod/clientes \
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
  "email": "joao.silva@example.com",
  "nome": "João Silva",
  "renda_mensal": 20000.0,
  "created_at": "2026-05-29T12:00:00Z"
}
```

### Simular Webhook Pipefy

**Local:**
```bash
curl -X POST http://localhost:8000/webhooks/pipefy/card-updated \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_123",
    "card_id": "card_456",
    "cliente_email": "joao.silva@example.com",
    "timestamp": "2026-05-29T12:00:00Z"
  }'
```

**Produção:**
```bash
curl -X POST https://api-id.execute-api.us-east-1.amazonaws.com/prod/webhooks/pipefy/card-updated \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "evt_123",
    "card_id": "card_456",
    "cliente_email": "joao.silva@example.com",
    "timestamp": "2026-05-29T12:00:00Z"
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
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI)                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                             │
│  HTTP Request → Router → Pydantic Validator → Service       │
│                                     ↓                       │
│  Response ← Exception Handler ← Orchestrator                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                 BUSINESS LOGIC LAYER                        │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                             │
│  • ClientIngestionService                                   │
│  • WebhookProcessingService                                 │
│  • PriorityCalculator (regras: patrimônio ≥ 200k)           │
│  • PipefyGraphqlClient (mutations createCard/updateCard)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  DATA PERSISTENCE LAYER                     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                             │
│  Local: PostgreSQL/Floci              Production: RDS       │
│  Testes: SQLite (memória)              Lock: DynamoDB       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## ☁️ Visão de Produção (AWS)

### Arquitetura Serverless

```
┌─────────────────────────────────────────┐
│         API Gateway REST                │
│         (porta 443 HTTPS)               │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│      AWS Lambda (Python 3.12)           │
│      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│      Executa:                           │
│      • Mangum adapter                   │
│      • FastAPI (via Mangum)             │
│      • Código ZIP deployment            │
│                                         │
│      Handler: lambda_handler.handler    │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      ↓                 ↓
┌───────────┐    ┌──────────────┐
│ RDS       │    │ DynamoDB     │
│ PostgreSQL│    │ (State Lock) │
│ (porta    │    │              │
│  5432)    │    │              │
└───────────┘    └──────────────┘
```

### Mapeamento de Serviços

| Componente | Local | Produção AWS |
|------------|-------|--------------|
| **API** | FastAPI (uvicorn) | API Gateway REST + Lambda (Mangum) |
| **Runtime** | Docker container | AWS Lambda Python 3.12 |
| **Banco** | PostgreSQL/Floci | RDS PostgreSQL 16 |
| **State Lock** | - | DynamoDB (tofu-state-lock) |
| **Secrets** | .env | AWS Secrets Manager |
| **Logs** | stdout | CloudWatch Logs |
| **Infra** | docker-compose.yml | OpenTofu (.tf files) |
| **Monitoring** | - | CloudWatch Alarms |

### Deploy Local vs Produção

**Local (Docker Compose):**
- ✅ Desenvolvimento rápido
- ✅ Testes de integração
- ✅ Debugging fácil
- ❌ Não escala
- ❌ Single server

**Produção (AWS Lambda):**
- ✅ Escala automática
- ✅ Alta disponibilidade
- ✅ Pay-per-use
- ✅ Serverless (scale-to-zero)
- ✅ Gerenciado pela AWS

### Por que Lambda + Mangum?

**Problema:** FastAPI usa ASGI, AWS Lambda usa eventos JSON - são **incompatíveis**.

**Solução:** Mangum traduz eventos Lambda ↔ ASGI automaticamente.

**Benefício:** Mesmo código FastAPI funciona local (uvicorn) e produção (Lambda + Mangum).

## Estrutura do Projeto

```
mundo-invest/
├── app/
│   ├── api/v1/              → Endpoints (clientes.py, webhooks.py)
│   ├── schemas/             → Pydantic models (cliente.py, webhook.py)
│   ├── models/              → SQLAlchemy ORM (cliente.py, webhook_event.py)
│   ├── services/             → Regras de negócio + Pipefy GraphQL
│   │   ├── client_ingestion_service.py
│   │   ├── webhook_processing_service.py
│   │   ├── priority_calculator.py
│   │   └── pipefy_graphql_client.py  ← MUTATIONS GRAPHQL
│   ├── errors/              → Exceções de domínio + handlers
│   ├── core/                → Settings, configuration
│   ├── lambda_handler.py    → Mangum adapter para Lambda
│   └── main.py              → FastAPI bootstrap
│
├── infrastructure/          → OpenTofu (IaC AWS)
│   ├── provider.tf          → AWS provider + backend
│   ├── variables.tf         → Variáveis de input
│   ├── outputs.tf           → Outputs (API endpoint, etc)
│   ├── main.tf              → S3 buckets
│   ├── lambda.tf            → Lambda Function
│   ├── api_gateway.tf       → API Gateway REST
│   ├── rds.tf               → RDS PostgreSQL
│   ├── secret_manager.tf    → Secrets Manager
│   ├── security_group.tf    → Security Groups
│   ├── state_lock.tf        → DynamoDB state lock
│   ├── lambda_role.tf       → IAM Role
│   ├── policies.tf          → IAM Policies
│   ├── logs.tf              → CloudWatch Logs
│   ├── alarms.tf            → CloudWatch Alarms
│   ├── dev.tfvars           → Variáveis dev
│   └── prod.tfvars          → Variáveis production
│
├── scripts/                 → Scripts auxiliares
│   ├── deploy.sh            → Deploy Lambda ZIP
│   ├── init-floci.sh        → Inicializa Floci
│   └── init-rds.sql         → Init RDS
│
├── tests/                   → Pytest
├── docker-compose.yml       → Floci + App + OpenTofu
├── Dockerfile               → Containerização
├── pyproject.toml           → Dependências
└── README.md               → Esta documentação
```

## Pipefy GraphQL Mutations

As mutations do Pipefy foram estruturadas em `app/services/pipefy_graphql_client.py` seguindo a documentação oficial:

### 1. createCard Mutation

```python
MUTATION_CREATE_CARD = """
mutation createCard($pipeId: ID!, $fieldsAttributes: [FieldAttributesInput!]!) {
  createCard(input: { pipeId: $pipeId, fieldsAttributes: $fieldsAttributes }) {
    card { id }
  }
}
"""
```

**Referência:** [Pipefy GraphQL API - createCard](https://api-docs.pipefy.com/reference/mutations/createcard)

### 2. updateCardField Mutation

```python
MUTATION_UPDATE_CARD_FIELD = """
mutation updateCardField($input: UpdateCardFieldInput!) {
  updateCardField(input: $input) {
    success
  }
}
"""
```

**Referência:** [Pipefy GraphQL API - updateCardField](https://api-docs.pipefy.com/reference/mutations/updatecardfield)

## Testes Obrigatórios

### 1. Criação de cliente

```bash
pytest tests/test_clientes.py::test_create_cliente_success -v
```

### 2. Processamento de webhook com prioridade

```bash
# Patrimônio >= 200.000 → prioridade_alta
pytest tests/test_webhooks.py::test_webhook_card_updated_high_priority -v

# Patrimônio < 200.000 → prioridade_normal
pytest tests/test_webhooks.py::test_webhook_card_updated_normal_priority -v
```

### 3. Idempotência (event_id duplicado)

```bash
pytest tests/test_webhooks.py::test_webhook_idempotency -v
```

### Rodar todos os testes

```bash
pytest -v --cov=app
```

## Troubleshooting

### Erro: "Floci não inicia"

```bash
# Verificar se portas estão em uso
lsof -i :4566  # Floci
lsof -i :5433  # PostgreSQL

# Limpar volumes docker
docker compose down -v
docker compose up --build
```

### Erro: "Lambda timeout"

Aumentar `timeout` em `infrastructure/lambda.tf`

### Erro: "RDS connection failed"

Verificar security groups e VPC configuration em `infrastructure/security_group.tf`

## Referências

- [OpenTofu Documentation](https://opentofu.org/)
- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [Mangum Adapter](https://github.com/jordaneremieff/mangum)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pipefy GraphQL API](https://api-docs.pipefy.com/)
