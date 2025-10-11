"""
Repositorio para operaciones de usuarios en base de datos
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.db_models import Player
from models.user import UserCreate, UserResponse
from typing import Optional
from datetime import datetime

class UserRepository:
    """
    Repositorio para manejar operaciones CRUD de usuarios
    Separa la lógica de acceso a datos del servicio de negocio
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_user_by_email(self, email: str) -> Optional[Player]:
        """
        Obtener usuario por email desde la base de datos
        
        Args:
            email: Email del usuario a buscar
            
        Returns:
            Player o None si no existe
        """
        return self.db.query(Player).filter(Player.email == email).first()

    def get_user_by_id(self, user_id: int) -> Optional[Player]:
        """
        Obtener usuario por ID desde la base de datos
        
        Args:
            user_id: ID del usuario a buscar
            
        Returns:
            Player o None si no existe
        """
        return self.db.query(Player).filter(Player.id == user_id).first()

    def create_user(self, user_data: UserCreate, hashed_password: str) -> Player:
        """
        Crear nuevo usuario en la base de datos
        
        Args:
            user_data: Datos del usuario del modelo Pydantic
            hashed_password: Contraseña ya hasheada
            
        Returns:
            Player creado
            
        Raises:
            ValueError: Si el email ya existe
        """
        # Crear instancia del modelo SQLAlchemy
        # Los datos ya vienen normalizados desde el modelo Pydantic UserCreate
        db_user = Player(
            email=user_data.email,  # Ya viene normalizado por EmailStr
            first_name=user_data.first_name,  # Ya viene con .strip().title() por el validator
            last_name=user_data.last_name,    # Ya viene con .strip().title() por el validator
            city=user_data.city,              # Ya viene con .strip().title() por el validator
            country=user_data.country,        # Ya viene con .strip().title() por el validator
            password_hash=hashed_password,
            created_at=datetime.now()
        )
        
        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)  # Para obtener el ID generado
            return db_user
        except IntegrityError:
            self.db.rollback()
            raise ValueError("El usuario ya existe")

    def update_user(self, user_id: int, **update_data) -> Optional[Player]:
        """
        Actualizar usuario en la base de datos
        
        Args:
            user_id: ID del usuario a actualizar
            **update_data: Campos a actualizar
            
        Returns:
            Player actualizado o None si no existe
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None
            
        # Actualizar solo los campos proporcionados
        for field, value in update_data.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)
        
        # Actualizar timestamp
        user.updated_at = datetime.utcnow()
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise ValueError("Error al actualizar usuario")

    def deactivate_user(self, user_id: int) -> bool:
        """
        Desactivar usuario (soft delete)
        
        Args:
            user_id: ID del usuario a desactivar
            
        Returns:
            True si se desactivó exitosamente
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False
            
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True

    def delete_user(self, user_id: int) -> bool:
        """
        Eliminar usuario permanentemente de la base de datos
        
        Args:
            user_id: ID del usuario a eliminar
            
        Returns:
            True si se eliminó exitosamente
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False
            
        self.db.delete(user)
        self.db.commit()
        return True

    def count_users(self) -> int:
        """
        Contar total de usuarios activos
        
        Returns:
            Número de usuarios activos
        """
        return self.db.query(Player).filter(Player.is_active == True).count()

    def to_user_response(self, db_user: Player) -> UserResponse:
        """
        Convertir modelo de base de datos a modelo de respuesta Pydantic
        
        Args:
            db_user: Usuario desde la base de datos
            
        Returns:
            UserResponse para la API
        """
        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            city=db_user.city,
            country=db_user.country,
            created_at=db_user.created_at,
        )