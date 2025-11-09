from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.video import Video


class VideoRepositoryInterface(ABC):
    """Interface para el repositorio de videos"""
    
    @abstractmethod
    async def create(self, video: Video) -> Video:
        """Crea un nuevo video"""
        pass
    
    @abstractmethod
    async def get_by_id(self, video_id: int) -> Optional[Video]:
        """Obtiene un video por ID"""
        pass
    
    @abstractmethod
    async def get_by_player(self, player_id: int) -> List[Video]:
        """Obtiene todos los videos de un jugador"""
        pass
    
    @abstractmethod
    async def get_public_videos(self, skip: int = 0, limit: int = 100) -> List[Video]:
        """Obtiene videos públicos para votación con paginación"""
        pass
    
    @abstractmethod
    async def update(self, video: Video) -> Video:
        """Actualiza un video"""
        pass
    
    @abstractmethod
    async def delete(self, video_id: int) -> bool:
        """Elimina un video"""
        pass
    
