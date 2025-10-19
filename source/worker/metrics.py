"""
Módulo centralizado de métricas de Prometheus para Worker
Este módulo usa prometheus_client en modo multiprocess para permitir
que múltiples procesos (FastAPI + Celery workers) compartan métricas.
"""
import os
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, multiprocess, generate_latest

# Directorio para archivos de métricas multiprocess
METRICS_DIR = os.environ.get('PROMETHEUS_MULTIPROC_DIR', '/tmp/prometheus_multiproc')

# Crear directorio si no existe
os.makedirs(METRICS_DIR, exist_ok=True)

# Establecer variable de entorno para prometheus_client
os.environ['PROMETHEUS_MULTIPROC_DIR'] = METRICS_DIR

# Registry para métricas compartidas entre procesos
registry = CollectorRegistry()

# ===== Métricas de Celery =====

# Contadores
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total number of Celery tasks processed',
    ['task_name', 'status']
)

celery_tasks_failed = Counter(
    'celery_tasks_failed_total',
    'Total number of failed Celery tasks',
    ['task_name', 'error_type']
)

# Histogramas para duraciones
celery_task_duration = Histogram(
    'celery_task_duration_seconds',
    'Duration of Celery task execution',
    ['task_name'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800]  # 1s a 30min
)

video_processing_duration = Histogram(
    'video_processing_duration_seconds',
    'Duration of video processing',
    buckets=[5, 10, 30, 60, 120, 300, 600, 1800]
)

# Gauges para estado actual (sin multiprocess - se actualizan desde FastAPI)
celery_active_tasks = Gauge(
    'celery_active_tasks',
    'Number of currently active Celery tasks',
    multiprocess_mode='livesum'
)

celery_reserved_tasks = Gauge(
    'celery_reserved_tasks',
    'Number of reserved Celery tasks',
    multiprocess_mode='livesum'
)

celery_queue_length = Gauge(
    'celery_queue_length',
    'Number of tasks waiting in Redis queue',
    ['queue_name'],
    multiprocess_mode='livesum'
)

# Histograma para tamaños de archivos
video_file_size_bytes = Histogram(
    'video_file_size_bytes',
    'Size of video files being processed',
    buckets=[1e6, 10e6, 50e6, 100e6, 200e6, 500e6, 1e9]  # 1MB a 1GB
)


def generate_multiprocess_metrics():
    """
    Genera métricas desde todos los procesos
    Para usar en el endpoint /metrics de FastAPI
    """
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return generate_latest(registry)
