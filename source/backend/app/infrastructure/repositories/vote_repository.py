from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.domain.entities.vote import Vote
from app.domain.repositories.vote_repository import VoteRepositoryInterface
from app.infrastructure.database.database import get_db
from app.infrastructure.database.models import VoteModel
from datetime import datetime


class VoteRepository(VoteRepositoryInterface):
    """Implementación del repositorio de votos usando PostgreSQL"""
    
    def __init__(self, db: Session = None):
        self._db = db
    
    def _get_db(self) -> Session:
        """Obtiene la sesión de base de datos"""
        if self._db:
            return self._db
        return next(get_db())
    
    def _to_domain(self, model: VoteModel) -> Vote:
        """Convierte un modelo SQLAlchemy a entidad de dominio"""
        return Vote(
            id=model.id,
            video_id=model.video_id,
            player_id=model.player_id,
            created_at=model.created_at
        )
    
    def _to_model(self, vote: Vote) -> VoteModel:
        """Convierte una entidad de dominio a modelo SQLAlchemy"""
        model_data = {
            "video_id": vote.video_id,
            "player_id": vote.player_id
        }
        
        # Solo incluir id si existe (para updates)
        if vote.id is not None:
            model_data["id"] = vote.id
        
        # Para nuevos registros, incluir timestamps actuales
        if vote.id is None:  # Nuevo registro
            now = datetime.now()
            model_data["created_at"] = now
        else:  # Actualización
            if vote.created_at is not None:
                model_data["created_at"] = vote.created_at
        
        return VoteModel(**model_data)
    
    async def create(self, vote: Vote) -> Vote:
        """Crea un nuevo voto"""
        db = self._get_db()
        try:
            model = self._to_model(vote)
            db.add(model)
            db.commit()
            db.refresh(model)
            return self._to_domain(model)
        finally:
            if not self._db:
                db.close()
    
    async def get_by_id(self, vote_id: int) -> Optional[Vote]:
        """Obtiene un voto por ID"""
        db = self._get_db()
        try:
            model = db.query(VoteModel).filter(VoteModel.id == vote_id).first()
            return self._to_domain(model) if model else None
        finally:
            if not self._db:
                db.close()
    
    async def get_by_video(self, video_id: int) -> List[Vote]:
        """Obtiene todos los votos de un video"""
        db = self._get_db()
        try:
            models = db.query(VoteModel).filter(VoteModel.video_id == video_id).all()
            return [self._to_domain(model) for model in models]
        finally:
            if not self._db:
                db.close()
    
    async def get_by_voter(self, player_id: int) -> List[Vote]:
        """Obtiene todos los votos de un votante"""
        db = self._get_db()
        try:
            models = db.query(VoteModel).filter(VoteModel.player_id == player_id).all()
            return [self._to_domain(model) for model in models]
        finally:
            if not self._db:
                db.close()
    
    async def has_user_voted(self, video_id: int, player_id: int) -> bool:
        """Verifica si un usuario ya votó por un video"""
        db = self._get_db()
        try:
            vote = db.query(VoteModel).filter(
                VoteModel.video_id == video_id,
                VoteModel.player_id == player_id
            ).first()
            return vote is not None
        finally:
            if not self._db:
                db.close()
    
    async def count_votes_for_video(self, video_id: int) -> int:
        """Cuenta el número de votos para un video"""
        db = self._get_db()
        try:
            count = db.query(VoteModel).filter(VoteModel.video_id == video_id).count()
            return count
        finally:
            if not self._db:
                db.close()
    
    async def delete(self, vote_id: int) -> bool:
        """Elimina un voto"""
        db = self._get_db()
        try:
            model = db.query(VoteModel).filter(VoteModel.id == vote_id).first()
            if model:
                db.delete(model)
                db.commit()
                return True
            return False
        finally:
            if not self._db:
                db.close()
    
    async def get_votes_by_videos(self, video_ids: List[int]) -> Dict[int, int]:
        """Obtiene el conteo de votos para múltiples videos"""
        db = self._get_db()
        try:
            from sqlalchemy import func
            results = db.query(
                VoteModel.video_id,
                func.count(VoteModel.id).label('vote_count')
            ).filter(
                VoteModel.video_id.in_(video_ids)
            ).group_by(VoteModel.video_id).all()
            
            # Crear diccionario con conteos
            vote_counts = {video_id: 0 for video_id in video_ids}
            for result in results:
                vote_counts[result.video_id] = result.vote_count
            
            return vote_counts
        finally:
            if not self._db:
                db.close()
