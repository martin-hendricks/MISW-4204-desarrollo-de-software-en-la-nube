from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.vote import Vote


class VoteRepositoryInterface(ABC):
    """Interface para el repositorio de votos"""
    
    @abstractmethod
    async def create(self, vote: Vote) -> Vote:
        """Crea un nuevo voto"""
        pass
    
    @abstractmethod
    async def get_by_id(self, vote_id: int) -> Optional[Vote]:
        """Obtiene un voto por ID"""
        pass
    
    @abstractmethod
    async def get_by_video(self, video_id: int) -> List[Vote]:
        """Obtiene todos los votos de un video"""
        pass
    
    @abstractmethod
    async def get_by_voter(self, player_id: int) -> List[Vote]:
        """Obtiene todos los votos de un votante"""
        pass
    
    @abstractmethod
    async def has_user_voted(self, video_id: int, player_id: int) -> bool:
        """Verifica si un usuario ya votó por un video"""
        pass
    
    @abstractmethod
    async def count_votes_for_video(self, video_id: int) -> int:
        """Cuenta el número de votos para un video"""
        pass
    
    @abstractmethod
    async def delete(self, vote_id: int) -> bool:
        """Elimina un voto"""
        pass
    
    @abstractmethod
    async def get_votes_by_videos(self, video_ids: List[int]) -> dict:
        """Obtiene el conteo de votos para múltiples videos"""
        pass
