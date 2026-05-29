"""Lambda handler para AWS Lambda usando Mangum.

Este adapter permite que a aplicação FastAPI rode no AWS Lambda
através do Mangum, que traduz eventos do Lambda para ASGI.
"""
import os
from typing import Any, Dict, cast
import boto3
import json
from mangum import Mangum
from app.main import app

# Cliente Secrets Manager
secrets_client = boto3.client('secretsmanager')


def get_secret(secret_arn: str) -> dict:
    """Busca secret do AWS Secrets Manager.

    Args:
        secret_arn: ARN do secret no Secrets Manager

    Returns:
        Dict com os valores do secret
    """
    try:
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_string = response['SecretString']
        parsed: dict = json.loads(secret_string)
        return parsed
    except Exception as e:
        print(f"Erro ao buscar secret {secret_arn}: {e}")
        return {}


def load_secrets():
    """Carrega secrets do AWS Secrets Manager e seta environment variables.

    Esta função é executada no handler para garantir que as secrets
    sejam carregadas em tempo de execução do Lambda, com credentials
    apropriadas do IAM Role.
    """
    # Buscar DATABASE_URL_SECRET_ARN se definido
    database_url_arn = os.environ.get('DATABASE_URL_SECRET_ARN')
    if database_url_arn:
        db_secret = get_secret(database_url_arn)
        if 'DATABASE_URL' in db_secret:
            os.environ['DATABASE_URL'] = db_secret['DATABASE_URL']

    # Buscar APP_SECRETS_SECRET_ARN se definido
    app_secrets_arn = os.environ.get('APP_SECRETS_SECRET_ARN')
    if app_secrets_arn:
        app_secret = get_secret(app_secrets_arn)
        for key, value in app_secret.items():
            os.environ[key] = str(value)


# Handler Lambda
def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handler para AWS Lambda.

    Args:
        event: Evento do Lambda (API Gateway, SQS, etc)
        context: Contexto de execução do Lambda

    Returns:
        Resposta da API FastAPI processada pelo Mangum
    """
    # Carregar secrets em tempo de execução
    load_secrets()

    # Criar adapter Mangum
    mangum_handler = Mangum(app, lifespan="off")

    # Executar handler e forçar o type casting para o MyPy
    response = mangum_handler(event, context)
    return cast(Dict[str, Any], response)


# Exportar handler
lambda_handler = handler
