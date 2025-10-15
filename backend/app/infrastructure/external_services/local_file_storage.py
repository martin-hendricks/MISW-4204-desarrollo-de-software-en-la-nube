import os
import uuid
from typing import Optional, Literal
from fastapi import UploadFile
from app.shared.interfaces.file_storage import FileStorageInterface, LocationType


class LocalFileStorage(FileStorageInterface):
    """Implementación local del almacenamiento de archivos"""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        self._ensure_upload_directories()
    
    def _ensure_upload_directories(self):
        """Asegura que los directorios de uploads existen"""
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(os.path.join(self.upload_dir, "original"), exist_ok=True)
        os.makedirs(os.path.join(self.upload_dir, "processed"), exist_ok=True)
    
    def _get_file_path(self, filename: str, location: LocationType) -> str:
        """Obtiene la ruta completa del archivo basada en la ubicación"""
        return os.path.join(self.upload_dir, location, filename)
    
    async def save_file(self, file: UploadFile, filename: str, location: LocationType = "original") -> str:
        """Guarda un archivo en el sistema local"""
        file_path = self._get_file_path(filename, location)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return file_path
    
    async def delete_file(self, filename: str, location: LocationType = "original") -> bool:
        """Elimina un archivo del sistema local"""
        file_path = self._get_file_path(filename, location)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except OSError:
            return False
    
    async def get_file_url(self, filename: str, location: LocationType = "original") -> str:
        """Genera la URL para acceder al archivo"""
        return f"/uploads/{location}/{filename}"
    
    async def file_exists(self, filename: str, location: LocationType = "original") -> bool:
        """Verifica si un archivo existe"""
        file_path = self._get_file_path(filename, location)
        return os.path.exists(file_path)
    
    async def get_file_size(self, filename: str, location: LocationType = "original") -> Optional[int]:
        """Obtiene el tamaño de un archivo en bytes"""
        file_path = self._get_file_path(filename, location)
        try:
            return os.path.getsize(file_path)
        except OSError:
            return None
    
    async def get_file_content(self, filename: str, location: LocationType = "original") -> bytes:
        """Obtiene el contenido del archivo como bytes"""
        file_path = self._get_file_path(filename, location)
        try:
            with open(file_path, "rb") as file:
                return file.read()
        except OSError as e:
            raise FileNotFoundError(f"Archivo no encontrado: {filename} en ubicación {location}")
