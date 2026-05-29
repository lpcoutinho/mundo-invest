output "api_endpoint" {
  description = "API Gateway Endpoint URL"
  value       = "${aws_api_gateway_rest_api.main.execution_arn}/${aws_api_gateway_stage.main.stage_name}"
}

output "api_invoke_url" {
  description = "API Gateway Invoke URL"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "lambda_function_name" {
  description = "Lambda Function Name"
  value       = aws_lambda_function.app.function_name
}

output "lambda_function_arn" {
  description = "Lambda Function ARN"
  value       = aws_lambda_function.app.arn
}

output "rds_endpoint" {
  description = "RDS Endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "database_url_secret_arn" {
  description = "Secret ARN for DATABASE_URL"
  value       = aws_secretsmanager_secret.database_url.arn
}

output "app_secrets_secret_arn" {
  description = "Secret ARN for app secrets"
  value       = aws_secretsmanager_secret.app_secrets.arn
}

output "dynamodb_state_lock_table" {
  description = "DynamoDB Table para State Lock"
  value       = aws_dynamodb_table.tf_state_lock.name
}
