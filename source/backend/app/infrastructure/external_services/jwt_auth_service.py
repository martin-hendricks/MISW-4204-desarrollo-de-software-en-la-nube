from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.shared.interfaces.authentication import AuthenticationInterface
from app.domain.entities.player import Player
from app.config.settings import settings

# Contexto para hash de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTAuthService(AuthenticationInterface):
    """Implementación de autenticación con JWT"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    async def hash_password(self, password: str) -> str:
        """Genera el hash de la contraseña"""
        return pwd_context.hash(password)
    
    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica si la contraseña coincide con el hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    async def create_access_token(self, data: dict) -> str:
        """Crea un token JWT de acceso"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    async def create_player_token(self, player_id: int) -> str:
        """Crea un token JWT específico para un jugador"""
        data = {"sub": str(player_id)}  # 'sub' es el estándar para el subject del token
        return await self.create_access_token(data)
    
    async def verify_token(self, token: str) -> Optional[dict]:
        """Verifica y decodifica un token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    async def authenticate_player(self, email: str, password: str) -> Optional[Player]:
        """Autentica un jugador con email y contraseña"""
        # Esta implementación necesitaría acceso al repositorio de jugadores
        # Por ahora retornamos None para evitar dependencias circulares
        # En una implementación real, se inyectaría el repositorio
        return None
