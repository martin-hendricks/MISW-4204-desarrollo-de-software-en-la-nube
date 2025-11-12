# S3 Bucket
resource "aws_s3_bucket" "videos" {
  bucket = "anb-videos-bucket-25"

  tags = {
    Name = "anb-videos-bucket-25"
  }
}

# Configuración de versionado (opcional, deshabilitado para free tier)
resource "aws_s3_bucket_versioning" "videos" {
  bucket = aws_s3_bucket.videos.id

  versioning_configuration {
    status = "Disabled"
  }
}

# Folder original/
resource "aws_s3_object" "original_folder" {
  bucket = aws_s3_bucket.videos.id
  key    = "original/"

  tags = {
    Name = "original-folder"
  }
}

# Folder processed/
resource "aws_s3_object" "processed_folder" {
  bucket = aws_s3_bucket.videos.id
  key    = "processed/"

  tags = {
    Name = "processed-folder"
  }
}

