from typing import List, Optional
from fastapi import UploadFile
from app.domain.entities.video import Video, VideoStatus
from app.domain.repositories.video_repository import VideoRepositoryInterface
from app.shared.interfaces.file_storage import FileStorageInterface
from app.shared.exceptions.video_exceptions import VideoNotFoundException, VideoNotOwnedException, VideoCannotBeDeletedException


class VideoService:
    """Servicio de aplicación para la gestión de videos"""
    
    def __init__(
        self,
        video_repository: VideoRepositoryInterface,
        file_storage: FileStorageInterface
    ):
        self._video_repository = video_repository
        self._file_storage = file_storage
    
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
        
        # Generar nombre único
        filename = await self._generate_unique_filename(file.filename)
        
        # Guardar archivo en ubicación original
        file_path = await self._file_storage.save_file(file, filename, "original")
        
        # Crear entidad de dominio con todos los campos inicializados
        video = Video(
            id=None,
            player_id=player_id,
            title=title,
            filename=filename,
            status=VideoStatus.UPLOADED,
            original_url=file_path,  # URL del archivo original
            processed_url=None,
            votes_count=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Guardar en repositorio
        created_video = await self._video_repository.create(video)
        
        # Iniciar procesamiento asíncrono
        await self._start_video_processing(created_video)
        
        return created_video
    
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
        
        # Eliminar archivo del almacenamiento
        await self._file_storage.delete_file(video.filename)
        
        # Eliminar de la base de datos
        return await self._video_repository.delete(video_id)
    
    async def get_public_videos(self) -> List[Video]:
        """Obtiene todos los videos públicos para votación"""
        return await self._video_repository.get_public_videos()
    
    async def vote_for_video(self, video_id: int, voter_id: int) -> bool:
        """Vota por un video"""
        video = await self._video_repository.get_by_id(video_id)
        if not video:
            raise VideoNotFoundException(f"Video con ID {video_id} no encontrado")
        
        if not video.is_public():
            raise ValueError("El video no está disponible para votación")
        
        # Verificar que el votante no sea el propietario del video
        if video.player_id == voter_id:
            raise ValueError("No puedes votar por tu propio video")
        
        # Verificar si el usuario ya votó por este video
        if await self._video_repository.has_user_voted(video_id, voter_id):
            raise ValueError("Ya has votado por este video")
        
        # Incrementar votos directamente en el repositorio
        success = await self._video_repository.increment_votes(video_id, voter_id)
        if not success:
            raise VideoNotFoundException(f"Video con ID {video_id} no encontrado")
        
        return True
    
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
    
    async def _generate_unique_filename(self, original_filename: str) -> str:
        """Genera un nombre único para el archivo"""
        import uuid
        file_extension = original_filename.split('.')[-1] if '.' in original_filename else 'mp4'
        return f"{uuid.uuid4()}.{file_extension}"
    
    async def _start_video_processing(self, video: Video) -> None:
        """Inicia el procesamiento asíncrono del video"""
        # Aquí se integraría con Celery o el sistema de tareas asíncronas
        video.start_processing()
        await self._video_repository.update(video)
        
        # En una implementación real, aquí se enviaría la tarea a la cola
        # await self._task_queue.enqueue('process_video', video.id)
    
    async def mark_video_as_processed(self, video_id: int, processed_url: str) -> None:
        """Marca un video como procesado"""
        video = await self._video_repository.get_by_id(video_id)
        if video:
            video.mark_as_processed(processed_url)
            await self._video_repository.update(video)
    
    async def get_original_video(self, video_id: int, player_id: int) -> bytes:
        """Obtiene el contenido del video original"""
        video = await self.get_video(video_id, player_id)
        return await self._file_storage.get_file_content(video.filename, "original")
    
    async def get_processed_video(self, video_id: int, player_id: int) -> bytes:
        """Obtiene el contenido del video procesado"""
        video = await self.get_video(video_id, player_id)
        
        if not video.processed_url:
            raise ValueError("El video procesado no está disponible")
        
        return await self._file_storage.get_file_content(video.filename, "processed")
