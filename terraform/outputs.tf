output "elb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.main.dns_name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "rds_address" {
  description = "RDS PostgreSQL address (without port)"
  value       = aws_db_instance.main.address
}

output "rds_port" {
  description = "RDS PostgreSQL port"
  value       = aws_db_instance.main.port
}

output "sqs_main_queue_url" {
  description = "URL of the main SQS queue"
  value       = aws_sqs_queue.main.url
}

output "sqs_dlq_url" {
  description = "URL of the Dead Letter Queue"
  value       = aws_sqs_queue.dlq.url
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.videos.id
}

output "performance_instance_id" {
  description = "Instance ID of the performance instance"
  value       = aws_instance.performance.id
}

output "performance_instance_public_ip" {
  description = "Public IP of the performance instance"
  value       = aws_instance.performance.public_ip
}

output "worker_instance_id" {
  description = "Instance ID of the worker instance"
  value       = aws_instance.worker.id
}

output "worker_instance_public_ip" {
  description = "Public IP of the worker instance"
  value       = aws_instance.worker.public_ip
}

output "key_pair_name" {
  description = "Name of the key pair created"
  value       = aws_key_pair.clavemac.key_name
}

output "private_key_path" {
  description = "Path to the private key file"
  value       = local_file.clavemac_private_key.filename
  sensitive   = true
}

