from abc import ABC, abstractmethod
from typing import Optional
from fastapi import UploadFile


class FileStorageInterface(ABC):
    """Interface para el almacenamiento de archivos"""
    
    @abstractmethod
    async def save_file(self, file: UploadFile, filename: str) -> str:
        """Guarda un archivo y retorna la ruta donde se guardó"""
        pass
    
    @abstractmethod
    async def delete_file(self, filename: str) -> bool:
        """Elimina un archivo del almacenamiento"""
        pass
    
    @abstractmethod
    async def get_file_url(self, filename: str) -> str:
        """Obtiene la URL pública para acceder al archivo"""
        pass
    
    @abstractmethod
    async def file_exists(self, filename: str) -> bool:
        """Verifica si un archivo existe"""
        pass
    
    @abstractmethod
    async def get_file_size(self, filename: str) -> Optional[int]:
        """Obtiene el tamaño de un archivo en bytes"""
        pass
