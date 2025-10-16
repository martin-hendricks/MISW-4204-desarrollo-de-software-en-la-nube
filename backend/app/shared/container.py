"""Contenedor de dependencias para inyección de dependencias"""

from typing import Dict, Any, Type
from app.shared.interfaces.file_storage import FileStorageInterface
from app.shared.interfaces.authentication import AuthenticationInterface
from app.domain.repositories.player_repository import PlayerRepositoryInterface
from app.domain.repositories.video_repository import VideoRepositoryInterface
from app.domain.repositories.vote_repository import VoteRepositoryInterface
from app.services.player_service import PlayerService
import os
from app.services.video_service import VideoService, MockVideoService


class DIContainer:
    """Contenedor de inyección de dependencias"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register_singleton(self, interface: Type, implementation: Type) -> None:
        """Registra una implementación como singleton"""
        self._services[interface.__name__] = (implementation, True)
    
    def register_transient(self, interface: Type, implementation: Type) -> None:
        """Registra una implementación como transiente"""
        self._services[interface.__name__] = (implementation, False)
    
    def get(self, interface: Type) -> Any:
        """Obtiene una instancia del servicio"""
        interface_name = interface.__name__
        
        if interface_name not in self._services:
            raise ValueError(f"Servicio {interface_name} no registrado")
        
        implementation_class, is_singleton = self._services[interface_name]
        
        if is_singleton:
            if interface_name not in self._singletons:
                self._singletons[interface_name] = implementation_class()
            return self._singletons[interface_name]
        else:
            return implementation_class()
    
    def get_player_service(self) -> PlayerService:
        """Obtiene el servicio de jugadores"""
        return PlayerService(
            player_repository=self.get(PlayerRepositoryInterface),
            auth_service=self.get(AuthenticationInterface)
        )
    
    def get_video_service(self) -> VideoService:
        """Obtiene el servicio de videos, usando el mock si está en modo test."""
        
        # Usa MockVideoService si la variable de entorno TEST_MODE es 'true'
        if os.getenv("TEST_MODE") == "true":
            ServiceClass = MockVideoService
        else:
            ServiceClass = VideoService
            
        return ServiceClass(
            video_repository=self.get(VideoRepositoryInterface),
            vote_repository=self.get(VoteRepositoryInterface),
            file_storage=self.get(FileStorageInterface)
        )


# Instancia global del contenedor
container = DIContainer()
