from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VideoUploadResponseDTO(BaseModel):
    """DTO de respuesta para subida de video"""
    message: str = "Video subido correctamente. Procesamiento en curso."
    task_id: str


class VideoListItemDTO(BaseModel):
    """DTO para item de lista de videos"""
    video_id: int
    title: str
    status: str  # uploaded, processed
    uploaded_at: datetime
    
    # Campos opcionales que solo están presentes si el video está procesado
    processed_at: Optional[datetime] = None
    processed_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class VideoDetailDTO(BaseModel):
    """DTO para detalle de video"""
    video_id: int
    title: str
    status: str
    votes: Optional[int] = 0
    original_url: Optional[str] = None
    processed_url: Optional[str] = None
    uploaded_at: Optional[datetime] = None


class VideoDeleteResponseDTO(BaseModel):
    """DTO de respuesta para eliminación de video"""
    message: str = "El video ha sido eliminado exitosamente."
    video_id: int


class VoteResponseDTO(BaseModel):
    """DTO de respuesta para votación"""
    message: str = "Voto registrado exitosamente."


class RankingItemDTO(BaseModel):
    """DTO para item de ranking"""
    position: int
    username: str
    city: str
    votes: int
