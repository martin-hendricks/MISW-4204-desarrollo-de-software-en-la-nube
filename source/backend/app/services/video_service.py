from typing import List
from fastapi import UploadFile
from app.config.settings import settings
from app.domain.entities.video import Video, VideoStatus
from app.domain.entities.vote import Vote
from app.domain.repositories.video_repository import VideoRepositoryInterface
from app.domain.repositories.vote_repository import VoteRepositoryInterface
from app.shared.interfaces.file_storage import FileStorageInterface
from app.shared.interfaces.task_queue import TaskQueueInterface
from app.shared.exceptions.video_exceptions import VideoNotFoundException, VideoNotOwnedException, VideoCannotBeDeletedException


class VideoService:
    """Servicio de aplicación para la gestión de videos"""
    
    def __init__(
        self,
        video_repository: VideoRepositoryInterface,
        vote_repository: VoteRepositoryInterface,
        file_storage: FileStorageInterface,
        task_queue: TaskQueueInterface
    ):
        self._video_repository = video_repository
        self._vote_repository = vote_repository
        self._file_storage = file_storage
        self._task_queue = task_queue
    
    async def upload_video(
        self,
        player_id: int,
        file: UploadFile,
        title: str
    ) -> Video:
        """Sube un nuevo video"""
        from datetime import datetime
        
        # Validar archivo
        await self._validate_video_file(file)
        
        # Obtener extensión del archivo
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'mp4'
        
        # Crear entidad de dominio temporal (sin filename ni URLs aún)
        video = Video(
            id=None,
            player_id=player_id,
            title=title,
            status=VideoStatus.UPLOADED,
            original_url=None,
            processed_url=None,
            uploaded_at=datetime.now()
        )

        # Guardar en repositorio primero para obtener el ID
        created_video = await self._video_repository.create(video)

        # Generar filename usando el ID de la BD - siempre usar .mp4 para consistencia con S3 y worker
        filename = f"{created_video.id}.mp4"
        
        # Generar la URL del archivo original
        original_url = f"{settings.BASE_PATH}/original/{created_video.id}"
        
        # Actualizar el video con el filename y URL correctos
        created_video.original_url = original_url
        
        # Guardar archivo en ubicación original con el filename correcto
        await self._file_storage.save_file(file, filename, "original")
        
        # Actualizar el registro en la BD con la información completa
        updated_video = await self._video_repository.update(created_video)
        
        # Iniciar procesamiento asíncrono
        await self._start_video_processing(updated_video)
        
        return updated_video
    
    async def get_player_videos(self, player_id: int) -> List[Video]:
        """Obtiene todos los videos de un jugador"""
        return await self._video_repository.get_by_player(player_id)
    
    async def get_video(self, video_id: int, player_id: int) -> Video:
        """Obtiene un video específico de un jugador"""
        video = await self._video_repository.get_by_id(video_id)
        if not video:
            raise VideoNotFoundException(f"Video con ID {video_id} no encontrado")
        
        if video.player_id != player_id:
            raise VideoNotOwnedException("No tienes permisos para acceder a este video")
        
        return video
    
    async def delete_video(self, video_id: int, player_id: int) -> bool:
        """Elimina un video"""
        video = await self.get_video(video_id, player_id)

        if not video.can_be_deleted():
            raise VideoCannotBeDeletedException("El video no puede ser eliminado en su estado actual")

        # Eliminar archivos del almacenamiento (original y procesado si existe)
        filename = f"{video_id}.mp4"
        await self._file_storage.delete_file(filename, "original")

        # Si el video está procesado, eliminar también el archivo procesado
        if video.status == VideoStatus.PROCESSED:
            await self._file_storage.delete_file(filename, "processed")

        # Eliminar de la base de datos
        return await self._video_repository.delete(video_id)
    
    async def get_public_videos(self, skip: int = 0, limit: int = 100) -> List[Video]:
        """Obtiene videos públicos para votación con paginación"""
        return await self._video_repository.get_public_videos(skip=skip, limit=limit)
    
    async def vote_for_video(self, video_id: int, player_id: int) -> bool:
        """Vota por un video"""
        video = await self._video_repository.get_by_id(video_id)
        if not video:
            raise VideoNotFoundException(f"Video con ID {video_id} no encontrado")
        
        if not video.is_public():
            raise ValueError("El video no está disponible para votación")
        
        # Verificar que el votante no sea el propietario del video
        if video.player_id == player_id:
            raise ValueError("No puedes votar por tu propio video")
        
        # Verificar si el usuario ya votó por este video
        if await self._vote_repository.has_user_voted(video_id, player_id):
            raise ValueError("Ya has votado por este video")
        
        # Crear el voto usando el VoteRepository
        vote = Vote(
            id=None,
            video_id=video_id,
            player_id=player_id
        )
        
        await self._vote_repository.create(vote)
        return True
    
    async def get_video_votes_count(self, video_id: int) -> int:
        """Obtiene el número de votos de un video"""
        return await self._vote_repository.count_votes_for_video(video_id)
    
    async def get_videos_with_votes(self) -> List[dict]:
        """Obtiene videos públicos con su conteo de votos"""
        videos = await self._video_repository.get_public_videos()
        video_ids = [video.id for video in videos]
        vote_counts = await self._vote_repository.get_votes_by_videos(video_ids)
        
        result = []
        for video in videos:
            result.append({
                "video": video,
                "votes_count": vote_counts.get(video.id, 0)
            })
        
        return result
    
    async def _validate_video_file(self, file: UploadFile) -> None:
        """Valida el archivo de video"""
        # Verificar tamaño (100MB máximo)
        if file.size and file.size > 100 * 1024 * 1024:
            raise ValueError("El archivo es demasiado grande. Máximo permitido: 100MB")
        
        # Verificar tipo de archivo
        allowed_extensions = {'.mp4', '.avi', '.mov', '.wmv'}
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        if f'.{file_extension}' not in allowed_extensions:
            raise ValueError(f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(allowed_extensions)}")
    
    # Método removido - ya no se usa filename único con UUID
    
    async def _start_video_processing(self, video: Video) -> None:
        """Inicia el procesamiento del video enviando tarea a la cola"""
        try:
            # Publicar tarea de procesamiento usando la interfaz
            task_id = await self._task_queue.publish_video_processing_task(video.id)
            
            # Log para debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🎬 Tarea de procesamiento iniciada para video {video.id}")
            logger.info(f"   Task ID: {task_id}")
            
        except Exception as e:
            # Si falla el envío de la tarea, loggear pero no fallar el upload
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Error enviando tarea de procesamiento para video {video.id}: {e}")
            logger.warning("   El video se subió correctamente pero no se procesará automáticamente")
    
    async def mark_video_as_processed(self, video_id: int, processed_url: str) -> None:
        """Marca un video como procesado"""
        video = await self._video_repository.get_by_id(video_id)
        if video:
            video.mark_as_processed(processed_url)
            await self._video_repository.update(video)
    
    async def get_original_video(self, video_id: int, player_id: int) -> bytes:
        """Obtiene el contenido del video original"""
        video = await self.get_video(video_id, player_id)
        # Pasar el filename con extensión (siempre mp4 después del procesamiento inicial)
        filename = f"{video_id}.mp4"
        return await self._file_storage.get_file_content(filename, "original")
    
    async def get_processed_video(self, video_id: int, player_id: int) -> bytes:
        """Obtiene el contenido del video procesado"""
        video = await self.get_video(video_id, player_id)

        if not video.processed_url:
            raise ValueError("El video procesado no está disponible")

        # Pasar el filename con extensión
        filename = f"{video_id}.mp4"
        return await self._file_storage.get_file_content(filename, "processed")


class MockVideoService(VideoService):
    """Implementación mock del servicio de videos para pruebas de carga"""
    
    async def _start_video_processing(self, video: Video) -> None:
        """Sobrescribe el método para no hacer nada y retornar instantáneamente."""
        # En modo mock, no se inicia el procesamiento asíncrono.
        # Simplemente se loguea o no se hace nada.
        print(f"[Mock Mode] Video processing skipped for video_id: {video.id}")
        return

