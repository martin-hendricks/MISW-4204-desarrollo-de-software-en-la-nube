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

# Importar métricas de CloudWatch
from metrics import cw_metrics, current_process
from cloudwatch.cloudwatch_metrics import MetricUnit

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

                # Publicar métricas del worker a CloudWatch
                # NOTA: ActiveTasks/ReservedTasks no disponibles con SQS
                # AWS SQS publica sus propias métricas: ApproximateNumberOfMessagesVisible, etc.
                cw_metrics.put_metrics(
                    metrics=[
                        {"name": "ProcessCPU", "value": process_cpu, "unit": MetricUnit.PERCENT},
                        {"name": "ProcessMemoryMB", "value": process_memory_mb, "unit": MetricUnit.MEGABYTES},
                        {"name": "ProcessMemoryPercent", "value": process_memory_percent, "unit": MetricUnit.PERCENT},
                        {"name": "SystemCPU", "value": system_cpu, "unit": MetricUnit.PERCENT},
                        {"name": "SystemMemoryPercent", "value": system_memory.percent, "unit": MetricUnit.PERCENT}
                    ],
                    dimensions={"MetricType": "System"}
                )

                logger.debug(f"[SYSTEM METRICS] CPU: {process_cpu:.1f}% | Memory: {process_memory_mb:.1f}MB")

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
    
    # 2. Check SQS (broker)
    try:
        import boto3
        sqs = boto3.client('sqs', region_name=config.AWS_REGION)
        # Verificar que la cola existe
        sqs.get_queue_attributes(
            QueueUrl=config.SQS_QUEUE_URL,
            AttributeNames=['ApproximateNumberOfMessages']
        )
        checks["sqs"] = True
    except Exception as e:
        checks["sqs"] = False
        all_healthy = False
        messages.append(f"SQS error: {str(e)}")
    
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
            "sqs_queue": config.SQS_QUEUE_URL,
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
    NOTA: No disponible con SQS (requiere colas temporales)
    """
    return JSONResponse(
        content={
            "status": "unavailable",
            "message": "Celery inspect() not available with SQS broker (requires temporary reply queues)",
            "broker": "SQS"
        },
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE
    )


@app.get("/celery/ping")
def celery_ping():
    """
    Ping a los workers de Celery
    NOTA: No disponible con SQS (requiere colas temporales)
    """
    return JSONResponse(
        content={
            "status": "unavailable",
            "message": "Celery ping() not available with SQS broker (requires temporary reply queues)",
            "broker": "SQS",
            "suggestion": "Use /health/detailed endpoint instead"
        },
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.WORKER_API_HOST,
        port=config.WORKER_API_PORT,
        log_level=config.LOG_LEVEL.lower()
    )