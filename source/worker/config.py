"""
Configuración del Worker ANB Rising Stars
Variables de entorno y configuración centralizada
"""
import os
from pathlib import Path

class Config:
    """Configuración del worker de procesamiento de videos"""
    
    # ===== REDIS BROKER =====
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    # NO usamos result_backend - PostgreSQL es la única fuente de verdad
    
    # ===== POSTGRESQL =====
    DATABASE_URL: str = os.getenv(
        'DATABASE_URL', 
        'postgresql://user:password@database:5432/fileprocessing'
    )
    
    # ===== ALMACENAMIENTO LOCAL (Carpetas compartidas) =====
    UPLOAD_BASE_DIR: str = os.getenv('UPLOAD_DIR', '/app/uploads')
    
    @property
    def ORIGINAL_DIR(self) -> str:
        """Carpeta para videos originales"""
        path = Path(self.UPLOAD_BASE_DIR) / 'original'
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    @property
    def PROCESSED_DIR(self) -> str:
        """Carpeta para videos procesados"""
        path = Path(self.UPLOAD_BASE_DIR) / 'processed'
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    @property
    def TEMP_DIR(self) -> str:
        """Carpeta temporal para procesamiento"""
        path = Path(self.UPLOAD_BASE_DIR) / 'temp'
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    # ===== CELERY =====
    CELERY_TASK_DEFAULT_RETRY_DELAY: int = int(os.getenv('CELERY_RETRY_DELAY', '60'))
    CELERY_TASK_MAX_RETRIES: int = int(os.getenv('CELERY_MAX_RETRIES', '3'))
    CELERY_WORKER_CONCURRENCY: int = int(os.getenv('CELERY_CONCURRENCY', '4'))
    
    # ===== PROCESAMIENTO DE VIDEO =====
    # Según especificación del proyecto
    VIDEO_MAX_DURATION: int = 30  # segundos (de 20-60s a máximo 30s)
    VIDEO_RESOLUTION_WIDTH: int = 1280  # 720p
    VIDEO_RESOLUTION_HEIGHT: int = 720
    VIDEO_ASPECT_RATIO: str = "16:9"
    VIDEO_CODEC: str = "libx264"
    VIDEO_PRESET: str = "fast"  # ultrafast, fast, medium, slow
    VIDEO_CRF: int = 23  # Constant Rate Factor (18-28 recomendado, menor = mejor calidad)
    
    # ===== LOGOS Y MARCA DE AGUA =====
    LOGO_PATH: str = os.getenv('LOGO_PATH', '/app/assets/anb_logo.png')
    LOGO_POSITION: str = os.getenv('LOGO_POSITION', 'top-right')  # top-left, top-right, bottom-left, bottom-right
    LOGO_MARGIN: int = 10  # píxeles desde el borde
    
    # Cortinillas (máximo 5 segundos adicionales según especificación)
    INTRO_VIDEO_PATH: str = os.getenv('INTRO_VIDEO_PATH', '/app/assets/intro.mp4')
    OUTRO_VIDEO_PATH: str = os.getenv('OUTRO_VIDEO_PATH', '/app/assets/outro.mp4')
    MAX_INTRO_DURATION: float = 2.5  # segundos
    MAX_OUTRO_DURATION: float = 2.5  # segundos
    
    # ===== LOGGING =====
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # ===== TIMEOUTS =====
    TASK_SOFT_TIME_LIMIT: int = 600  # 10 minutos (warning)
    TASK_HARD_TIME_LIMIT: int = 900  # 15 minutos (kill task)
    
    # ===== HEALTH CHECK API =====
    WORKER_API_HOST: str = os.getenv('WORKER_API_HOST', '0.0.0.0')
    WORKER_API_PORT: int = int(os.getenv('WORKER_API_PORT', '8001'))
    
    @classmethod
    def validate(cls) -> bool:
        """Valida que las configuraciones críticas estén presentes"""
        instance = cls()
        required = [
            instance.REDIS_URL,
            instance.DATABASE_URL,
            instance.UPLOAD_BASE_DIR
        ]
        return all(required)
    
    def __repr__(self):
        return f"<Config(redis={self.REDIS_URL}, db={self.DATABASE_URL})>"


# Instancia global
config = Config()

# Crear directorios al importar
_ = config.ORIGINAL_DIR
_ = config.PROCESSED_DIR
_ = config.TEMP_DIR

