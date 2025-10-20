from abc import ABC, abstractmethod
from typing import Optional, Literal
from fastapi import UploadFile

LocationType = Literal["original", "processed"]


class FileStorageInterface(ABC):
    """Interface para el almacenamiento de archivos"""
    
    @abstractmethod
    async def save_file(self, file: UploadFile, filename: str, location: LocationType = "original") -> str:
        """Guarda un archivo y retorna la ruta donde se guardó"""
        pass
    
    @abstractmethod
    async def delete_file(self, filename: str, location: LocationType = "original") -> bool:
        """Elimina un archivo del almacenamiento"""
        pass
    
    @abstractmethod
    async def get_file_url(self, filename: str, location: LocationType = "original") -> str:
        """Obtiene la URL pública para acceder al archivo"""
        pass
    
    @abstractmethod
    async def file_exists(self, filename: str, location: LocationType = "original") -> bool:
        """Verifica si un archivo existe"""
        pass
    
    @abstractmethod
    async def get_file_size(self, filename: str, location: LocationType = "original") -> Optional[int]:
        """Obtiene el tamaño de un archivo en bytes"""
        pass
    
    @abstractmethod
    async def get_file_content(self, filename: str, location: LocationType = "original") -> bytes:
        """Obtiene el contenido del archivo como bytes"""
        pass
