"""Configuración del contenedor de dependencias"""

from app.shared.container import container
from app.shared.interfaces.file_storage import FileStorageInterface
from app.shared.interfaces.authentication import AuthenticationInterface
from app.shared.interfaces.task_queue import TaskQueueInterface
from app.domain.repositories.player_repository import PlayerRepositoryInterface
from app.domain.repositories.video_repository import VideoRepositoryInterface
from app.domain.repositories.vote_repository import VoteRepositoryInterface
from app.config.settings import settings, FileStorageType


def configure_container():
    """Configura el contenedor de dependencias con las implementaciones apropiadas"""

    # Configurar almacenamiento de archivos basado en la configuración
    if settings.FILE_STORAGE_TYPE == FileStorageType.LOCAL:
        from app.infrastructure.external_services.local_file_storage import LocalFileStorage
        # Crear instancia con parámetros
        local_instance = LocalFileStorage(settings.UPLOAD_DIR)
        container._singletons[FileStorageInterface.__name__] = local_instance
    elif settings.FILE_STORAGE_TYPE == FileStorageType.S3:
        from app.infrastructure.external_services.s3_file_storage import S3FileStorage
        # Crear instancia con parámetros requeridos
        s3_instance = S3FileStorage(
            bucket_name=settings.S3_BUCKET_NAME,
            region=settings.AWS_REGION
        )
        container._singletons[FileStorageInterface.__name__] = s3_instance
    
    # Configurar autenticación
    from app.infrastructure.external_services.jwt_auth_service import JWTAuthService
    container.register_singleton(AuthenticationInterface, JWTAuthService)
    
    # Configurar cola de tareas
    from app.infrastructure.external_services.celery_client import CeleryTaskQueue
    container.register_singleton(TaskQueueInterface, CeleryTaskQueue)
    
    
    # Configurar repositorios
    from app.infrastructure.repositories.player_repository import PlayerRepository
    from app.infrastructure.repositories.video_repository import VideoRepository
    from app.infrastructure.repositories.vote_repository import VoteRepository
    
    container.register_singleton(PlayerRepositoryInterface, PlayerRepository)
    container.register_singleton(VideoRepositoryInterface, VideoRepository)
    container.register_singleton(VoteRepositoryInterface, VoteRepository)


# Configurar el contenedor al importar el módulo
configure_container()
