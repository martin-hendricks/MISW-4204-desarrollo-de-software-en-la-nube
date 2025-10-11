from celery import current_task
from sqlalchemy.orm import sessionmaker
from app.celery_app import celery_app
from app.db.database import engine
from app.models.models import Video, Task
from app.file_storage import get_file_url, file_exists
from app.crud import update_video_status, update_task_status, get_video_by_id
from app.schemas.schemas import TaskStatus
import os
import time

# Crear sesión de base de datos para las tareas
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@celery_app.task(bind=True)
def process_video(self, video_id: int):
    """
    Tarea asíncrona para procesar un video
    En una implementación real, aquí se haría el procesamiento real del video
    """
    db = SessionLocal()
    
    try:
        # Obtener el video
        video = get_video_by_id(db, video_id)
        if not video:
            raise Exception(f"Video {video_id} no encontrado")
        
        # Actualizar estado de la tarea a procesando
        update_task_status(
            db, 
            self.request.id, 
            TaskStatus.PROCESSING, 
            progress=0.0
        )
        
        # Simular procesamiento del video
        # En una implementación real, aquí se procesaría el video con FFmpeg, etc.
        total_steps = 10
        for step in range(total_steps):
            # Simular trabajo
            time.sleep(2)
            
            # Actualizar progreso
            progress = (step + 1) / total_steps * 100
            update_task_status(
                db, 
                self.request.id, 
                TaskStatus.PROCESSING, 
                progress=progress
            )
            
            # Actualizar el progreso de la tarea en Celery
            current_task.update_state(
                state='PROGRESS',
                meta={'current': step + 1, 'total': total_steps, 'status': 'Procesando video...'}
            )
        
        # Verificar que el archivo existe
        if not file_exists(video.filename):
            raise Exception("Archivo de video no encontrado")
        
        # Generar URLs
        original_url = get_file_url(video.filename)
        processed_url = get_file_url(f"processed_{video.filename}")
        
        # Actualizar el video como procesado
        update_video_status(
            db, 
            video_id, 
            "processed", 
            original_url=original_url,
            processed_url=processed_url
        )
        
        # Marcar tarea como completada
        update_task_status(
            db, 
            self.request.id, 
            TaskStatus.COMPLETED, 
            progress=100.0
        )
        
        return {
            'status': 'Video procesado exitosamente',
            'video_id': video_id,
            'original_url': original_url,
            'processed_url': processed_url
        }
        
    except Exception as exc:
        # Marcar tarea como fallida
        update_task_status(
            db, 
            self.request.id, 
            TaskStatus.FAILED, 
            error_message=str(exc)
        )
        
        # Actualizar el video como fallido
        update_video_status(db, video_id, "failed")
        
        # Re-lanzar la excepción para que Celery la maneje
        raise self.retry(exc=exc, countdown=60, max_retries=3)
    
    finally:
        db.close()


@celery_app.task
def cleanup_old_files():
    """
    Tarea para limpiar archivos antiguos
    """
    # Implementar lógica de limpieza si es necesario
    pass


@celery_app.task
def generate_thumbnails(video_id: int):
    """
    Tarea para generar miniaturas de videos
    """
    # Implementar generación de miniaturas si es necesario
    pass
