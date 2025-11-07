"""Configuración de la aplicación"""

import os
from enum import Enum


class FileStorageType(Enum):
    """Tipos de almacenamiento de archivos disponibles"""
    LOCAL = "local"
    S3 = "s3"


class Settings:
    """Configuración de la aplicación"""
    
    # Base de datos
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://user:password@localhost:5432/fileprocessing"
    )
    
    # Message Broker (Redis o SQS)
    USE_SQS: bool = os.getenv("USE_SQS", "false").lower() == "true"

    # Redis (broker actual)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # AWS SQS (broker alternativo para autoscaling)
    SQS_QUEUE_URL: str = os.getenv("SQS_QUEUE_URL", "")
    SQS_DLQ_URL: str = os.getenv("SQS_DLQ_URL", "")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Servidor
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"
    
    # Almacenamiento de archivos
    FILE_STORAGE_TYPE: FileStorageType = FileStorageType(
        os.getenv("FILE_STORAGE_TYPE", "local")
    )
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/app/uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "104857600"))  # 100MB
    BASE_PATH: str = os.getenv("BASE_PATH", "http://localhost:80/api/videos")
    
    # AWS S3 (si se usa)
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_SESSION_TOKEN: str = os.getenv("AWS_SESSION_TOKEN", "")  # Para AWS Academy
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "")
    
    
    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")


# Instancia global de configuración
settings = Settings()
