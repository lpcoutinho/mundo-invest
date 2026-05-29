# Security Group para RDS PostgreSQL

resource "aws_security_group" "rds" {
  name_prefix = "${var.app_name}-rds-"
  description = "Security Group para RDS PostgreSQL"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.app_name}-rds-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Allow ingress from Lambda security group
resource "aws_security_group_rule" "rds_ingress_from_lambda" {
  description              = "Allow PostgreSQL from Lambda"
  security_group_id        = aws_security_group.rds.id
  source_security_group_id = aws_security_group.lambda.id
  from_port               = 5432
  to_port                 = 5432
  protocol                = "tcp"
  type                    = "ingress"
}

# Egress rule (não necessário para RDS, mas boa prática)
resource "aws_security_group_rule" "rds_egress" {
  description       = "Allow all egress"
  security_group_id = aws_security_group.rds.id
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  type              = "egress"
  cidr_blocks       = ["0.0.0.0/0"]
}
