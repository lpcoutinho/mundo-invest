# Lambda Function (FastAPI + Mangum)

# Lambda Security Group
resource "aws_security_group" "lambda" {
  name_prefix = "${var.app_name}-lambda-"
  description = "Security Group para Lambda Function"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.app_name}-lambda-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Egress rule para Lambda
resource "aws_security_group_rule" "lambda_egress" {
  description       = "Allow all egress"
  security_group_id = aws_security_group.lambda.id
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  type              = "egress"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_lambda_function" "app" {
  function_name    = "${var.app_name}-${var.environment}-app"
  description     = "Mundo Invest Backend - FastAPI + Mangum"
  runtime         = "python3.12"
  handler         = "app.lambda_handler.handler"
  role            = aws_iam_role.lambda.arn
  timeout         = 30
  memory_size     = 512

  # Code (ZIP deployment)
  filename         = var.lambda_zip_file
  source_code_hash = filebase64sha256(var.lambda_zip_file)

  # Environment variables
  environment {
    variables = {
      DEBUG                     = "false"
      ENV                       = var.environment
      PIPEFY_PIPE_ID            = var.PIPEFY_PIPE_ID
      DATABASE_URL_SECRET_ARN   = aws_secretsmanager_secret.database_url.arn
      APP_SECRETS_SECRET_ARN    = aws_secretsmanager_secret.app_secrets.arn
    }
  }

  # VPC config (para acessar RDS)
  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  # Logging
  logging_config {
    log_format = "JSON"
  }

  # Tags
  tags = {
    Name = "${var.app_name}-lambda"
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic,
    aws_iam_role_policy_attachment.lambda_vpc,
    aws_cloudwatch_log_group.lambda,
  ]
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.app_name}-${var.environment}-app"
  retention_in_days = 7

  tags = {
    Name = "${var.app_name}-lambda-logs"
  }
}
