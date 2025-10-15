from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class VideoStatus(Enum):
    """Estados posibles de un video"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


@dataclass
class Video:
    """Entidad de dominio para un video"""
    
    id: Optional[int]
    player_id: int
    title: str
    status: VideoStatus
    original_url: Optional[str] = None
    processed_url: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones después de la inicialización"""
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("El título del video no puede estar vacío")
      
        
        if self.player_id <= 0:
            raise ValueError("El ID del jugador debe ser válido")
    
    def start_processing(self) -> None:
        """Inicia el procesamiento del video"""
        if self.status != VideoStatus.UPLOADED:
            raise ValueError("Solo se pueden procesar videos que estén en estado 'uploaded'")
        self.status = VideoStatus.PROCESSING
    
    def mark_as_processed(self, processed_url: str) -> None:
        """Marca el video como procesado"""
        if self.status != VideoStatus.PROCESSING:
            raise ValueError("Solo se pueden marcar como procesados videos que estén siendo procesados")
        self.status = VideoStatus.PROCESSED
        self.processed_url = processed_url
    
    def mark_as_failed(self) -> None:
        """Marca el video como fallido"""
        self.status = VideoStatus.FAILED
    
    
    def can_be_deleted(self) -> bool:
        """Verifica si el video puede ser eliminado"""
        return self.status in [VideoStatus.UPLOADED, VideoStatus.PROCESSING]
    
    def is_public(self) -> bool:
        """Verifica si el video está disponible para votación pública"""
        return self.status == VideoStatus.PROCESSED
