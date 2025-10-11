from passlib.context import CryptContext
from models.user import UserCreate, UserResponse
from repositories.user_repository import UserRepository
from sqlalchemy.orm import Session
from typing import Optional
import os

class AuthService:
    """
    Servicio de autenticación con acceso a base de datos real
    """
    def __init__(self, db_session: Session):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.user_repo = UserRepository(db_session)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hashear contraseña"""
        return self.pwd_context.hash(password)

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """Obtener usuario por email"""
        db_user = self.user_repo.get_user_by_email(email)
        if db_user:
            return self.user_repo.to_user_response(db_user)
        return None

    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """Obtener usuario por ID"""
        db_user = self.user_repo.get_user_by_id(user_id)
        if db_user:
            return self.user_repo.to_user_response(db_user)
        return None

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Crear nuevo usuario"""
        # Verificar si el usuario ya existe
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValueError("El usuario ya existe")

        # Hashear contraseña y crear usuario
        hashed_password = self.get_password_hash(user_data.password1)
        db_user = self.user_repo.create_user(user_data, hashed_password)
        
        return self.user_repo.to_user_response(db_user)

    async def authenticate_user(self, email: str, password: str) -> Optional[UserResponse]:
        """Autenticar usuario"""
        db_user = self.user_repo.get_user_by_email(email)
        if not db_user:
            return None
        
        if not self.verify_password(password, db_user.hashed_password):
            return None
        
        return self.user_repo.to_user_response(db_user)