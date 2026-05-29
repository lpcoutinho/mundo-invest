# Main Terraform configuration
# Este arquivo pode ser usado para módulos ou recursos adicionais

# Data sources para obter informações da VPC existente
data "aws_vpc" "main" {
  id = var.vpc_id
}

# Data source para obter subnets privadas
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }

  tags = {
    Tier = "private"
  }
}

# Random suffix para evitar conflitos de nomes
resource "random_pet" "suffix" {
  length = 2
}

# S3 Bucket para Lambda deployment (opcional)
resource "aws_s3_bucket" "lambda_deployment" {
  bucket = "${var.app_name}-lambda-deployment-${random_pet.suffix.id}"

  tags = {
    Purpose = "Lambda Deployment Packages"
  }
}

resource "aws_s3_bucket_versioning" "lambda_deployment" {
  bucket = aws_s3_bucket.lambda_deployment.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lambda_deployment" {
  bucket = aws_s3_bucket.lambda_deployment.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket para state (alternativa ao backend hardcoded)
resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.app_name}-terraform-state"

  tags = {
    Purpose = "Terraform State Storage"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
