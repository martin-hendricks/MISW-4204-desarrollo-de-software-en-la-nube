from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import asyncio
import logging
import psutil
import sys

# Configurar logger
logger = logging.getLogger(__name__)

# Importar configuración del contenedor
from app.config.container_config import configure_container
from app.config.settings import settings

# ===== MÉTRICAS DE CLOUDWATCH =====
# Agregar directorio shared al path para importar módulo compartido
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.cloudwatch_metrics import CloudWatchMetrics, MetricUnit

# Inicializar cliente CloudWatch
cw_metrics = CloudWatchMetrics(
    namespace=os.getenv("CLOUDWATCH_NAMESPACE", "ANB/Backend"),
    service_name="API"
)

# Obtener el proceso actual para métricas
current_process = psutil.Process(os.getpid())

# Crear la aplicación FastAPI
app = FastAPI(
    title="ANB Rising Stars Showcase API",
    description="API REST con arquitectura DDD - Gestión de videos de habilidades de baloncesto",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ===== MIDDLEWARE DE CLOUDWATCH =====
@app.middleware("http")
async def cloudwatch_middleware(request: Request, call_next):
    """Middleware para capturar métricas de todas las requests y enviarlas a CloudWatch"""
    # Excluir endpoints internos de las métricas
    if request.url.path in ["/metrics", "/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    method = request.method
    endpoint = request.url.path
    start_time = time.time()

    try:
        # Procesar request
        response = await call_next(request)

        # Calcular duración en milisegundos
        duration_ms = (time.time() - start_time) * 1000
        status = response.status_code

        # Publicar múltiples métricas en un solo EMF log (eficiente)
        cw_metrics.put_metrics(
            metrics=[
                {"name": "RequestCount", "value": 1, "unit": MetricUnit.COUNT},
                {"name": "RequestDuration", "value": duration_ms, "unit": MetricUnit.MILLISECONDS},
                {"name": "ErrorCount", "value": 1 if status >= 500 else 0, "unit": MetricUnit.COUNT},
                {"name": "Success", "value": 1 if 200 <= status < 300 else 0, "unit": MetricUnit.COUNT}
            ],
            dimensions={
                "Method": method,
                "Endpoint": endpoint,
                "StatusCode": str(status)
            }
        )

        logger.debug(f"[METRICS] {method} {endpoint} - {status} - {duration_ms:.2f}ms")
        return response

    except Exception as e:
        # Capturar errores y registrar métricas
        duration_ms = (time.time() - start_time) * 1000

        cw_metrics.put_metrics(
            metrics=[
                {"name": "RequestCount", "value": 1, "unit": MetricUnit.COUNT},
                {"name": "ErrorCount", "value": 1, "unit": MetricUnit.COUNT},
                {"name": "RequestDuration", "value": duration_ms, "unit": MetricUnit.MILLISECONDS}
            ],
            dimensions={
                "Method": method,
                "Endpoint": endpoint,
                "StatusCode": "500",
                "ErrorType": type(e).__name__
            }
        )

        logger.error(f"[METRICS] {method} {endpoint} - ERROR: {e}")
        raise

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear directorio de uploads si no existe
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Montar directorio estático para servir archivos (solo si es almacenamiento local)
if settings.FILE_STORAGE_TYPE.value == "local":
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Incluir routers
from app.routers import auth, videos, public

app.include_router(auth.router)
app.include_router(videos.router)
app.include_router(public.router)

# ===== MÉTRICAS DE SISTEMA (Background Task) =====
@app.on_event("startup")
async def start_system_metrics():
    """
    Publica métricas de sistema (CPU, memoria) cada 60 segundos a CloudWatch
    Estas métricas se ejecutan en background para no bloquear requests
    """
    async def publish_system_metrics():
        while True:
            try:
                await asyncio.sleep(60)  # Publicar cada 60 segundos

                # Obtener métricas del proceso Backend
                process_cpu = current_process.cpu_percent(interval=0.1)
                mem_info = current_process.memory_info()
                process_memory_mb = mem_info.rss / (1024 * 1024)  # Convertir a MB
                process_memory_percent = current_process.memory_percent()

                # Obtener métricas del sistema completo
                system_cpu = psutil.cpu_percent(interval=0.1)
                system_memory = psutil.virtual_memory()

                # Publicar todas las métricas de sistema en un solo batch
                cw_metrics.put_metrics(
                    metrics=[
                        {"name": "ProcessCPU", "value": process_cpu, "unit": MetricUnit.PERCENT},
                        {"name": "ProcessMemoryMB", "value": process_memory_mb, "unit": MetricUnit.MEGABYTES},
                        {"name": "ProcessMemoryPercent", "value": process_memory_percent, "unit": MetricUnit.PERCENT},
                        {"name": "SystemCPU", "value": system_cpu, "unit": MetricUnit.PERCENT},
                        {"name": "SystemMemoryPercent", "value": system_memory.percent, "unit": MetricUnit.PERCENT},
                        {"name": "SystemMemoryAvailableMB", "value": system_memory.available / (1024 * 1024), "unit": MetricUnit.MEGABYTES}
                    ],
                    dimensions={"MetricType": "System"}
                )

                logger.debug(f"[SYSTEM METRICS] CPU: {process_cpu:.1f}% | Memory: {process_memory_mb:.1f}MB ({process_memory_percent:.1f}%)")

            except Exception as e:
                logger.error(f"Error publishing system metrics: {e}")

    # Iniciar tarea en background
    asyncio.create_task(publish_system_metrics())
    logger.info("System metrics background task started (60s interval)")

@app.get("/")
def read_root():
    return {
        "message": "ANB Rising Stars Showcase API", 
        "version": "1.0.0",
        "architecture": "DDD + Clean Architecture",
        "docs": "/docs",
        "file_storage": settings.FILE_STORAGE_TYPE.value
    }

@app.get("/metrics")
async def metrics():
    """
    Endpoint de compatibilidad con Prometheus (deprecado)
    Las métricas ahora se publican a CloudWatch automáticamente
    """
    return {
        "message": "Metrics migrated to CloudWatch",
        "namespace": os.getenv("CLOUDWATCH_NAMESPACE", "ANB/Backend"),
        "service": "API",
        "documentation": "Check AWS CloudWatch console for metrics"
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
