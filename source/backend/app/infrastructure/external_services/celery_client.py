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

# Configuración mínima para cliente
celery_app.conf.update(
    broker_url=settings.REDIS_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Bogota',
    enable_utc=True,
    # No necesitamos result_backend para el cliente
    task_ignore_result=True,
    # Configuración de envío
    task_default_retry_delay=60,
    task_max_retries=3,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Configurar rutas de tareas (debe coincidir con el worker)
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
            result = celery_app.send_task(
                'tasks.video_processor.process_video',
                args=[video_id],
                queue='video_processing',
                routing_key='video.process'
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

