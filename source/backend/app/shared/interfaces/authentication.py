from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.player import Player


class AuthenticationInterface(ABC):
    """Interface para la autenticación"""
    
    @abstractmethod
    async def hash_password(self, password: str) -> str:
        """Genera el hash de una contraseña"""
        pass
    
    @abstractmethod
    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica si una contraseña coincide con su hash"""
        pass
    
    @abstractmethod
    async def create_access_token(self, data: dict) -> str:
        """Crea un token JWT de acceso"""
        pass
    
    @abstractmethod
    async def verify_token(self, token: str) -> Optional[dict]:
        """Verifica y decodifica un token JWT"""
        pass
    
    @abstractmethod
    async def authenticate_player(self, email: str, password: str) -> Optional[Player]:
        """Autentica un jugador con email y contraseña"""
        pass
