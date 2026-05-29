# IAM Policies customizadas para Lambda

# Policy para acessar Secrets Manager
data "aws_iam_policy_document" "secrets_manager_access" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ]
    resources = [
      aws_secretsmanager_secret.database_url.arn,
      aws_secretsmanager_secret.app_secrets.arn
    ]
  }
}

resource "aws_iam_role_policy" "secrets_manager_access" {
  name   = "secrets-manager-access"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.secrets_manager_access.json
}

# Policy para escrever logs no CloudWatch
data "aws_iam_policy_document" "cloudwatch_logs" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = [
      "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.app_name}-${var.environment}-app*"
    ]
  }
}

resource "aws_iam_role_policy" "cloudwatch_logs" {
  name   = "cloudwatch-logs"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.cloudwatch_logs.json
}

# Policy para acessar RDS (necessário para VPC)
data "aws_iam_policy_document" "rds_access" {
  statement {
    effect = "Allow"
    actions = [
      "rds:DescribeDBInstances",
      "rds:DescribeDBClusters"
    ]
    resources = [
      aws_db_instance.main.arn
    ]
  }
}

resource "aws_iam_role_policy" "rds_access" {
  name   = "rds-access"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.rds_access.json
}

# Dados para obter account ID
data "aws_caller_identity" "current" {}
