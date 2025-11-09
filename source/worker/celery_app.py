"""
Configuración de Celery para Worker ANB Rising Stars
Broker: Redis (sin result backend - PostgreSQL es la fuente de verdad)
"""
from celery import Celery
from celery.signals import task_failure, task_success, task_retry, task_prerun, task_postrun, worker_ready
from config import config
import logging
import time

# Configurar logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# ===== MÉTRICAS DE PROMETHEUS =====
# Importar las métricas definidas en main.py para usarlas en los signals
# Esto permite que los signals de Celery actualicen las métricas
task_start_times = {}  # Diccionario para trackear tiempos de inicio

# Crear aplicación Celery
app = Celery('anb_video_processor')

# ===== CONFIGURACIÓN DE CELERY SEGÚN BROKER =====
if config.USE_SQS:
    # ===== CONFIGURACIÓN AWS SQS =====
    logger.info("🚀 Configurando Worker con AWS SQS como broker")
    app.conf.update(
        # ===== BROKER (AWS SQS) =====
        broker_url='sqs://',
        broker_transport_options={
            'region': config.AWS_REGION,
            'predefined_queues': {
                'video_processing': {
                    'url': config.SQS_QUEUE_URL,
                },
                'dlq': {
                    'url': config.SQS_DLQ_URL,
                }
            },
            'polling_interval': 20,  # Long polling (reduce costos)
            'visibility_timeout': 3600,  # 1 hora (tiempo de procesamiento)
        },
        # NO definimos result_backend - PostgreSQL es la fuente de verdad

        # ===== SERIALIZACIÓN =====
        task_serializer='json',
        accept_content=['json'],

        # ===== TIMEZONE =====
        timezone='America/Bogota',
        enable_utc=True,

        # ===== ACKNOWLEDGMENT (Tolerancia a fallos) =====
        task_acks_late=True,
        task_reject_on_worker_lost=True,

        # ===== REINTENTOS =====
        task_default_retry_delay=config.CELERY_TASK_DEFAULT_RETRY_DELAY,
        task_max_retries=config.CELERY_TASK_MAX_RETRIES,

        # ===== TIMEOUTS =====
        task_soft_time_limit=config.TASK_SOFT_TIME_LIMIT,
        task_hard_time_limit=config.TASK_HARD_TIME_LIMIT,

        # ===== RUTAS DE TAREAS (QUEUES) - SQS =====
        task_routes={
            'tasks.video_processor.process_video': {
                'queue': 'video_processing',
            },
            'tasks.video_processor.handle_failed_video': {
                'queue': 'dlq',
            },
        },

        # ===== WORKER =====
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=50,

        # ===== TRACKING =====
        task_track_started=True,
        task_send_sent_event=True,
    )

else:
    # ===== CONFIGURACIÓN REDIS =====
    logger.info("🚀 Configurando Worker con Redis como broker")
    app.conf.update(
        # ===== BROKER (Solo Redis para colas) =====
        broker_url=config.REDIS_URL,
        # NO definimos result_backend - PostgreSQL es la fuente de verdad

        # ===== SERIALIZACIÓN =====
        task_serializer='json',
        accept_content=['json'],

        # ===== TIMEZONE =====
        timezone='America/Bogota',
        enable_utc=True,

        # ===== ACKNOWLEDGMENT (Tolerancia a fallos) =====
        task_acks_late=True,
        task_reject_on_worker_lost=True,

        # ===== REINTENTOS =====
        task_default_retry_delay=config.CELERY_TASK_DEFAULT_RETRY_DELAY,
        task_max_retries=config.CELERY_TASK_MAX_RETRIES,

        # ===== TIMEOUTS =====
        task_soft_time_limit=config.TASK_SOFT_TIME_LIMIT,
        task_hard_time_limit=config.TASK_HARD_TIME_LIMIT,

        # ===== RUTAS DE TAREAS (QUEUES) - Redis =====
        task_routes={
            'tasks.video_processor.process_video': {
                'queue': 'video_processing',
                'routing_key': 'video.process',
            },
            'tasks.video_processor.handle_failed_video': {
                'queue': 'dlq',
                'routing_key': 'video.failed',
            },
        },

        # ===== WORKER =====
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=50,

        # ===== REDIS ESPECÍFICO =====
        broker_transport_options={
            'visibility_timeout': 3600,
            'fanout_prefix': True,
            'fanout_patterns': True,
        },

        # ===== TRACKING =====
        task_track_started=True,
        task_send_sent_event=True,
    )

# ===== SIGNALS (HOOKS PARA LOGGING Y MÉTRICAS) =====

@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Se ejecuta cuando el worker está listo"""
    broker_info = "AWS SQS" if config.USE_SQS else config.REDIS_URL
    logger.info("=" * 60)
    logger.info("🚀 Worker ANB Rising Stars iniciado correctamente")
    logger.info(f"📍 Broker: {broker_info}")
    logger.info(f"📍 Database: {config.DATABASE_URL}")
    logger.info(f"📁 Upload dir: {config.UPLOAD_BASE_DIR}")
    logger.info(f"⚙️  Concurrency: {config.CELERY_WORKER_CONCURRENCY}")
    logger.info("=" * 60)


@task_prerun.connect
def task_prerun_handler(task_id=None, task=None, **kwargs):
    """Hook antes de ejecutar una tarea - trackear tiempo de inicio"""
    task_start_times[task_id] = time.time()


@task_postrun.connect
def task_postrun_handler(task_id=None, task=None, state=None, **kwargs):
    """Hook después de ejecutar una tarea - calcular duración y publicar a CloudWatch"""
    if task_id in task_start_times:
        duration = time.time() - task_start_times[task_id]
        task_name = task.name.split('.')[-1]

        # Publicar duración de la tarea a CloudWatch
        try:
            from metrics import cw_metrics
            from cloudwatch.cloudwatch_metrics import MetricUnit

            cw_metrics.record_histogram(
                histogram_name="TaskDuration",
                value=duration,
                unit=MetricUnit.SECONDS,
                dimensions={"TaskName": task_name}
            )

            logger.debug(f"[METRICS] Task {task_name} duration: {duration:.2f}s")
        except ImportError as e:
            logger.warning(f"Could not import CloudWatch metrics: {e}")

        del task_start_times[task_id]


@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    """Hook cuando una tarea se completa exitosamente"""
    task_name = sender.name.split('.')[-1]
    logger.info(f"✅ Tarea exitosa: {task_name}")

    # Incrementar contador de métricas en CloudWatch
    try:
        from metrics import cw_metrics
        from cloudwatch.cloudwatch_metrics import MetricUnit

        cw_metrics.put_metric(
            metric_name="TaskCount",
            value=1,
            unit=MetricUnit.COUNT,
            dimensions={"TaskName": task_name, "Status": "Success"}
        )
    except ImportError as e:
        logger.warning(f"Could not import CloudWatch metrics: {e}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, **kwargs):
    """Hook cuando una tarea falla"""
    task_name = sender.name.split('.')[-1]
    error_type = type(exception).__name__ if exception else 'Unknown'

    logger.error(f"❌ Tarea fallida: {task_name} (ID: {task_id})")
    logger.error(f"   Error: {exception}")

    # Incrementar contadores de métricas en CloudWatch
    try:
        from metrics import cw_metrics
        from cloudwatch.cloudwatch_metrics import MetricUnit

        # Publicar múltiples métricas de fallo
        cw_metrics.put_metrics(
            metrics=[
                {"name": "TaskCount", "value": 1, "unit": MetricUnit.COUNT},
                {"name": "TaskFailure", "value": 1, "unit": MetricUnit.COUNT}
            ],
            dimensions={
                "TaskName": task_name,
                "Status": "Failed",
                "ErrorType": error_type
            }
        )
    except ImportError as e:
        logger.warning(f"Could not import CloudWatch metrics: {e}")


@task_retry.connect
def task_retry_handler(sender=None, reason=None, **kwargs):
    """Hook cuando una tarea se reintenta"""
    task_name = sender.name.split('.')[-1]
    logger.warning(f"🔄 Reintentando tarea: {task_name}")
    logger.warning(f"   Razón: {reason}")

    # Incrementar contador de métricas en CloudWatch
    try:
        from metrics import cw_metrics
        from cloudwatch.cloudwatch_metrics import MetricUnit

        cw_metrics.put_metric(
            metric_name="TaskCount",
            value=1,
            unit=MetricUnit.COUNT,
            dimensions={"TaskName": task_name, "Status": "Retry"}
        )
    except ImportError as e:
        logger.warning(f"Could not import CloudWatch metrics: {e}")


# ===== IMPORTAR TAREAS =====
# Debe estar al final para evitar imports circulares
try:
    from tasks import video_processor  # noqa
    logger.info("✅ Tareas importadas correctamente")
except ImportError as e:
    logger.error(f"❌ Error importando tareas: {e}")

