from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import time
import os
import asyncio
import logging
import psutil

# Configurar logger
logger = logging.getLogger(__name__)

# Importar configuración del contenedor
from app.config.container_config import configure_container
from app.config.settings import settings

# ===== MÉTRICAS DE PROMETHEUS =====
# Definir métricas manualmente (igual que en worker)
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress'
)

# Métricas de sistema
process_cpu_usage = Gauge(
    'process_cpu_usage_percent',
    'CPU usage percentage of the backend process'
)

process_memory_usage = Gauge(
    'process_memory_usage_bytes',
    'Memory usage in bytes of the backend process'
)

process_memory_percent = Gauge(
    'process_memory_usage_percent',
    'Memory usage percentage of the backend process'
)

system_cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System-wide CPU usage percentage'
)

system_memory_usage = Gauge(
    'system_memory_usage_percent',
    'System-wide memory usage percentage'
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

# ===== MIDDLEWARE DE PROMETHEUS =====
@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """Middleware para capturar métricas de todas las requests"""
    # Excluir el endpoint /metrics de las métricas
    if request.url.path == "/metrics":
        return await call_next(request)

    method = request.method
    endpoint = request.url.path

    # Incrementar contador de requests en progreso
    http_requests_in_progress.inc()
    current_value = http_requests_in_progress._value.get()
    logger.info(f"[METRICS DEBUG] Incremented gauge. Current value: {current_value}. Path: {endpoint}")

    # Iniciar timer
    start_time = time.time()

    try:
        # Procesar request
        response = await call_next(request)

        # Calcular duración
        duration = time.time() - start_time

        # Registrar métricas
        status = response.status_code
        http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
        http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)

        return response
    finally:
        # Decrementar contador de requests en progreso (siempre se ejecuta)
        http_requests_in_progress.dec()
        current_value = http_requests_in_progress._value.get()
        logger.info(f"[METRICS DEBUG] Decremented gauge. Current value: {current_value}. Path: {endpoint}")

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

# ===== ENDPOINT DE MÉTRICAS =====
@app.get("/metrics")
async def metrics():
    """Endpoint para exponer métricas de Prometheus"""
    try:
        # Actualizar métricas del proceso actual
        process_cpu_usage.set(current_process.cpu_percent(interval=0.1))

        mem_info = current_process.memory_info()
        process_memory_usage.set(mem_info.rss)  # RSS = Resident Set Size (memoria física)
        process_memory_percent.set(current_process.memory_percent())

        # Actualizar métricas del sistema completo
        system_cpu_usage.set(psutil.cpu_percent(interval=0.1))
        system_memory_usage.set(psutil.virtual_memory().percent)

    except Exception as e:
        logger.warning(f"Error actualizando métricas de sistema: {e}")

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/")
def read_root():
    return {
        "message": "ANB Rising Stars Showcase API", 
        "version": "1.0.0",
        "architecture": "DDD + Clean Architecture",
        "docs": "/docs",
        "file_storage": settings.FILE_STORAGE_TYPE.value
    }

@app.get("/test-gauge")
async def test_gauge():
    """Endpoint de prueba para verificar que el gauge funciona"""
    http_requests_in_progress.inc()
    await asyncio.sleep(5)  # Mantener incrementado por 5 segundos
    http_requests_in_progress.dec()
    return {"message": "Gauge test completed"}

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
