"""
Cliente Celery para el Backend ANB Rising Stars
Solo para publicar tareas, no para procesarlas
"""
from celery import Celery
from app.config.settings import settings
from app.shared.interfaces.task_queue import TaskQueueInterface
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Crear aplicación Celery (solo cliente)
celery_app = Celery('anb_backend_client')

# Configuración según broker (Redis o SQS)
if settings.USE_SQS:
    # ===== CONFIGURACIÓN AWS SQS =====
    logger.info("🚀 Configurando Celery con AWS SQS como broker")
    celery_app.conf.update(
        broker_url='sqs://',
        broker_transport_options={
            'region': settings.AWS_REGION,
            'predefined_queues': {
                'video_processing': {
                    'url': settings.SQS_QUEUE_URL,
                },
                'dlq': {
                    'url': settings.SQS_DLQ_URL,
                }
            },
            'polling_interval': 20,  # Long polling (reduce costos)
            'visibility_timeout': 3600,  # 1 hora (tiempo de procesamiento)
        },
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='America/Bogota',
        enable_utc=True,
        task_ignore_result=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
    )

    # Configurar rutas de tareas para SQS
    celery_app.conf.task_routes = {
        'tasks.video_processor.process_video': {
            'queue': 'video_processing',
        },
    }

else:
    # ===== CONFIGURACIÓN REDIS =====
    logger.info("🚀 Configurando Celery con Redis como broker")
    celery_app.conf.update(
        broker_url=settings.REDIS_URL,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='America/Bogota',
        enable_utc=True,
        task_ignore_result=True,
        task_default_retry_delay=60,
        task_max_retries=3,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
    )

    # Configurar rutas de tareas para Redis
    celery_app.conf.task_routes = {
        'tasks.video_processor.process_video': {
            'queue': 'video_processing',
            'routing_key': 'video.process',
        },
    }

class CeleryTaskQueue(TaskQueueInterface):
    """Implementación de TaskQueueInterface usando Celery"""
    
    async def publish_video_processing_task(self, video_id: int) -> str:
        """
        Publica una tarea de procesamiento de video a la cola

        Args:
            video_id: ID del video a procesar

        Returns:
            Task ID de la tarea publicada
        """
        try:
            # Enviar tarea a la cola
            # Para SQS: routing_key se ignora (solo usa queue)
            # Para Redis: routing_key se respeta
            task_params = {
                'args': [video_id],
                'queue': 'video_processing',
            }

            # Solo agregar routing_key si usamos Redis
            if not settings.USE_SQS:
                task_params['routing_key'] = 'video.process'

            result = celery_app.send_task(
                'tasks.video_processor.process_video',
                **task_params
            )

            logger.info(f"✅ Tarea de procesamiento publicada para video {video_id}")
            logger.info(f"   Task ID: {result.id}")
            logger.info(f"   Queue: video_processing")

            return result.id

        except Exception as e:
            logger.error(f"❌ Error publicando tarea para video {video_id}: {e}")
            raise
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de una tarea
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            Diccionario con el estado de la tarea
        """
        try:
            result = celery_app.AsyncResult(task_id)
            return {
                'task_id': task_id,
                'status': result.status,
                'result': result.result if result.ready() else None,
                'ready': result.ready(),
                'successful': result.successful() if result.ready() else False,
                'failed': result.failed() if result.ready() else False,
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo estado de tarea {task_id}: {e}")
            return {
                'task_id': task_id,
                'status': 'UNKNOWN',
                'error': str(e)
            }


# Instancia global para compatibilidad con código existente
def publish_video_processing_task(video_id: int) -> str:
    """Función de conveniencia para mantener compatibilidad"""
    task_queue = CeleryTaskQueue()
    return task_queue.publish_video_processing_task(video_id)

