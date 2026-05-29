# OpenTofu Infrastructure - Mundo Invest Backend

Este diretório contém toda a infraestrutura AWS como código usando OpenTofu (fork open-source do Terraform).

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────┐
│         API Gateway REST                │  →  Expose endpoints
└──────────────┬──────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────┐
│      AWS Lambda (Python 3.12)           │
│      FastAPI + Mangum                    │
│      ZIP deployment (Layer approach)    │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┐
      ↓                 ↓
┌───────────┐    ┌──────────────┐
│ RDS       │    │ DynamoDB     │
│ PostgreSQL│    │ (State Lock) │
└───────────┘    └──────────────┘
                   Lock table:
                   tofu-lock-state
```

## 📁 Estrutura de Diretórios

```
infrastructure/
├── main.tf                 # Recursos principais (Lambda, API Gateway, RDS)
├── variables.tf            # Variáveis de input
├── outputs.tf              # Outputs da infraestrutura
├── provider.tf             # Configuração providers (AWS, random)
├── lambda/
│   ├── lambda.tf           # Recursos Lambda
│   ├── api_gateway.tf      # API Gateway REST
│   └── layers.tf           # Lambda Layers (dependencies)
├── database/
│   ├── rds.tf              # RDS PostgreSQL
│   ├── secrets_manager.tf  # Secrets (DATABASE_URL, etc)
│   └── security_group.tf   # SG para RDS
├── dynamodb/
│   └── state_lock.tf       # DynamoDB para state lock
├── cloudwatch/
│   ├── logs.tf             # CloudWatch Logs
│   └── alarms.tf           # CloudWatch Alarms
├── iam/
│   ├── lambda_role.tf      # IAM Role para Lambda
│   └── policies.tf         # IAM Policies
├── environments/
│   ├── dev.tfvars          # Variáveis dev
│   └── prod.tfvars         # Variáveis production
└── README.md               # Esta documentação
```

## 🚀 Uso

### Pré-requisitos

- OpenTofu instalado (>= 1.5.0)
- AWS CLI configurado
- Docker (para local com Floci)

### Local com Floci

1. **Iniciar Floci**:
```bash
docker compose up --build
```

2. **Testar OpenTofu local**:
```bash
docker compose --profile tofu run tofu init
docker compose --profile tofu run tofu plan
```

### Produção AWS

1. **Configurar backend S3** (primeira vez):
```bash
# Criar bucket S3
aws s3 mb s3://mundo-invest-terraform-state

# Criar tabela DynamoDB
aws dynamodb create-table \
    --table-name tofu-state-lock \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

2. **Inicializar OpenTofu**:
```bash
cd infrastructure
tofu init
```

3. **Planejar mudanças**:
```bash
tofu plan -var-file=environments/prod.tfvars \
    -var="database_username=admin" \
    -var="database_password=SecurePassword123"
```

4. **Aplicar mudanças**:
```bash
tofu apply -var-file=environments/prod.tfvars \
    -var="database_username=admin" \
    -var="database_password=SecurePassword123"
```

## 📦 Deploy Lambda ZIP

1. **Criar pacote**:
```bash
./scripts/deploy.sh
```

2. **Upload manual**:
```bash
aws s3 cp lambda_deployment.zip \
    s3://mundo-invest-lambda-deployment/prod/
```

3. **Atualizar Lambda**:
```bash
aws lambda update-function-code \
    --function-name mundo-invest-prod-app \
    --s3-bucket mundo-invest-lambda-deployment \
    --s3-key prod/lambda_deployment.zip
```

## 🔒 Segurança

- **Secrets Manager**: Todas as secrets são armazenadas no AWS Secrets Manager
- **IAM Roles**: Lambda usa roles com minimum privilege
- **RDS**: Banco não é publicamente acessível
- **VPC**: Lambda e RDS estão em subnets privadas

## 📊 Monitoramento

- **CloudWatch Logs**: Logs do Lambda e API Gateway
- **CloudWatch Alarms**: Alertas para erros 5XX e Lambda errors
- **Performance Insights**: Monitoramento do RDS

## 🧪 Testes Locais

1. **Subir Floci**:
```bash
docker compose up --build
```

2. **Testar endpoints**:
```bash
# Health check
curl http://localhost:8000/health

# Criar cliente
curl -X POST http://localhost:8000/v1/clientes \
    -H "Content-Type: application/json" \
    -d '{"nome": "João Silva", "email": "joao@example.com"}'
```

3. **Rodar testes**:
```bash
DATABASE_URL="postgresql+asyncpg://app:app123@localhost:5433/mundo_invest?sslmode=disable" \
pytest -v --cov=app
```

## 🔧 Variáveis Principais

| Variável | Descrição | Default |
|----------|-----------|---------|
| `aws_region` | AWS Region | `us-east-1` |
| `environment` | Ambiente (dev/prod) | `prod` |
| `app_name` | Nome da aplicação | `mundo-invest` |
| `rds_instance_class` | Classe RDS | `db.t3.micro` |
| `rds_allocated_storage` | Armazenamento RDS (GB) | `20` |
| `PIPEFY_PIPE_ID` | Pipefy Pipe ID | `307173097` |

## 📝 Outputs

Após o deploy, os seguintes outputs estarão disponíveis:

- `api_endpoint`: Endpoint do API Gateway
- `lambda_function_name`: Nome da função Lambda
- `rds_endpoint`: Endpoint do RDS
- `database_url_secret_arn`: ARN do secret DATABASE_URL

## 🔄 Workflow

1. **Desenvolvimento**: Use Floci localmente
2. **Testes**: Execute testes com Floci
3. **Deploy**: Use OpenTofu para criar infraestrutura AWS
4. **Monitoramento**: Configure CloudWatch alarms

## 🆘 Troubleshooting

### Erro: "LockID not found"
Execute:
```bash
aws dynamodb create-table \
    --table-name tofu-state-lock \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST
```

### Erro: "Lambda timeout"
Aumente `timeout` em `lambda/lambda.tf`

### Erro: "RDS connection failed"
Verifique security groups e VPC configuration

## 📚 Referências

- [OpenTofu Documentation](https://opentofu.org/)
- [AWS Lambda Python](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html)
- [Mangum Adapter](https://github.com/jordaneremieff/mangum)
- [FastAPI](https://fastapi.tiangolo.com/)

## 📄 Licença

Este código faz parte do projeto Mundo Invest Backend.
