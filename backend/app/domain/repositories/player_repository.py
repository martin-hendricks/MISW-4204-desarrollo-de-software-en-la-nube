from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.player import Player
from app.domain.value_objects.email import Email


class PlayerRepositoryInterface(ABC):
    """Interface para el repositorio de jugadores"""
    
    @abstractmethod
    async def create(self, player: Player) -> Player:
        """Crea un nuevo jugador"""
        pass
    
    @abstractmethod
    async def get_by_id(self, player_id: int) -> Optional[Player]:
        """Obtiene un jugador por ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: Email) -> Optional[Player]:
        """Obtiene un jugador por email"""
        pass
    
    @abstractmethod
    async def update(self, player: Player) -> Player:
        """Actualiza un jugador"""
        pass
    
    @abstractmethod
    async def delete(self, player_id: int) -> bool:
        """Elimina un jugador"""
        pass
    
    @abstractmethod
    async def get_rankings(self, city: Optional[str] = None) -> List[Player]:
        """Obtiene el ranking de jugadores"""
        pass
