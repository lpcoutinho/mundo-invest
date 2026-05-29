# Provider configuration
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Backend S3 + DynamoDB para state lock
  backend "s3" {
    bucket         = "mundo-invest-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "tofu-state-lock"
  }
}

# AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "mundo-invest"
      Environment = var.environment
      ManagedBy   = "OpenTofu"
    }
  }
}
