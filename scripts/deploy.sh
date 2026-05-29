#!/bin/bash
# Deploy Lambda ZIP para AWS

set -e

APP_NAME="mundo-invest"
ENVIRONMENT=${1:-prod}
ZIP_FILE="lambda_deployment.zip"

echo "📦 Creating Lambda deployment package..."

# Criar diretório temporário para o package
mkdir -p package

# Instalar dependências no package
pip install --target package -r requirements.txt

# Copiar código para o package
cp -r app package/

# Criar ZIP
cd package
zip -r ../${ZIP_FILE} .
cd ..

# Limpar
rm -rf package

echo "✅ Lambda package created: ${ZIP_FILE}"
echo "📤 Size: $(du -h ${ZIP_FILE} | cut -f1)"

# Upload para S3 (opcional)
# aws s3 cp ${ZIP_FILE} s3://${APP_NAME}-lambda-deployment/${ENVIRONMENT}/
