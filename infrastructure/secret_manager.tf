# Secrets Manager para DATABASE_URL e outras secrets

resource "aws_secretsmanager_secret" "database_url" {
  name = "${var.app_name}/${var.environment}/database-url"

  tags = {
    Purpose = "Database connection string"
  }
}

resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id = aws_secretsmanager_secret.database_url.id
  secret_string = jsonencode({
    DATABASE_URL = "postgresql+asyncpg://${var.database_username}:${var.database_password}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
  })
}

resource "aws_secretsmanager_secret" "app_secrets" {
  name = "${var.app_name}/${var.environment}/app-secrets"

  tags = {
    Purpose = "Application secrets"
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  secret_id = aws_secretsmanager_secret.app_secrets.id
  secret_string = jsonencode({
    PIPEFY_PIPE_ID = var.PIPEFY_PIPE_ID
    AWS_REGION     = var.aws_region
  })
}
