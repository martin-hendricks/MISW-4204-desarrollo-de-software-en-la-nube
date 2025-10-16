from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.entities.video import Video, VideoStatus
from app.domain.repositories.video_repository import VideoRepositoryInterface
from app.infrastructure.database.database import get_db
from app.infrastructure.database.models import VideoModel, VideoStatusEnum
from datetime import datetime


class VideoRepository(VideoRepositoryInterface):
    """Implementación del repositorio de videos usando PostgreSQL"""
    
    def __init__(self, db: Session = None):
        self._db = db
    
    def _get_db(self) -> Session:
        """Obtiene la sesión de base de datos"""
        if self._db:
            return self._db
        return next(get_db())
    
    def _to_domain(self, model: VideoModel) -> Video:
        """Convierte un modelo SQLAlchemy a entidad de dominio"""
        # Convertir el string de la BD al enum de dominio
        status_map = {
            "uploaded": VideoStatus.UPLOADED,
            "processed": VideoStatus.PROCESSED,
        }
        
        # Debug: imprimir el status que viene de la BD
        mapped_status = status_map.get(model.status, VideoStatus.UPLOADED)
        
        return Video(
            id=model.id,
            player_id=model.player_id,
            title=model.title,
            status=mapped_status,
            original_url=model.original_url,
            processed_url=model.processed_url,
            uploaded_at=model.uploaded_at,
            processed_at=model.processed_at
        )
    
    def _to_model(self, video: Video) -> VideoModel:
        """Convierte una entidad de dominio a modelo SQLAlchemy"""
        # Convertir el enum de dominio al string para la BD
        status_map = {
            VideoStatus.UPLOADED: "uploaded",
            VideoStatus.PROCESSED: "processed",
        }
        
        model_data = {
            "player_id": video.player_id,
            "title": video.title,
            "status": status_map.get(video.status, "uploaded"),
            "original_url": video.original_url,
            "processed_url": video.processed_url,
            "processed_at": video.processed_at
        }
        
        # Solo incluir id si existe (para updates)
        if video.id is not None:
            model_data["id"] = video.id
        
        # Para nuevos registros, incluir timestamps actuales
        if video.id is None:  # Nuevo registro
            from datetime import datetime
            now = datetime.now()
            model_data["uploaded_at"] = now
        else:  # Actualización
            if video.uploaded_at is not None:
                model_data["uploaded_at"] = video.uploaded_at
        
        return VideoModel(**model_data)
    
    async def create(self, video: Video) -> Video:
        """Crea un nuevo video"""
        db = self._get_db()
        try:
            model = self._to_model(video)
            db.add(model)
            db.commit()
            db.refresh(model)
            return self._to_domain(model)
        finally:
            if not self._db:
                db.close()
    
    async def get_by_id(self, video_id: int) -> Optional[Video]:
        """Obtiene un video por ID"""
        db = self._get_db()
        try:
            model = db.query(VideoModel).filter(VideoModel.id == video_id).first()
            return self._to_domain(model) if model else None
        finally:
            if not self._db:
                db.close()
    
    async def get_by_player(self, player_id: int) -> List[Video]:
        """Obtiene todos los videos de un jugador"""
        db = self._get_db()
        try:
            models = db.query(VideoModel).filter(VideoModel.player_id == player_id).all()
            return [self._to_domain(model) for model in models]
        finally:
            if not self._db:
                db.close()
    
    async def get_public_videos(self) -> List[Video]:
        """Obtiene todos los videos públicos para votación"""
        db = self._get_db()
        try:
            models = db.query(VideoModel).filter(
                VideoModel.status == 'processed'
            ).all()
            return [self._to_domain(model) for model in models]
        finally:
            if not self._db:
                db.close()
    
    async def update(self, video: Video) -> Video:
        """Actualiza un video"""
        db = self._get_db()
        try:
            model = db.query(VideoModel).filter(VideoModel.id == video.id).first()
            if model:
                # Convertir el enum de dominio al enum de SQLAlchemy
                status_map = {
                    VideoStatus.UPLOADED: VideoStatusEnum.UPLOADED,
                    VideoStatus.PROCESSED: VideoStatusEnum.PROCESSED,
                }
                
                model.title = video.title
                model.status = status_map.get(video.status, VideoStatusEnum.UPLOADED)
                model.original_url = video.original_url
                model.processed_url = video.processed_url
                model.processed_at = video.processed_at
                db.commit()
                db.refresh(model)
                return self._to_domain(model)
            return video
        finally:
            if not self._db:
                db.close()
    
    async def delete(self, video_id: int) -> bool:
        """Elimina un video"""
        db = self._get_db()
        try:
            model = db.query(VideoModel).filter(VideoModel.id == video_id).first()
            if model:
                db.delete(model)
                db.commit()
                return True
            return False
        finally:
            if not self._db:
                db.close()
    
