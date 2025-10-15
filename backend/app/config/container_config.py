"""Configuración del contenedor de dependencias"""

from app.shared.container import container
from app.shared.interfaces.file_storage import FileStorageInterface
from app.shared.interfaces.authentication import AuthenticationInterface
from app.domain.repositories.player_repository import PlayerRepositoryInterface
from app.domain.repositories.video_repository import VideoRepositoryInterface
from app.domain.repositories.vote_repository import VoteRepositoryInterface
from app.config.settings import settings, FileStorageType


def configure_container():
    """Configura el contenedor de dependencias con las implementaciones apropiadas"""
    
    # Configurar almacenamiento de archivos basado en la configuración
    if settings.FILE_STORAGE_TYPE == FileStorageType.LOCAL:
        from app.infrastructure.external_services.local_file_storage import LocalFileStorage
        container.register_singleton(FileStorageInterface, LocalFileStorage)
    elif settings.FILE_STORAGE_TYPE == FileStorageType.S3:
        from app.infrastructure.external_services.s3_file_storage import S3FileStorage
        container.register_singleton(FileStorageInterface, S3FileStorage)
    
    # Configurar autenticación
    from app.infrastructure.external_services.jwt_auth_service import JWTAuthService
    container.register_singleton(AuthenticationInterface, JWTAuthService)
    
    
    # Configurar repositorios
    from app.infrastructure.repositories.player_repository import PlayerRepository
    from app.infrastructure.repositories.video_repository import VideoRepository
    from app.infrastructure.repositories.vote_repository import VoteRepository
    
    container.register_singleton(PlayerRepositoryInterface, PlayerRepository)
    container.register_singleton(VideoRepositoryInterface, VideoRepository)
    container.register_singleton(VoteRepositoryInterface, VoteRepository)


# Configurar el contenedor al importar el módulo
configure_container()
