"""
Modelos de base de datos - Coincide con database/init.sql

IMPORTANTE: Este modelo refleja EXACTAMENTE la tabla 'videos' en PostgreSQL
El worker solo puede leer/actualizar los campos que existen en la base de datos
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class VideoStatus(str, enum.Enum):
    """Estados posibles de un video según init.sql
    
    IMPORTANTE: Solo 'uploaded' y 'processed' existen en PostgreSQL.
    'failed' NO existe en el ENUM actual de la BD.
    """
    uploaded = "uploaded"
    processed = "processed"
    # NOTA: 'failed' NO existe en init.sql, comentado para evitar intentar usarlo
    # failed = "failed"


class Video(Base):
    """
    Modelo de Video - Coincide con database/init.sql
    
    Schema original:
        id SERIAL PRIMARY KEY,
        player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        status video_status NOT NULL DEFAULT 'uploaded',
        original_url VARCHAR(512),
        processed_url VARCHAR(512),
        uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP WITH TIME ZONE
    
    El worker puede:
    - ✅ Leer: id, player_id, title, status, original_url, processed_url
    - ✅ Actualizar: status, processed_url, processed_at
    
    NOTA: No hay campos para original_path, processed_path, task_id, error_message
          El worker construye las rutas por convención: /app/uploads/original/{id}.mp4
    """
    __tablename__ = "videos"
    
    # Campos según init.sql
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, nullable=False)  # Era user_id, ahora player_id
    title = Column(String(255), nullable=False)
    
    # Estado (ENUM en PostgreSQL: 'uploaded', 'processed')
    # IMPORTANTE: Usar Enum de SQLAlchemy para mapear correctamente el tipo ENUM de PostgreSQL
    status = Column(
        Enum(VideoStatus, name='video_status', create_type=False, values_callable=lambda x: [e.value for e in x]),
        default=VideoStatus.uploaded,
        nullable=False
    )
    
    # URLs públicas (lo que ve el usuario final)
    original_url = Column(String(512), nullable=True)
    processed_url = Column(String(512), nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.now(), nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Video(id={self.id}, title='{self.title}', status='{self.status}')>"

