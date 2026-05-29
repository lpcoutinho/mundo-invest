# API Gateway REST API

resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.app_name}-${var.environment}-api"
  description = "Mundo Invest Backend API"
  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "${var.app_name}-api"
  }
}

# API Gateway Resource (root)
resource "aws_api_gateway_resource" "root" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "v1"
}

# API Gateway Resource (clientes)
resource "aws_api_gateway_resource" "clientes" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.root.id
  path_part   = "clientes"
}

# POST /clientes
resource "aws_api_gateway_method" "clientes_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.clientes.id
  http_method   = "POST"
  authorization = "NONE"
}

# Lambda Integration
resource "aws_api_gateway_integration" "clientes_post" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.clientes.id
  http_method = aws_api_gateway_method.clientes_post.http_method
  type        = "AWS_PROXY"
  integration_http_method = "POST"

  uri = aws_lambda_function.app.invoke_arn
}

# API Gateway Resource (webhooks)
resource "aws_api_gateway_resource" "webhooks" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.root.id
  path_part   = "webhooks"
}

resource "aws_api_gateway_resource" "webhooks_pipefy" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.webhooks.id
  path_part   = "pipefy"
}

resource "aws_api_gateway_resource" "webhooks_card_updated" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.webhooks_pipefy.id
  path_part   = "card-updated"
}

# POST /webhooks/pipefy/card-updated
resource "aws_api_gateway_method" "webhook_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.webhooks_card_updated.id
  http_method   = "POST"
  authorization = "NONE"
}

# Lambda Integration
resource "aws_api_gateway_integration" "webhook_post" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.webhooks_card_updated.id
  http_method = aws_api_gateway_method.webhook_post.http_method
  type        = "AWS_PROXY"
  integration_http_method = "POST"

  uri = aws_lambda_function.app.invoke_arn
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.clientes.id,
      aws_api_gateway_resource.webhooks_card_updated.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment

  tags = {
    Environment = var.environment
  }
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.app.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.main.execution_arn}/*/*/*"
}
