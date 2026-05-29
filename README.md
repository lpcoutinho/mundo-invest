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
- **Automação:** Makefile

## 🎯 Por que FastAPI + Mangum + Lambda?

**Problema**: FastAPI usa ASGI, AWS Lambda usa eventos JSON - são **incompatíveis**.

**Solução**: Mangum traduz eventos Lambda ↔ ASGI automaticamente.

**Benefício**: Mesmo código FastAPI funciona local (uvicorn) e produção (Lambda + Mangum).

```python
# app/lambda_handler.py
from mangum import Mangum
from app.main import app

def handler(event, context):
    """Handler para AWS Lambda - traduz Lambda event → ASGI"""
    mangum_handler = Mangum(app, lifespan="off")
    return mangum_handler(event, context)
```

**Como funciona**:
1. API Gateway recebe HTTP request
2. API Gateway invoca Lambda com evento JSON
3. Mangum traduz evento JSON → ASGI request
4. FastAPI processa como se fosse um servidor ASGI
5. Mangum traduz response ASGI → JSON
6. API Gateway retorna HTTP response

## ☁️ Arquitetura AWS vs Local

### Produção AWS (Serverless)

```
┌─────────────────────────────────────────┐
│         API Gateway REST                │
│         (porta 443 HTTPS)                │
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│      AWS Lambda (Python 3.12)          │
│      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│      • Mangum adapter (Lambda ↔ ASGI)   │
│      • FastAPI                           │
│      • ZIP deployment (30MB)             │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      ↓                 ↓
┌───────────┐    ┌──────────────┐
│ RDS       │    │ DynamoDB     │
│ PostgreSQL│    │ (State Lock) │
└───────────┘    └──────────────┘
```

### Local com Floci (Desenvolvimento)

```
┌─────────────────────────────────────────┐
│      Docker Compose (localhost)         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                          │
│  ┌──────────┐   ┌──────────┐            │
│  │ Floci    │   │ Postgres │            │
│  │ (4566)   │   │ (5433)   │            │
│  └──────────┘   └──────────┘            │
│       ↓              ↑                   │
│  ┌──────────────────────────┐           │
│  │  FastAPI (localhost:8000) │           │
│  └──────────────────────────┘           │
│                                          │
└─────────────────────────────────────────┘
```

### Mapeamento de Serviços

| Componente | Local | Produção AWS |
|------------|-------|--------------|
| **API** | FastAPI (uvicorn) | API Gateway + Lambda (Mangum) |
| **Runtime** | Docker container | AWS Lambda Python 3.12 |
| **Banco** | PostgreSQL/Floci | RDS PostgreSQL 16 |
| **State Lock** | - | DynamoDB (tofu-state-lock) |
| **Secrets** | .env | AWS Secrets Manager |
| **Logs** | stdout | CloudWatch Logs |
| **Infra** | docker-compose.yml | OpenTofu (.tf files) |
| **Monitoring** | - | CloudWatch Alarms |

## 🔧 OpenTofu - Infraestrutura como Código

**O que é**: OpenTofu é um fork open-source do Terraform para provisionar infraestrutura AWS.

**Por que usar**:
- ✅ Infraestrutura versionada no Git
- ✅ Deploy reproduzível
- ✅ State lock via DynamoDB
- ✅ Plan/Apply para segurança

**Exemplo de código**:
```hcl
# infrastructure/lambda.tf
resource "aws_lambda_function" "app" {
  function_name    = "mundo-invest-prod-app"
  description     = "Mundo Invest Backend - FastAPI + Mangum"
  runtime         = "python3.12"
  handler         = "app.lambda_handler.handler"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      DEBUG   = "false"
      ENV     = "prod"
      DATABASE_URL_SECRET_ARN = aws_secretsmanager_secret.database_url.arn
    }
  }
}
```

**Recursos criados automaticamente (43 total)**:
- Lambda Function (Python 3.12)
- API Gateway REST + Resources + Methods
- RDS PostgreSQL (db.t3.micro)
- DynamoDB Table (state lock)
- IAM Roles + Policies
- Security Groups
- CloudWatch Logs + Alarms
- Secrets Manager
- S3 Buckets

## 🚀 Floci - AWS Emulator para Local

**O que é**: Floci é um emulator de serviços AWS para desenvolvimento local.

**Serviços suportados**:
- Lambda (execução local)
- API Gateway (porta 4566)
- DynamoDB (porta 4566)
- S3 (porta 4566)
- SQS (porta 4566)

**Benefícios**:
- ✅ Desenvolvimento rápido sem custos AWS
- ✅ Testes de integração realistas
- ✅ Debugging fácil
- ✅ CI/CD mais rápido

**Exemplo de uso**:
```bash
# 1. Buildar e subir todo o stack
make build && make up

# 2. Criar recursos
bash scripts/init-floci.sh

# 3. Testar OpenTofu local
AWS_ACCESS_KEY_ID=test_access_key \
AWS_SECRET_ACCESS_KEY=test_secret_key \
AWS_ENDPOINT_URL=http://localhost:4566 \
tofu plan -var-file=environments/dev.tfvars
```

## Pré-requisitos

- Python 3.10+
- Docker (para banco PostgreSQL local e Floci)
- OpenTofu >= 1.5.0 (para deploy na AWS)
- make

## Comandos Make

O projeto utiliza `make` para automatizar tarefas comuns de desenvolvimento e Docker.

### Desenvolvimento Local

| Comando | Descrição |
|---------|-----------|
| `make install` | Instalar dependências do projeto |
| `make dev` | Instalar dependências incluindo dev |
| `make lint` | Rodar ruff (linter) |
| `make typecheck` | Rodar mypy (type checker) |
| `make check` | Rodar lint + typecheck |
| `make test` | Rodar testes com pytest |
| `make test-cov` | Rodar testes com cobertura |
| `make run` | Subir servidor uvicorn |

### Docker

| Comando | Descrição |
|---------|-----------|
| `make build` | Build da imagem Docker da aplicação |
| `make up` | Subir todo o stack (postgres + floci + app) |
| `make down` | Derrubar todos os serviços |
| `make db-up` | Subir apenas PostgreSQL via Docker |
| `make db-down` | Parar apenas PostgreSQL |
| `make logs` | Tail dos logs do container app |
| `make shell` | Bash interativo no container app |
| `make test-docker` | Rodar pytest dentro do container app |
| `make clean-docker` | Derrubar tudo e remover volumes |

### Utilitários

| Comando | Descrição |
|---------|-----------|
| `make clean` | Remover cache e artefatos |

## Setup

### Opção 1: Desenvolvimento Local com Docker (Recomendado)

```bash
# 1. Clonar repositório
git clone <repo-url> && cd mundo-invest-backend

# 2. Criar ambiente virtual
python -m venv .venv && source .venv/bin/activate

# 3. Instalar dependências
make dev

# 4. Buildar imagem e subir stack completo
make build && make up

# 5. A API estará disponível em
open http://localhost:8000/docs

# Para acompanhar os logs
make logs
```

### Opção 2: Desenvolvimento Local Só com Python

```bash
# 1. Clonar repositório
git clone <repo-url> && cd mundo-invest-backend

# 2. Criar ambiente virtual
python -m venv .venv && source .venv/bin/activate

# 3. Instalar dependências
make dev

# 4. Subir apenas o PostgreSQL
make db-up

# 5. Rodar servidor localmente
make run
```

### Opção 3: Windows (PowerShell)

No Windows o `make` não está disponível nativamente. Instale via [Chocolatey](https://chocolatey.org/) ou use os comandos `docker compose` diretamente.

```powershell
# ── Instalar make (opcional, recomentado) ──
choco install make

# ── Setup ──
git clone <repo-url>
cd mundo-invest-backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

# ── Docker (precisa do Docker Desktop) ──
docker compose build app
docker compose up -d

# ── Logs ──
docker compose logs -f app

# ── Shell interativo ──
docker compose exec app cmd

# ── Testes dentro do container ──
docker compose run --rm app pytest -v

# ── Derrubar tudo ──
docker compose down

# ── Limpar volumes ──
docker compose down -v
```

> **Alternativa sem `make`**: Use os comandos `docker compose` acima diretamente no PowerShell. Todos os targets do Makefile têm equivalentes manuais listados na seção "Comandos Make".

### Opção 4: Produção AWS

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
make test-cov
```

### Testes de Integração (Floci + PostgreSQL)

```bash
# 1. Subir stack completo
make build && make up

# 2. Rodar testes dentro do container (conectado ao PostgreSQL/Floci)
make test-docker
```

### Testes Específicos

```bash
# Criação de cliente
make test-docker ARGS="tests/test_clientes.py::test_create_cliente_success -v"

# Webhook com prioridade alta (patrimônio >= 200.000)
make test-docker ARGS="tests/test_webhooks.py::test_webhook_card_updated_high_priority -v"

# Webhook com prioridade normal (patrimônio < 200.000)
make test-docker ARGS="tests/test_webhooks.py::test_webhook_card_updated_normal_priority -v"

# Idempotência (event_id duplicado)
make test-docker ARGS="tests/test_webhooks.py::test_webhook_idempotency -v"
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

**Nota:** Para `valor_patrimonio >= 200000` retorna `prioridade_alta`. Para `< 200000` retorna `prioridade_normal`.

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

## 🔄 Fluxo Completo da Aplicação

### Fluxo 1: Criar Cliente (POST /clientes)

```
┌─────────────────────────────────────────────────────────────┐
│  1. HTTP Request                                            │
│  POST /clientes {"cliente_nome": "...", "cliente_email": ...}│
└──────────────┬──────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│  2. API Layer (app/api/v1/clientes.py)                     │
│  • Pydantic valida campos obrigatórios                      │
│  • EmailStr valida formato email                            │
│  • Field(ge=0) valida patrimonio não-negativo               │
└──────────────┬──────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Business Logic (ClientIngestionService)                 │
│  • ClienteRepository.create() → persiste no banco           │
│  • PipefyGraphQLClient.createCard() → cria card Pipefy      │
│  • Retorna ClienteResponse com status + card_id            │
└──────────────┬──────────────────────────────────────────────┘
               │
      ┌────────┴────────┐
      ↓                 ↓
┌───────────┐    ┌──────────────┐
│ Banco     │    │ Pipefy API   │
│ SQLAlchemy│    │ GraphQL      │
└───────────┘    └──────────────┘
```

**Código chave**:
```python
# app/services/client_ingestion_service.py
async def execute(self, payload: ClienteCreate) -> ClienteResponse:
    # 1. Persistir no banco
    cliente = await self.repository.create(payload)

    # 2. Criar card no Pipefy
    card_id = await self.pipefy.create_card(cliente)

    # 3. Atualizar com card_id
    cliente.pipefy_card_id = card_id
    return await self.repository.update(cliente)
```

### Fluxo 2: Webhook de Prioridade (POST /webhooks/pipefy/card-updated)

```
┌─────────────────────────────────────────────────────────────┐
│  1. Webhook Request (Pipefy)                                │
│  POST /webhooks/pipefy/card-updated {event_id, card_id, ...}│
└──────────────┬──────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│  2. API Layer (app/api/v1/webhooks.py)                     │
│  • Verifica idempotência (event_id já processado?)         │
│  • Retorna 409 Conflict se duplicado                        │
└──────────────┬──────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Business Logic (WebhookProcessingService)             │
│  • Busca cliente por email                                  │
│  • PriorityCalculator calcula prioridade:                   │
│    - valor_patrimonio >= 200000 → "prioridade_alta"        │
│    - valor_patrimonio < 200000 → "prioridade_normal"       │
│  • PipefyGraphQLClient.updateCard() → atualiza Pipefy      │
│  • ClienteRepository.update() → persiste no banco         │
└──────────────┬──────────────────────────────────────────────┘
               │
      ┌────────┴────────┐
      ↓                 ↓
┌───────────┐    ┌──────────────┐
│ Banco     │    │ Pipefy API   │
│ (update)  │    │ (mutation)  │
└───────────┘    └──────────────┘
```

**Código chave**:
```python
# app/services/priority_calculator.py
def calculate(valor_patrimonio: float) -> str:
    if valor_patrimonio >= 200000:
        return "prioridade_alta"
    return "prioridade_normal"
```

### Idempotência em Webhooks

**Problema**: Pipefy pode reenviar webhooks duplicados.

**Solução**: Tabela `webhook_events` com constraint unique em `event_id`.

```python
# app/models/webhook_event.py
class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: UUID = Column(UUID, primary_key=True)
    event_id: str = Column(String, unique=True, nullable=False)  # ← Unique!
    card_id: int = Column(Integer, nullable=False)
    payload: dict = Column(JSONB, nullable=False)
    processado_em: datetime = Column(DateTime, nullable=True)
```

**Resultado**: Event_id duplicado → `IntegrityError` → `409 Conflict`

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
│  • WebhookProcessingService │
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
├── Makefile                 → Automação (build, up, test, etc.)
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
make test-docker ARGS="tests/test_clientes.py::test_create_cliente_success -v"
```

### 2. Processamento de webhook com prioridade

```bash
# Patrimônio >= 200.000 → prioridade_alta
make test-docker ARGS="tests/test_webhooks.py::test_webhook_card_updated_high_priority -v"

# Patrimônio < 200.000 → prioridade_normal
make test-docker ARGS="tests/test_webhooks.py::test_webhook_card_updated_normal_priority -v"
```

### 3. Idempotência (event_id duplicado)

```bash
make test-docker ARGS="tests/test_webhooks.py::test_webhook_idempotency -v"
```

### Rodar todos os testes

```bash
make test-docker
```

## Troubleshooting

### Erro: "Floci não inicia"

```bash
# Verificar se portas estão em uso
lsof -i :4566  # Floci
lsof -i :5433  # PostgreSQL

# Limpar volumes docker e rebuildar
make clean-docker && make build && make up
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
