# RDS PostgreSQL Instance

resource "aws_db_instance" "main" {
  identifier           = "${var.app_name}-${var.environment}-db"
  engine               = "postgres"
  engine_version       = "16.3"
  instance_class       = var.rds_instance_class
  allocated_storage    = var.rds_allocated_storage
  storage_type         = "gp3"
  storage_encrypted    = true

  db_name  = "mundo_invest"
  username = var.database_username
  password = var.database_password

  # VPC
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Monitoring
  monitoring_interval         = 60
  performance_insights_enabled = true

  # Backup
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  # Logs
  enabled_cloudwatch_logs_exports = ["postgresql"]

  # Tags
  tags = {
    Name = "${var.app_name}-${var.environment}-rds"
  }

  # Lifecycle
  lifecycle {
    create_before_destroy = true
    ignore_changes        = [password]
  }
}

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-subnet-group"
  subnet_ids = var.database_subnet_ids

  tags = {
    Name = "${var.app_name}-subnet-group"
  }
}
