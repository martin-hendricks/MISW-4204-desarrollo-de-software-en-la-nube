from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os

class JWTService:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        # Tiempo de expiración corto como se requiere (1 hora = 3600 segundos)
        self.access_token_expire_minutes = 60

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Crear token JWT"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str):
        """Verificar y decodificar token JWT"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise Exception("Token inválido")

    def get_expires_in_seconds(self) -> int:
        """Obtener tiempo de expiración en segundos"""
        return self.access_token_expire_minutes * 60

    def decode_token(self, token: str):
        """Decodificar token sin verificar (para depuración)"""
        try:
            return jwt.get_unverified_claims(token)
        except JWTError:
            return None