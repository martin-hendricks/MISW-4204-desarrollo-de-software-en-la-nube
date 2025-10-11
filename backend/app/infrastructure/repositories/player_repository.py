from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.player import Player
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password
from app.domain.repositories.player_repository import PlayerRepositoryInterface
from app.infrastructure.database.database import get_db
from app.infrastructure.database.models import PlayerModel
from datetime import datetime


class PlayerRepository(PlayerRepositoryInterface):
    """Implementación del repositorio de jugadores usando PostgreSQL"""
    
    def __init__(self, db: Session = None):
        self._db = db
    
    def _get_db(self) -> Session:
        """Obtiene la sesión de base de datos"""
        if self._db:
            return self._db
        return next(get_db())
    
    def _to_domain(self, model: PlayerModel) -> Player:
        """Convierte un modelo SQLAlchemy a entidad de dominio"""
        return Player(
            id=model.id,
            first_name=model.first_name,
            last_name=model.last_name,
            email=Email(model.email),
            password=Password(value="dummy", hashed_value=model.password_hash),
            city=model.city,
            country=model.country,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_model(self, player: Player) -> PlayerModel:
        """Convierte una entidad de dominio a modelo SQLAlchemy"""
        model_data = {
            "first_name": player.first_name,
            "last_name": player.last_name,
            "email": player.email.value,
            "password_hash": player.password.hashed_value,
            "city": player.city,
            "country": player.country,
            "is_active": player.is_active
        }
        
        # Solo incluir id si existe (para updates)
        if player.id is not None:
            model_data["id"] = player.id
        
        # Para nuevos registros, incluir timestamps actuales
        if player.id is None:  # Nuevo registro
            from datetime import datetime
            now = datetime.now()
            model_data["created_at"] = now
            model_data["updated_at"] = now
        else:  # Actualización
            if player.created_at is not None:
                model_data["created_at"] = player.created_at
            if player.updated_at is not None:
                model_data["updated_at"] = player.updated_at
        
        return PlayerModel(**model_data)
    
    async def create(self, player: Player) -> Player:
        """Crea un nuevo jugador"""
        db = self._get_db()
        try:
            model = self._to_model(player)
            db.add(model)
            db.commit()
            db.refresh(model)
            return self._to_domain(model)
        finally:
            if not self._db:
                db.close()
    
    async def get_by_id(self, player_id: int) -> Optional[Player]:
        """Obtiene un jugador por ID"""
        db = self._get_db()
        try:
            model = db.query(PlayerModel).filter(PlayerModel.id == player_id).first()
            return self._to_domain(model) if model else None
        finally:
            if not self._db:
                db.close()
    
    async def get_by_email(self, email: Email) -> Optional[Player]:
        """Obtiene un jugador por email"""
        db = self._get_db()
        try:
            model = db.query(PlayerModel).filter(PlayerModel.email == email.value).first()
            return self._to_domain(model) if model else None
        finally:
            if not self._db:
                db.close()
    
    async def update(self, player: Player) -> Player:
        """Actualiza un jugador"""
        db = self._get_db()
        try:
            model = db.query(PlayerModel).filter(PlayerModel.id == player.id).first()
            if model:
                model.first_name = player.first_name
                model.last_name = player.last_name
                model.city = player.city
                model.country = player.country
                model.is_active = player.is_active
                model.updated_at = datetime.now()
                db.commit()
                db.refresh(model)
                return self._to_domain(model)
            return player
        finally:
            if not self._db:
                db.close()
    
    async def delete(self, player_id: int) -> bool:
        """Elimina un jugador"""
        db = self._get_db()
        try:
            model = db.query(PlayerModel).filter(PlayerModel.id == player_id).first()
            if model:
                db.delete(model)
                db.commit()
                return True
            return False
        finally:
            if not self._db:
                db.close()
    
    async def get_rankings(self, city: Optional[str] = None) -> List[Player]:
        """Obtiene el ranking de jugadores"""
        db = self._get_db()
        try:
            query = db.query(PlayerModel)
            if city:
                query = query.filter(PlayerModel.city == city)
            # TODO: Ordenar por votos totales
            models = query.all()
            return [self._to_domain(model) for model in models]
        finally:
            if not self._db:
                db.close()
