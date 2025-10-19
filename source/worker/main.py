"""
API de Health Checks para el Worker ANB Rising Stars
Este servicio corre en paralelo al worker de Celery
"""
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional
import logging

from config import config
from database import test_db_connection
from celery_app import app as celery_app

# Configurar logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="ANB Worker Health API",
    version="1.0.0",
    description="Health checks y monitoreo del worker de procesamiento de videos"
)


class HealthResponse(BaseModel):
    """Modelo de respuesta de health check"""
    status: str
    service: str
    version: str
    checks: Dict[str, bool]
    message: Optional[str] = None


@app.get("/")
def read_root():
    """Endpoint raíz"""
    return {
        "service": "ANB Video Processing Worker",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "health_detailed": "/health/detailed",
            "celery_stats": "/celery/stats"
        }
    }


@app.get("/health", response_model=HealthResponse)
def health_check():
    """
    Health check básico
    Usado por Docker, Kubernetes, load balancers, etc.
    """
    return HealthResponse(
        status="healthy",
        service="worker",
        version="1.0.0",
        checks={"api": True}
    )


@app.get("/health/detailed")
def detailed_health_check():
    """
    Health check detallado
    Verifica conexión a Redis, PostgreSQL y estado del sistema
    """
    checks = {}
    all_healthy = True
    messages = []
    
    # 1. Check PostgreSQL
    try:
        pg_healthy = test_db_connection()
        checks["postgresql"] = pg_healthy
        if not pg_healthy:
            all_healthy = False
            messages.append("PostgreSQL connection failed")
    except Exception as e:
        checks["postgresql"] = False
        all_healthy = False
        messages.append(f"PostgreSQL error: {str(e)}")
    
    # 2. Check Redis (broker)
    try:
        celery_app.backend.client.ping()
        checks["redis"] = True
    except:
        try:
            # Intentar ping directo
            import redis
            r = redis.from_url(config.REDIS_URL)
            r.ping()
            checks["redis"] = True
        except Exception as e:
            checks["redis"] = False
            all_healthy = False
            messages.append(f"Redis error: {str(e)}")
    
    # 3. Check directorios de almacenamiento
    try:
        import os
        checks["storage_original"] = os.path.exists(config.ORIGINAL_DIR) and os.access(config.ORIGINAL_DIR, os.W_OK)
        checks["storage_processed"] = os.path.exists(config.PROCESSED_DIR) and os.access(config.PROCESSED_DIR, os.W_OK)
        checks["storage_temp"] = os.path.exists(config.TEMP_DIR) and os.access(config.TEMP_DIR, os.W_OK)
        
        if not all([checks["storage_original"], checks["storage_processed"], checks["storage_temp"]]):
            all_healthy = False
            messages.append("Storage directories not accessible")
    except Exception as e:
        checks["storage_original"] = False
        checks["storage_processed"] = False
        checks["storage_temp"] = False
        all_healthy = False
        messages.append(f"Storage error: {str(e)}")
    
    # 4. Check FFmpeg
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        checks["ffmpeg"] = result.returncode == 0
        if not checks["ffmpeg"]:
            all_healthy = False
            messages.append("FFmpeg not available")
    except Exception as e:
        checks["ffmpeg"] = False
        all_healthy = False
        messages.append(f"FFmpeg error: {str(e)}")
    
    response_data = {
        "status": "healthy" if all_healthy else "unhealthy",
        "service": "worker",
        "version": "1.0.0",
        "checks": checks,
        "config": {
            "redis_url": config.REDIS_URL.split('@')[-1] if '@' in config.REDIS_URL else config.REDIS_URL,
            "upload_dir": config.UPLOAD_BASE_DIR,
            "max_retries": config.CELERY_TASK_MAX_RETRIES,
            "concurrency": config.CELERY_WORKER_CONCURRENCY
        }
    }
    
    if messages:
        response_data["messages"] = messages
    
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(content=response_data, status_code=status_code)


@app.get("/celery/stats")
def celery_stats():
    """
    Estadísticas del worker de Celery
    Muestra información sobre tareas activas, reservadas, etc.
    """
    try:
        # Obtener estadísticas del worker
        inspect = celery_app.control.inspect()
        
        stats = {
            "active_tasks": inspect.active(),
            "reserved_tasks": inspect.reserved(),
            "registered_tasks": inspect.registered(),
            "stats": inspect.stats(),
        }
        
        return {
            "status": "success",
            "celery_stats": stats
        }
    except Exception as e:
        logger.error(f"Error obteniendo stats de Celery: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@app.get("/celery/ping")
def celery_ping():
    """
    Ping a los workers de Celery
    Verifica que hay workers activos escuchando
    """
    try:
        result = celery_app.control.ping(timeout=5)
        
        if result:
            return {
                "status": "success",
                "workers_online": len(result),
                "workers": result
            }
        else:
            return JSONResponse(
                content={
                    "status": "no_workers",
                    "message": "No hay workers de Celery activos"
                },
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    except Exception as e:
        logger.error(f"Error haciendo ping a Celery: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e)
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.WORKER_API_HOST,
        port=config.WORKER_API_PORT,
        log_level=config.LOG_LEVEL.lower()
    )