# DynamoDB Table para State Lock do OpenTofu

resource "aws_dynamodb_table" "tf_state_lock" {
  name           = "tofu-state-lock"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name       = "OpenTofu State Lock"
    Purpose    = "State Lock for OpenTofu"
    ManagedBy  = "OpenTofu"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }
}
