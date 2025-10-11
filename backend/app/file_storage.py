import os
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from pathlib import Path

# Configuración de archivos
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".wmv"}


def ensure_upload_directory():
    """Asegura que el directorio de uploads existe"""
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def validate_video_file(file: UploadFile) -> None:
    """Valida que el archivo de video cumple con los requisitos"""
    # Verificar tamaño
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo es demasiado grande. Máximo permitido: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Verificar extensión
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(ALLOWED_EXTENSIONS)}"
        )


def generate_unique_filename(original_filename: str) -> str:
    """Genera un nombre de archivo único"""
    file_extension = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{file_extension}"


def save_uploaded_file(file: UploadFile, filename: str) -> str:
    """Guarda el archivo subido en el directorio de uploads"""
    ensure_upload_directory()
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    return file_path


def get_file_url(filename: str) -> str:
    """Genera la URL para acceder al archivo"""
    return f"/uploads/{filename}"


def delete_file(filename: str) -> bool:
    """Elimina un archivo del sistema"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except OSError:
        return False


def get_file_size(file_path: str) -> Optional[int]:
    """Obtiene el tamaño de un archivo en bytes"""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return None


def file_exists(filename: str) -> bool:
    """Verifica si un archivo existe"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    return os.path.exists(file_path)
