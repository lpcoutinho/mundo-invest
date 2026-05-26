# Video Guide: Client Management & Pipefy Integration

> Documento de apoio para gravação do vídeo de defesa técnica (máx. 7 min).
> Teste técnico — Desenvolvedor Backend — Mundo Invest

---

## 1. Estrutura do Vídeo (7 min)

| Seção | Duração | Conteúdo |
|-------|---------|----------|
| **Abertura** | 30s | Quem sou, background técnico, stack escolhida |
| **Arquitetura** | 1min30s | Pastas, camadas, decisões técnicas |
| **Mutation #1 — createCard** | 1min30s | Código + como encontrei na doc Pipefy |
| **Mutation #2 — updateCardField** | 1min30s | Código + referência na doc Pipefy |
| **Testes + Endpoints** | 1min30s | `make test`, `make check`, curl nos 2 endpoints |
| **Encerramento** | 30s | Recap + diferencial (async, CI, idempotência) |

---

## 2. Stack e Decisões Técnicas

**Stack:** Python 3.10+ · FastAPI · SQLAlchemy 2.0 (async) · Pydantic v2 · Pytest · Ruff · Mypy

**Decisões principais:**
- Async runtime (`asyncpg` em prod, `aiosqlite` em testes) — I/O-bound (Pipefy HTTP calls)
- SQLite in-memory nos testes → CI roda sem Docker
- Pipefy mutations como dataclasses → type-safe, testável
- Idempotência via `IntegrityError` → `409 Conflict`
- Resposta padronizada: `{"success": true, "data": {...}}` / `{"success": false, "error": {...}}`
- TDD: test → fail → implement → pass

---

## 3. Arquitetura de Pastas

```
mundo-invest/
├── app/
│   ├── main.py                  # Entry-point, lifespan, router
│   ├── api/v1/clientes.py       # POST /clientes (thin router)
│   ├── schemas/
│   │   ├── cliente.py           # ClienteCreate, ClienteResponse
│   │   └── responses.py         # SuccessResponse, ErrorDetail
│   ├── errors/
│   │   ├── exceptions.py        # DomainError, IdempotencyConflictException
│   │   └── handlers.py          # domain_error_handler (404/409/400)
│   ├── models/
│   │   ├── database.py          # Async engine + session factory
│   │   └── cliente.py           # ClienteModel + ClienteRepository
│   ├── services/
│   │   ├── pipefy_graphql_client.py    # CreateCardMutation + client
│   │   └── client_ingestion_service.py # Orchestrator
│   └── core/
│       └── settings.py          # Pydantic Settings
├── tests/
│   ├── conftest.py              # Fixtures (SQLite, ASGITransport)
│   ├── test_clientes.py         # Repository + endpoint tests
│   ├── test_health.py           # Health check
│   ├── test_schemas.py          # Schemas, exceptions, error handler
│   └── test_services.py         # Pipefy mutation + service
├── PIPEFY.md                    # Documentação oficial Pipefy (referência)
├── .github/workflows/ci.yml     # CI: ruff → mypy → pytest
├── Makefile                     # Comandos: lint, typecheck, test, run
└── docker-compose.yml           # PostgreSQL 16 local
```

**Camadas (só setas para baixo):**
```
Router (thin) → Service → Repository + PipefyClient → Schemas → Error Handler
```

---

## 4. As Duas Mutations GraphQL do Pipefy

### 4.1 Mutation 1 — `createCard` (Fluxo 1: POST /clientes)

**Arquivo:** `app/services/pipefy_graphql_client.py:34-52`

```python
@dataclass
class CreateCardMutation:
    pipe_id: int
    title: str
    fields_attributes: list[dict[str, str]] = field(default_factory=list)

    def build(self) -> str:
        fields = ", ".join(
            f'{{field_id: "{f["field_id"]}", field_value: "{f["field_value"]}"}}'
            for f in self.fields_attributes
        )
        return (
            f"mutation {{ createCard(input: {{ pipe_id: {self.pipe_id}, "
            f'title: "{self.title}", fields_attributes: [{fields}] '
            f"}}) {{ card {{ id title }} }} }}"
        )
```

**Mutation gerada (exemplo real do log do servidor):**
```graphql
mutation { createCard(input: { pipe_id: 123, title: "João - Atualização",
  fields_attributes: [{field_id: "cliente_nome", field_value: "João"},
  {field_id: "cliente_email", field_value: "joao@test.com"},
  {field_id: "valor_patrimonio", field_value: "100000"}]
}) { card { id title } } }
```

**Como encontrei na documentação Pipefy:**
- Documento: `PIPEFY.md` (linhas 163-178) — seção **Card mutations**
- Exemplo oficial:
  ```graphql
  mutation {
    createCard(input: {
      pipe_id: 123,
      title: "New card",
      fields_attributes: [
        {field_id: "field_1", field_value: "Value 1"},
        {field_id: "field_2", field_value: "Value 2"}
      ]
    }) { card { title } }
  }
  ```
- Adaptei: `title` com `"{nome} - {tipo_solicitacao}"`, `fields_attributes` com os 3 campos mapeados

---

### 4.2 Mutation 2 — `updateCardField` (Fluxo 2: Webhook — ainda implementar)

**Referência na documentação:** `PIPEFY.md` (seção **updateCardField**)

```graphql
mutation {
  updateCardField(input: {
    card_id: 123,
    field_id: "field_1",
    new_value: "New field value"
  }) { card { id title } }
}
```

**Estrutura planejada (dataclass no mesmo padrão):**

```python
@dataclass
class UpdateCardFieldMutation:
    card_id: int
    field_id: str
    new_value: str

    def build(self) -> str:
        return (
            f"mutation {{ updateCardField(input: {{ "
            f'card_id: {self.card_id}, '
            f'field_id: "{self.field_id}", '
            f'new_value: "{self.new_value}" '
            f"}}) {{ card {{ id title }} }} }}"
        )
```

**Uso no Fluxo 2:**
- Evento: `POST /webhooks/pipefy/card-updated`
- Regra: se `valor_patrimonio >= 200000` → `prioridade_alta`, senão `prioridade_normal`
- Campos a atualizar no Pipefy: status (`"Processado"`) e prioridade calculada

---

## 5. Roteiro de Demonstração

### 5.1 Testes (terminal)

```bash
make check    # ruff + mypy (mostrar zero erros)
make test     # 22 passed (mostrar lista completa)
```

**22 testes:**
| Classe | Testes | O que cobre |
|--------|--------|-------------|
| `TestClienteRepository` | 3 | create, get_by_email (found + not found) |
| `TestClienteEndpoint` | 4 | 201 válido, 422 email inválido, 422 campo ausente, 422 patrimonio negativo |
| `TestHealth` | 1 | GET /health |
| `TestClienteCreateSchema` | 4 | payload válido, email inválido, campo ausente, patrimonio negativo |
| `TestClienteResponseSchema` | 1 | response com todos os campos |
| `TestResponseSchemas` | 2 | success + error response |
| `TestDomainExceptions` | 2 | EntityNotFound + IdempotencyConflict messages |
| `TestErrorHandler` | 2 | 404 + 409 via domain handler |
| `TestCreateCardMutation` | 1 | mutation string contém createCard, pipe_id, fields |
| `TestPipefyGraphQLClient` | 1 | mock response com card id + title |
| `TestClientIngestionService` | 1 | fluxo completo: persist + pipefy + response |

### 5.2 Endpoints (curl)

**POST /clientes — sucesso (201):**
```bash
curl -s -X POST http://localhost:8000/clientes/ \
  -H "Content-Type: application/json" \
  -d '{
    "cliente_nome": "João Silva",
    "cliente_email": "joao.silva@example.com",
    "tipo_solicitacao": "Atualização cadastral",
    "valor_patrimonio": 250000
  }'
```
Resposta: `{"success": true, "data": {"cliente_nome": "...", "pipefy_card_id": "1356383093", ...}}`

**POST /clientes — email duplicado (409):**
```bash
curl -s -X POST http://localhost:8000/clientes/ \
  -H "Content-Type: application/json" \
  -d '{"cliente_nome":"...","cliente_email":"joao.silva@example.com","tipo_solicitacao":"...","valor_patrimonio":1000}'
```
Resposta: `{"success": false, "error": {"message": "...already exists.", "code": "IDEMPOTENCY_CONFLICT"}}`

**POST /clientes — email inválido (422):**
```bash
curl -s -X POST http://localhost:8000/clientes/ \
  -H "Content-Type: application/json" \
  -d '{"cliente_nome":"João","cliente_email":"invalido","tipo_solicitacao":"...","valor_patrimonio":1000}'
```
Resposta: `{"detail": [{"type": "value_error", ...}]}`

### 5.3 Log do servidor (prova da mutation)

```
2026-05-26 INFO app.services.pipefy_graphql_client: Simulating Pipefy createCard mutation:
mutation { createCard(input: { pipe_id: 123, title: "João - Atualização",
  fields_attributes: [{field_id: "cliente_nome", field_value: "João"}, ...]
}) { card { id title } } }
2026-05-26 INFO app.services.client_ingestion_service: Pipefy card created: 1356383093
```

---

## 6. Frases-Chave para o Vídeo

> "Usei dataclasses do Python para representar as mutations do Pipefy porque isso me dá type safety em tempo de compilação — diferente de concatenar strings soltas no service layer."

> "A documentação oficial do Pipefy está num arquivo PIPEFY.md na raiz do projeto, pra facilitar a consulta. A mutation `createCard` eu encontrei na seção 'Card mutations'."

> "A resposta da API segue um padrão consistente: `success: true` com `data` para sucesso, ou `success: false` com `error.message` + `error.code` para erros."

> "Os testes rodam com SQLite in-memory — nenhuma dependência de Docker. O CI valida exatamente o mesmo cenário."

---

## 7. Checklist Pré-Gravação

- [ ] `make check` — ruff ✅, mypy ✅
- [ ] `make test` — 22 passed ✅
- [ ] Servidor rodando com `make run` (ou `DATABASE_URL=sqlite+aiosqlite:///dev.db make run`)
- [ ] Terminal limpo, fonte legível (tamanho 16+)
- [ ] Janelas organizadas: código (esquerda) + terminal (direita)
- [ ] PIPEFY.md aberto nas seções `createCard` e `updateCardField`
- [ ] Editor mostrando `app/services/pipefy_graphql_client.py` (a mutation)
- [ ] Curl commands copiados num bloco de notas (atalho)

---

## 8. Produção na AWS (para menção rápida, se sobrar tempo)

> "Em produção, o banco PostgreSQL subiria para RDS Aurora, o webhook seria um Lambda atrás do API Gateway, e a fila de eventos usaria SQS + DynamoDB para idempotência garantida."

---

## 9. Referências

- Documentação Pipefy: `PIPEFY.md` na raiz do repositório
- FastAPI: https://fastapi.tiangolo.com
- SQLAlchemy 2.0 async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Pydantic v2: https://docs.pydantic.dev/latest/
