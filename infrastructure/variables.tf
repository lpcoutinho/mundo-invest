variable "aws_region" {
  description = "AWS Region para recursos"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "app_name" {
  description = "Nome da aplicação"
  type        = string
  default     = "mundo-invest"
}

variable "lambda_zip_file" {
  description = "Caminho para ZIP do Lambda"
  type        = string
  default     = "../lambda_deployment.zip"
}

variable "rds_instance_class" {
  description = "Classe da instância RDS"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "Armazenamento RDS (GB)"
  type        = number
  default     = 20
}

variable "database_username" {
  description = "Username do banco"
  type        = string
  sensitive   = true
}

variable "database_password" {
  description = "Password do banco"
  type        = string
  sensitive   = true
}

variable "PIPEFY_PIPE_ID" {
  description = "Pipefy Pipe ID"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID para recursos"
  type        = string
}

variable "private_subnet_ids" {
  description = "Subnet IDs privadas para Lambda e RDS"
  type        = list(string)
}

variable "database_subnet_ids" {
  description = "Subnet IDs para database subnet group"
  type        = list(string)
}
