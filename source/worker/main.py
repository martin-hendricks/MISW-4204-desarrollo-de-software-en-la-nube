"""
API de Health Checks para el Worker ANB Rising Stars
Este servicio corre en paralelo al worker de Celery
"""
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Optional
import logging
import asyncio
import psutil
import os

from config import config
from database import test_db_connection
from celery_app import app as celery_app

# Importar métricas de CloudWatch
from metrics import cw_metrics, current_process
from shared.cloudwatch_metrics import MetricUnit

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
            "celery_stats": "/celery/stats",
            "metrics": "/metrics"
        }
    }


@app.get("/metrics")
def metrics():
    """
    Endpoint de compatibilidad con Prometheus (deprecado)
    Las métricas ahora se publican a CloudWatch automáticamente
    """
    return {
        "message": "Metrics migrated to CloudWatch",
        "namespace": os.getenv("CLOUDWATCH_NAMESPACE", "ANB/Worker"),
        "service": "VideoProcessor",
        "documentation": "Check AWS CloudWatch console for metrics"
    }


# ===== MÉTRICAS DE SISTEMA Y CELERY (Background Task) =====
@app.on_event("startup")
async def start_metrics_collection():
    """
    Publica métricas de sistema y Celery cada 60 segundos a CloudWatch
    """
    async def publish_worker_metrics():
        while True:
            try:
                await asyncio.sleep(60)  # Publicar cada 60 segundos

                # 1. Métricas del proceso Worker
                process_cpu = current_process.cpu_percent(interval=0.1)
                mem_info = current_process.memory_info()
                process_memory_mb = mem_info.rss / (1024 * 1024)
                process_memory_percent = current_process.memory_percent()

                # 2. Métricas del sistema completo
                system_cpu = psutil.cpu_percent(interval=0.1)
                system_memory = psutil.virtual_memory()

                # 3. Métricas de Celery
                inspect = celery_app.control.inspect()

                # Tareas activas
                active = inspect.active()
                total_active = sum(len(tasks) for tasks in active.values()) if active else 0

                # Tareas reservadas
                reserved = inspect.reserved()
                total_reserved = sum(len(tasks) for tasks in reserved.values()) if reserved else 0

                # 4. Tamaño de colas (Redis o SQS)
                video_queue_length = 0
                dlq_length = 0

                if not config.USE_SQS:
                    # Solo para Redis (SQS no tiene concepto de queue length directamente accesible)
                    try:
                        import redis
                        r = redis.from_url(config.REDIS_URL)
                        video_queue_length = r.llen('video_processing') or 0
                        dlq_length = r.llen('dlq') or 0
                    except Exception as e:
                        logger.warning(f"Error obteniendo tamaño de colas Redis: {e}")

                # Publicar todas las métricas del worker
                cw_metrics.put_metrics(
                    metrics=[
                        {"name": "ProcessCPU", "value": process_cpu, "unit": MetricUnit.PERCENT},
                        {"name": "ProcessMemoryMB", "value": process_memory_mb, "unit": MetricUnit.MEGABYTES},
                        {"name": "ProcessMemoryPercent", "value": process_memory_percent, "unit": MetricUnit.PERCENT},
                        {"name": "SystemCPU", "value": system_cpu, "unit": MetricUnit.PERCENT},
                        {"name": "SystemMemoryPercent", "value": system_memory.percent, "unit": MetricUnit.PERCENT},
                        {"name": "ActiveTasks", "value": total_active, "unit": MetricUnit.COUNT},
                        {"name": "ReservedTasks", "value": total_reserved, "unit": MetricUnit.COUNT}
                    ],
                    dimensions={"MetricType": "System"}
                )

                # Publicar métricas de colas por separado (con dimensión de nombre de cola)
                if not config.USE_SQS:
                    cw_metrics.put_metric(
                        metric_name="QueueLength",
                        value=video_queue_length,
                        unit=MetricUnit.COUNT,
                        dimensions={"QueueName": "video_processing"}
                    )

                    cw_metrics.put_metric(
                        metric_name="QueueLength",
                        value=dlq_length,
                        unit=MetricUnit.COUNT,
                        dimensions={"QueueName": "dlq"}
                    )

                logger.debug(f"[SYSTEM METRICS] CPU: {process_cpu:.1f}% | Memory: {process_memory_mb:.1f}MB | Active Tasks: {total_active}")

            except Exception as e:
                logger.error(f"Error publishing worker metrics: {e}")

    # Iniciar tarea en background
    asyncio.create_task(publish_worker_metrics())
    logger.info("Worker metrics background task started (60s interval)")


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