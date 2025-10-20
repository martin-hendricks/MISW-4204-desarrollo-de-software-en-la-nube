"""Aplicación FastAPI para tests"""

import os

# IMPORTANTE: Configurar variables de entorno ANTES de cualquier importación
# que use settings, ya que settings se evalúa al momento de la importación
os.environ["UPLOAD_DIR"] = os.path.join(os.getcwd(), "test_uploads")
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["FILE_STORAGE_TYPE"] = "local"
os.environ["TEST_MODE"] = "true"

# Crear el directorio de uploads para tests
test_upload_dir = os.path.join(os.getcwd(), "test_uploads")
os.makedirs(test_upload_dir, exist_ok=True)
os.makedirs(os.path.join(test_upload_dir, "original"), exist_ok=True)
os.makedirs(os.path.join(test_upload_dir, "processed"), exist_ok=True)

# Ahora importar después de configurar las variables de entorno
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Importar configuración del contenedor
from app.config.container_config import configure_container
from app.config.settings import settings

# Crear la aplicación FastAPI
app = FastAPI(
    title="ANB Rising Stars Showcase API",
    description="API REST con arquitectura DDD - Gestión de videos de habilidades de baloncesto",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar directorio estático para servir archivos (solo si es almacenamiento local)
if settings.FILE_STORAGE_TYPE.value == "local" and os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Incluir routers
from app.routers import auth, videos, public

app.include_router(auth.router)
app.include_router(videos.router)
app.include_router(public.router)

@app.get("/")
def read_root():
    return {
        "message": "ANB Rising Stars Showcase API", 
        "version": "1.0.0",
        "architecture": "DDD + Clean Architecture",
        "docs": "/docs",
        "file_storage": settings.FILE_STORAGE_TYPE.value
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "service": "backend",
        "architecture": "DDD",
        "file_storage": settings.FILE_STORAGE_TYPE.value
    }

@app.get("/config")
def get_config():
    """Endpoint para ver la configuración actual (solo para desarrollo)"""
    return {
        "file_storage_type": settings.FILE_STORAGE_TYPE.value,
        "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "hidden",
        "redis_url": settings.REDIS_URL.split("@")[-1] if "@" in settings.REDIS_URL else "hidden"
    }
