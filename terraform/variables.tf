variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_access_key_id" {
  description = "AWS Access Key ID"
  type        = string
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "AWS Secret Access Key"
  type        = string
  sensitive   = true
}

variable "aws_session_token" {
  description = "AWS Session Token (opcional, para AWS Academy)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "rds_password" {
  description = "Password for RDS PostgreSQL"
  type        = string
  default     = "root1234"
  sensitive   = true
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed for SSH access"
  type        = string
  default     = "0.0.0.0/0" # Cambiar a tu IP específica para mayor seguridad
}

