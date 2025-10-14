"""
Tarea principal de procesamiento de videos ANB Rising Stars
"""
import os
import logging
from datetime import datetime
from typing import Dict
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from celery_app import app
from database import get_db_session
from models import Video
from utils.video_processing import video_processor, VideoProcessingError
from config import config

logger = logging.getLogger(__name__)


class VideoProcessingTask(Task):
    """Clase base para tareas de procesamiento de video con manejo de errores"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Hook ejecutado cuando la tarea falla definitivamente"""
        video_id = args[0] if args else None
        logger.error(f"❌ Tarea {task_id} falló definitivamente para video {video_id}")
        logger.error(f"   Excepción: {exc}")
        
        # Enviar a Dead Letter Queue
        if video_id:
            handle_failed_video.delay(video_id, str(exc), task_id)
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Hook ejecutado cuando la tarea se reintenta"""
        video_id = args[0] if args else None
        logger.warning(f"🔄 Reintentando tarea {task_id} para video {video_id}")


@app.task(
    bind=True,
    base=VideoProcessingTask,
    name='tasks.video_processor.process_video',
    autoretry_for=(Exception,),
    retry_backoff=True,           # Backoff exponencial: 60s, 120s, 240s
    retry_backoff_max=600,        # Máximo 10 minutos entre reintentos
    retry_jitter=True,            # Agregar jitter para evitar thundering herd
    max_retries=config.CELERY_TASK_MAX_RETRIES,
    soft_time_limit=config.TASK_SOFT_TIME_LIMIT,
    time_limit=config.TASK_HARD_TIME_LIMIT,
)
def process_video(self, video_id: int) -> Dict:
    """
    Tarea principal de procesamiento de video
    
    Flujo:
    1. Consultar video desde PostgreSQL
    2. Validar que existe el archivo original
    3. Actualizar estado a 'processing'
    4. Procesar video con FFmpeg:
       - Recortar a 30s
       - Escalar a 720p 16:9
       - Agregar logo ANB
       - Eliminar audio
    5. Guardar video procesado
    6. Actualizar PostgreSQL: status='processed', processed_path, processed_at
    
    Args:
        video_id: ID del video en la base de datos
    
    Returns:
        Diccionario con resultado del procesamiento
    
    Raises:
        VideoProcessingError: Si falla el procesamiento
        SoftTimeLimitExceeded: Si excede el tiempo límite
    """
    db = None
    temp_files = []
    
    try:
        logger.info(f"🎬 Iniciando procesamiento de video ID: {video_id}")
        logger.info(f"   Task ID: {self.request.id}")
        logger.info(f"   Intento: {self.request.retries + 1}/{self.max_retries + 1}")
        
        # ===== 1. CONSTRUIR RUTA DEL ARCHIVO (CONVENCIÓN) =====
        # El worker NO consulta la BD para saber dónde está el archivo
        # Usa convención: /app/uploads/original/{video_id}.mp4
        original_path = os.path.join(config.ORIGINAL_DIR, f"{video_id}.mp4")
        
        logger.info(f"📂 Ruta esperada del video: {original_path}")
        
        # Validar que el archivo existe
        if not os.path.exists(original_path):
            error_msg = f"Archivo original no encontrado: {original_path}"
            logger.error(f"❌ {error_msg}")
            raise VideoProcessingError(error_msg)
        
        logger.info(f"✅ Archivo encontrado en almacenamiento")
        
        # ===== 2. CONECTAR A BD Y ACTUALIZAR ESTADO =====
        db = get_db_session()
        video = db.query(Video).filter(Video.id == video_id).first()
        
        if not video:
            error_msg = f"Video {video_id} no encontrado en base de datos"
            logger.error(f"❌ {error_msg}")
            raise VideoProcessingError(error_msg)
        
        logger.info(f"📹 Video encontrado en BD: '{video.title}'")
        logger.info(f"   Usuario: {video.user_id}")
        logger.info(f"   Estado actual: {video.status}")
        
        # ===== 3. ACTUALIZAR ESTADO A 'PROCESSING' =====
        video.status = "processing"
        video.task_id = self.request.id
        video.retry_count = self.request.retries
        db.commit()
        logger.info("✅ Estado actualizado a 'processing'")
        
        # ===== 4. PROCESAR VIDEO CON FFMPEG =====
        
        # Definir ruta de salida (también por convención)
        video_filename = f"{video_id}_processed.mp4"
        processed_path = os.path.join(config.PROCESSED_DIR, video_filename)
        
        # Procesar video
        logger.info("⚙️ Procesando con FFmpeg...")
        video_processor.process_video(
            input_path=original_path,  # Usa la ruta construida, no de BD
            output_path=processed_path,
            add_logo=True
        )
        
        temp_files.append(processed_path)
        
        # Validar video procesado
        if not video_processor.validate_video(processed_path):
            logger.warning("⚠️ Video procesado no cumple todas las validaciones")
        
        # ===== 5. AGREGAR CORTINILLAS (OPCIONAL) =====
        # Si existen archivos de intro/outro, agregarlos
        if os.path.exists(config.INTRO_VIDEO_PATH) or os.path.exists(config.OUTRO_VIDEO_PATH):
            logger.info("🎬 Agregando cortinillas...")
            final_path = os.path.join(config.PROCESSED_DIR, f"{video_id}_final.mp4")
            
            video_processor.add_intro_outro(
                video_path=processed_path,
                output_path=final_path
            )
            
            # Usar el video final
            if os.path.exists(final_path):
                processed_path = final_path
                temp_files.append(final_path)
        
        # ===== 6. ACTUALIZAR BASE DE DATOS =====
        video.status = "processed"
        video.processed_path = processed_path
        video.processed_at = datetime.utcnow()
        video.error_message = None  # Limpiar errores previos
        
        # Obtener duración del video procesado
        video_info = video_processor.get_video_info(processed_path)
        video.processed_duration = int(video_info['duration'])
        
        db.commit()
        
        logger.info("=" * 60)
        logger.info(f"✅ Video {video_id} procesado exitosamente")
        logger.info(f"   Path procesado: {processed_path}")
        logger.info(f"   Duración: {video.processed_duration}s")
        logger.info(f"   Tiempo total: ~{(datetime.utcnow() - video.uploaded_at).seconds}s")
        logger.info("=" * 60)
        
        return {
            "status": "success",
            "video_id": video_id,
            "processed_path": processed_path,
            "duration": video.processed_duration,
            "task_id": self.request.id
        }
    
    except SoftTimeLimitExceeded:
        logger.error(f"⏱️ Tiempo límite excedido para video {video_id}")
        if db and video:
            video.status = "failed"
            video.error_message = "Tiempo límite de procesamiento excedido"
            db.commit()
        raise
    
    except VideoProcessingError as e:
        logger.error(f"❌ Error de procesamiento: {e}")
        if db and video:
            video.error_message = str(e)
            video.retry_count = self.request.retries
            db.commit()
        raise
    
    except Exception as e:
        logger.error(f"❌ Error inesperado procesando video {video_id}: {e}")
        if db and video:
            video.error_message = f"Error inesperado: {str(e)}"
            video.retry_count = self.request.retries
            db.commit()
        raise
    
    finally:
        # Cerrar sesión de BD
        if db:
            db.close()
        
        # Limpiar archivos temporales (opcional)
        # for temp_file in temp_files:
        #     if os.path.exists(temp_file):
        #         os.remove(temp_file)


@app.task(
    name='tasks.video_processor.handle_failed_video',
    queue='dlq'
)
def handle_failed_video(video_id: int, error_message: str, original_task_id: str):
    """
    Dead Letter Queue - Maneja videos que fallaron definitivamente
    
    Esta tarea se ejecuta cuando un video falla después de todos los reintentos.
    Aquí puedes:
    - Notificar al usuario
    - Loggear para análisis
    - Mover a una cola de revisión manual
    - Generar alertas
    
    Args:
        video_id: ID del video
        error_message: Mensaje de error
        original_task_id: ID de la tarea original que falló
    """
    logger.error("=" * 60)
    logger.error(f"💀 DLQ: Video {video_id} falló definitivamente")
    logger.error(f"   Task original: {original_task_id}")
    logger.error(f"   Error: {error_message}")
    logger.error("=" * 60)
    
    db = None
    try:
        db = get_db_session()
        video = db.query(Video).filter(Video.id == video_id).first()
        
        if video:
            video.status = "failed"
            video.error_message = f"Falló después de {config.CELERY_TASK_MAX_RETRIES} reintentos: {error_message}"
            db.commit()
            
            logger.info(f"✅ Video {video_id} marcado como 'failed' en base de datos")
            
            # Aquí podrías:
            # - Enviar email al usuario
            # - Enviar notificación a Slack/Discord
            # - Crear ticket en sistema de soporte
            # - Guardar en tabla de videos_fallidos para revisión manual
        
    except Exception as e:
        logger.error(f"❌ Error en DLQ para video {video_id}: {e}")
    
    finally:
        if db:
            db.close()


@app.task(name='tasks.video_processor.cleanup_temp_files')
def cleanup_temp_files():
    """
    Tarea periódica para limpiar archivos temporales antiguos
    Se puede ejecutar con Celery Beat
    """
    try:
        temp_dir = config.TEMP_DIR
        logger.info(f"🧹 Limpiando archivos temporales en {temp_dir}")
        
        # Limpiar archivos más viejos de 1 hora
        import time
        current_time = time.time()
        deleted_count = 0
        
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > 3600:  # 1 hora
                    os.remove(file_path)
                    deleted_count += 1
        
        logger.info(f"✅ {deleted_count} archivos temporales eliminados")
        
    except Exception as e:
        logger.error(f"❌ Error limpiando archivos temporales: {e}")

