import os
import glob
from typing import Optional, Literal
from fastapi import UploadFile
from app.shared.interfaces.file_storage import FileStorageInterface, LocationType


class LocalFileStorage(FileStorageInterface):
    """Implementación local del almacenamiento de archivos"""
    
    def __init__(self, upload_dir: str = None):
        # Usar variable de entorno o ruta por defecto
        self.upload_dir = upload_dir or os.getenv("UPLOAD_DIR", "/app/uploads")
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
        directory = os.path.join(self.upload_dir, location)
        pattern_path = os.path.join(directory, f"{filename}.*")
        try:
            files_found = glob.glob(pattern_path)
            if files_found:
                for file_path in files_found:
                    os.remove(file_path)
                return True
            return False
        except OSError:
            return False
    
    async def get_file_url(self, filename: str, location: LocationType = "original") -> str:
        """Genera la URL para acceder al archivo"""
        return f"/app/uploads/{location}/{filename}"
    
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
        directory = os.path.join(self.upload_dir, location)
        try:
            if os.path.exists(directory):
                files = os.listdir(directory)
                matching_files = [f for f in files if f.startswith(f"{filename}.")]
                
                if matching_files:
                    # Tomar el primer archivo que coincida
                    actual_filename = matching_files[0]
                    file_path = os.path.join(directory, actual_filename)
                    
                    with open(file_path, "rb") as file:
                        return file.read()
                else:
                    raise FileNotFoundError(f"Archivo no encontrado: {filename} en ubicación {location}")
            else:
                raise FileNotFoundError(f"Directorio no encontrado: {location}")
        except OSError as e:
            raise FileNotFoundError(f"Error al leer archivo: {filename} en ubicación {location}")
    
