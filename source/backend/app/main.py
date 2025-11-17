from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import time
import os
import asyncio
import logging
import sys
import random

# Configurar logger
logger = logging.getLogger(__name__)

# Importar configuración del contenedor
from app.config.container_config import configure_container
from app.config.settings import settings

# ===== MÉTRICAS DE CLOUDWATCH =====
# Agregar directorio cloudwatch al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from cloudwatch.cloudwatch_metrics import MetricUnit
import boto3

# Constantes para CloudWatch
CLOUDWATCH_NAMESPACE = "ANB/Backend"
CLOUDWATCH_SERVICE = "API"

# Inicializar cliente CloudWatch directo (sin metadata de instancia)
cw_client = boto3.client('cloudwatch', region_name=os.getenv('AWS_REGION', 'us-east-1'))

# Crear la aplicación FastAPI
app = FastAPI(
    title="ANB Rising Stars Showcase API",
    description="API REST con arquitectura DDD - Gestión de videos de habilidades de baloncesto",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ===== MIDDLEWARE DE CLOUDWATCH =====
# Configuración de sampling para optimización de costos
EXCLUDED_PATHS = {"/metrics", "/docs", "/redoc", "/openapi.json"}
SAMPLED_PATHS = {"/health": 0.1, "/": 0.2}  # path: sample_rate (0.1 = 10%, 0.2 = 20%)

@app.middleware("http")
async def cloudwatch_middleware(request: Request, call_next):
    """
    Middleware para capturar métricas de todas las requests y enviarlas a CloudWatch

    Optimizaciones de costos implementadas:
    - Excluye endpoints internos (/metrics, /docs, /redoc, /openapi.json)
    - Sampling en endpoints de health check (10% de requests)
    - Sampling en endpoint raíz (20% de requests)
    """
    path = request.url.path

    # Excluir endpoints internos de las métricas completamente
    if path in EXCLUDED_PATHS:
        return await call_next(request)

    # Aplicar sampling para endpoints de alta frecuencia
    if path in SAMPLED_PATHS:
        sample_rate = SAMPLED_PATHS[path]
        if random.random() > sample_rate:
            # Skip métrica (solo procesar el request)
            return await call_next(request)

    method = request.method
    endpoint = path
    start_time = time.time()

    try:
        # Procesar request
        response = await call_next(request)

        # Calcular duración en milisegundos
        duration_ms = (time.time() - start_time) * 1000
        status = response.status_code

        # Publicar métricas SIN metadata de instancia (solo dimensiones esenciales)
        cw_client.put_metric_data(
            Namespace=CLOUDWATCH_NAMESPACE,
            MetricData=[
                {
                    'MetricName': 'RequestCount',
                    'Value': 1,
                    'Unit': MetricUnit.COUNT.value,
                    'Dimensions': [
                        {"Name": "Method", "Value": method},
                        {"Name": "Endpoint", "Value": endpoint},
                        {"Name": "StatusCode", "Value": str(status)}
                    ]
                },
                {
                    'MetricName': 'RequestDuration',
                    'Value': duration_ms,
                    'Unit': MetricUnit.MILLISECONDS.value,
                    'Dimensions': [
                        {"Name": "Method", "Value": method},
                        {"Name": "Endpoint", "Value": endpoint}
                    ]
                }
            ]
        )

        logger.debug(f"[METRICS] {method} {endpoint} - {status} - {duration_ms:.2f}ms")
        return response

    except Exception as e:
        # Capturar errores y registrar métricas
        duration_ms = (time.time() - start_time) * 1000

        # Publicar métricas SIN metadata de instancia
        cw_client.put_metric_data(
            Namespace=CLOUDWATCH_NAMESPACE,
            MetricData=[
                {
                    'MetricName': 'RequestCount',
                    'Value': 1,
                    'Unit': MetricUnit.COUNT.value,
                    'Dimensions': [
                        {"Name": "Method", "Value": method},
                        {"Name": "Endpoint", "Value": endpoint},
                        {"Name": "StatusCode", "Value": "500"}
                    ]
                },
                {
                    'MetricName': 'ErrorCount',
                    'Value': 1,
                    'Unit': MetricUnit.COUNT.value,
                    'Dimensions': [
                        {"Name": "Method", "Value": method},
                        {"Name": "Endpoint", "Value": endpoint},
                        {"Name": "ErrorType", "Value": type(e).__name__}
                    ]
                },
                {
                    'MetricName': 'RequestDuration',
                    'Value': duration_ms,
                    'Unit': MetricUnit.MILLISECONDS.value,
                    'Dimensions': [
                        {"Name": "Method", "Value": method},
                        {"Name": "Endpoint", "Value": endpoint}
                    ]
                }
            ]
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

# ===== HEARTBEAT METRICS (Background Task) =====
@app.on_event("startup")
async def start_heartbeat_metrics():
    """
    Publica heartbeat cada 5 minutos para confirmar que el servicio está activo

    NOTA: Métricas de CPU/Memoria del sistema se obtienen de EC2 CloudWatch (gratuitas).
    Para habilitar métricas detalladas de memoria en EC2:
    - Instalar CloudWatch Agent en la instancia
    - Las métricas aparecerán en namespace CWAgent
    """
    async def publish_heartbeat():
        while True:
            try:
                await asyncio.sleep(300)  # Publicar cada 5 minutos (optimizado para costos)

                # Solo publicar heartbeat para confirmar que el servicio está activo
                cw_client.put_metric_data(
                    Namespace=CLOUDWATCH_NAMESPACE,
                    MetricData=[{
                        'MetricName': 'ServiceHeartbeat',
                        'Value': 1,
                        'Unit': MetricUnit.COUNT.value,
                        'Dimensions': [{"Name": "MetricType", "Value": "Health"}]
                    }]
                )

                logger.debug(f"[HEARTBEAT] Service is alive")

            except Exception as e:
                logger.error(f"Error publishing heartbeat: {e}")

    # Iniciar tarea en background
    asyncio.create_task(publish_heartbeat())
    logger.info("Heartbeat metrics background task started (5min interval - cost optimized)")

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
