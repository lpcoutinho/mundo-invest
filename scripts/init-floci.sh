#!/bin/bash
# Script de inicialização do Floci

set -e

echo "🚀 Inicializando Floci..."

# Criar bucket S3 para state do OpenTofu
echo "📦 Criando S3 bucket para state..."
aws --endpoint-url=http://localhost:4566 s3 mb s3://mundo-invest-terraform-state || echo "Bucket já existe"

# Criar tabela DynamoDB para state lock
echo "🔒 Criando tabela DynamoDB para state lock..."
aws --endpoint-url=http://localhost:4566 dynamodb create-table \
    --table-name tofu-state-lock \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST || echo "Tabela já existe"

# Criar fila SQS para webhooks (opcional)
echo "📨 Criando fila SQS para webhooks..."
aws --endpoint-url=http://localhost:4566 sqs create-queue \
    --queue-name mundo-invest-webhooks || echo "Fila já existe"

echo "✅ Floci inicializado com sucesso!"
echo ""
echo "📊 Serviços disponíveis:"
echo "  - S3: http://localhost:4566"
echo "  - DynamoDB: http://localhost:4566"
echo "  - SQS: http://localhost:4566"
echo "  - Lambda: http://localhost:4566"
echo "  - API Gateway: http://localhost:4566"
echo "  - RDS PostgreSQL: localhost:5433"
