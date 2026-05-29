# CloudWatch Alarms

# Alarme para erros 5XX do API Gateway
resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx" {
  alarm_name          = "${var.app_name}-${var.environment}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "5XXError"
  namespace          = "AWS/APIGateway"
  period             = "300"
  statistic          = "Sum"
  threshold          = "10"
  alarm_description  = "Alerta quando há muitos erros 5XX no API Gateway"
  alarm_actions      = [aws_sns_topic.alarms.arn]
  ok_actions         = [aws_sns_topic.alarms.arn]

  dimensions = {
    ApiId   = aws_api_gateway_rest_api.main.id
    Stage   = aws_api_gateway_stage.main.stage_name
  }

  tags = {
    Purpose = "API Gateway 5XX Errors Alarm"
  }
}

# Alarme para Lambda Errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.app_name}-${var.environment}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "Errors"
  namespace          = "AWS/Lambda"
  period             = "300"
  statistic          = "Sum"
  threshold          = "5"
  alarm_description  = "Alerta quando há erros na Lambda"
  alarm_actions      = [aws_sns_topic.alarms.arn]
  ok_actions         = [aws_sns_topic.alarms.arn]

  dimensions = {
    FunctionName = aws_lambda_function.app.function_name
  }

  tags = {
    Purpose = "Lambda Errors Alarm"
  }
}

# Alarme para Lambda Duration
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.app_name}-${var.environment}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "Duration"
  namespace          = "AWS/Lambda"
  period             = "300"
  statistic          = "Average"
  threshold          = "25000"  # 25 segundos
  alarm_description  = "Alerta quando Lambda demora muito"
  alarm_actions      = [aws_sns_topic.alarms.arn]
  ok_actions         = [aws_sns_topic.alarms.arn]

  dimensions = {
    FunctionName = aws_lambda_function.app.function_name
  }

  tags = {
    Purpose = "Lambda Duration Alarm"
  }
}

# SNS Topic para alarms
resource "aws_sns_topic" "alarms" {
  name = "${var.app_name}-${var.environment}-alarms"

  tags = {
    Purpose = "CloudWatch Alarms"
  }
}
