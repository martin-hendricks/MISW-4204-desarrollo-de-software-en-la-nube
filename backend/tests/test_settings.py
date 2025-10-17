"""Configuración específica para tests"""

import os
from app.config.settings import Settings, FileStorageType

class TestSettings(Settings):
    """Configuración de la aplicación para tests"""
    
    # Base de datos de prueba
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # Directorio de uploads para tests (directorio local)
    UPLOAD_DIR: str = os.path.join(os.getcwd(), "test_uploads")
    
    # Almacenamiento local para tests
    FILE_STORAGE_TYPE: FileStorageType = FileStorageType.LOCAL
    
    # Base path para tests
    BASE_PATH: str = "http://localhost:8000/videos"

# Instancia global de configuración para tests
test_settings = TestSettings()
