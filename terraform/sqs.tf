# Dead Letter Queue
resource "aws_sqs_queue" "dlq" {
  name                      = "anb-nube-video-processing-dlq"
  message_retention_seconds = 1209600 # 14 días

  tags = {
    Name = "anb-nube-video-processing-dlq"
  }
}

# Cola principal
resource "aws_sqs_queue" "main" {
  name                      = "anb-nube-video-processing-queue"
  message_retention_seconds = 345600 # 4 días
  receive_wait_time_seconds = 20     # Long polling

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "anb-nube-video-processing-queue"
  }
}

