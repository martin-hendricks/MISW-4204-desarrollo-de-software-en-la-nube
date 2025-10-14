"""
Modelos de base de datos (solo para referencia)
IMPORTANTE: El backend es responsable de crear estas tablas
El worker solo las usa para actualizar estados
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Video(Base):
    """
    Modelo de Video
    
    NOTA: Este modelo debe coincidir exactamente con el del backend
    El worker solo actualiza: status, processed_path, processed_at, error_message
    """
    __tablename__ = "videos"
    
    # Campos principales
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    
    # Estados: uploaded, processing, processed, failed
    status = Column(String(50), default="uploaded", nullable=False)
    
    # Rutas de archivos (filesystem local)
    original_path = Column(String(500), nullable=True)    # /app/uploads/original/123456.mp4
    processed_path = Column(String(500), nullable=True)   # /app/uploads/processed/123456.mp4
    processed_url = Column(String(500), nullable=True)    # URL pública (backend la genera)
    
    # Tracking de tareas Celery (para debugging)
    task_id = Column(String(255), nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Manejo de errores
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Metadata opcional
    original_duration = Column(Integer, nullable=True)    # Duración en segundos
    processed_duration = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Video(id={self.id}, title='{self.title}', status='{self.status}')>"

