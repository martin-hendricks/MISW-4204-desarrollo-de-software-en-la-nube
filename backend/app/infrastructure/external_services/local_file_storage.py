import os
import uuid
from typing import Optional
from fastapi import UploadFile
from app.shared.interfaces.file_storage import FileStorageInterface


class LocalFileStorage(FileStorageInterface):
    """Implementación local del almacenamiento de archivos"""
    
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        self._ensure_upload_directory()
    
    def _ensure_upload_directory(self):
        """Asegura que el directorio de uploads existe"""
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def save_file(self, file: UploadFile, filename: str) -> str:
        """Guarda un archivo en el sistema local"""
        file_path = os.path.join(self.upload_dir, filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return file_path
    
    async def delete_file(self, filename: str) -> bool:
        """Elimina un archivo del sistema local"""
        file_path = os.path.join(self.upload_dir, filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except OSError:
            return False
    
    async def get_file_url(self, filename: str) -> str:
        """Genera la URL para acceder al archivo"""
        return f"/uploads/{filename}"
    
    async def file_exists(self, filename: str) -> bool:
        """Verifica si un archivo existe"""
        file_path = os.path.join(self.upload_dir, filename)
        return os.path.exists(file_path)
    
    async def get_file_size(self, filename: str) -> Optional[int]:
        """Obtiene el tamaño de un archivo en bytes"""
        file_path = os.path.join(self.upload_dir, filename)
        try:
            return os.path.getsize(file_path)
        except OSError:
            return None
