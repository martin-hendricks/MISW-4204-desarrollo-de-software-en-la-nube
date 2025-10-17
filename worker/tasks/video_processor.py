"""
Tarea principal de procesamiento de videos ANB Rising Stars
"""

import logging

import os
from typing import Dict

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from celery_app import app

from database import get_db_session
from datetime import datetime
from models import Video, VideoStatus
from utils.video_processing import video_processor, VideoProcessingError
from config import config
from models import Video, VideoStatus
from utils.video_processing import VideoProcessingError, video_processor

from database import get_db_session

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
    name="tasks.video_processor.process_video",
    autoretry_for=(Exception,),
    retry_backoff=True,  # Backoff exponencial: 60s, 120s, 240s
    retry_backoff_max=600,  # Máximo 10 minutos entre reintentos
    retry_jitter=True,  # Agregar jitter para evitar thundering herd
    max_retries=config.CELERY_TASK_MAX_RETRIES,
    soft_time_limit=config.TASK_SOFT_TIME_LIMIT,
    time_limit=config.TASK_HARD_TIME_LIMIT,
)
def process_video(self, video_id: int) -> Dict:
    """
    Tarea principal de procesamiento de video

    Flujo OPTIMIZADO (sin consultas innecesarias a BD):
    1. Construir rutas por convención: /app/uploads/original/{video_id}.mp4
    2. Validar que el archivo original existe (File System directo)
    3. Procesar video con FFmpeg:
       - Recortar a 30s
       - Escalar a 720p 16:9
       - Agregar logo ANB
       - Eliminar audio
    4. Agregar cortinillas (intro/outro) si existen
    5. SOLO DESPUÉS actualizar PostgreSQL con el resultado:
       - status='processed'
       - processed_url='/api/videos/{id}/download'
       - processed_at=NOW()

    IMPORTANTE: El worker NO consulta la BD antes de procesar.
    Solo usa el video_id para construir las rutas y actualizar el resultado.

    Args:
        video_id: ID del video (se usa para construir rutas por convención)

    Returns:
        Diccionario con resultado del procesamiento

    Raises:
        VideoProcessingError: Si falla el procesamiento
        SoftTimeLimitExceeded: Si excede el tiempo límite
    """
    temp_files = []

    try:
        logger.info(f"🎬 Iniciando procesamiento de video ID: {video_id}")
        logger.info(f"   Task ID: {self.request.id}")
        logger.info(f"   Intento: {self.request.retries + 1}/{self.max_retries + 1}")

        # ===== 1. CONSTRUIR RUTAS POR CONVENCIÓN (SIN CONSULTAR BD) =====
        # El worker NO consulta la BD para saber dónde están los archivos
        # Usa convención: /app/uploads/original/{video_id}.mp4
        original_path = os.path.join(config.ORIGINAL_DIR, f"{video_id}.mp4")
        processed_path = os.path.join(config.PROCESSED_DIR, f"{video_id}.mp4")

        logger.info(f"📂 Ruta original:  {original_path}")
        logger.info(f"📂 Ruta procesada: {processed_path}")

        # ===== 2. VALIDAR QUE EL ARCHIVO ORIGINAL EXISTE =====
        if not os.path.exists(original_path):
            error_msg = f"Archivo original no encontrado: {original_path}"
            logger.error(f"❌ {error_msg}")
            raise VideoProcessingError(error_msg)

        logger.info("✅ Archivo original encontrado en almacenamiento")

        # ===== 3. PROCESAR VIDEO CON FFMPEG =====

        logger.info("⚙️ Procesando con FFmpeg...")
        video_processor.process_video(
            input_path=original_path, output_path=processed_path, add_logo=True
        )

        temp_files.append(processed_path)
        logger.info(f"✅ Video procesado: {processed_path}")

        # Validar video procesado
        if not video_processor.validate_video(processed_path):
            logger.warning("⚠️ Video procesado no cumple todas las validaciones")

        # ===== 4. AGREGAR CORTINILLAS (OPCIONAL) =====
        # Si existen archivos de intro/outro, agregarlos
        if os.path.exists(config.INTRO_VIDEO_PATH) or os.path.exists(
            config.OUTRO_VIDEO_PATH
        ):
            logger.info("🎬 Agregando cortinillas...")
            # Crear archivo temporal para video con cortinillas
            temp_with_intros = os.path.join(config.TEMP_DIR, f"{video_id}_with_intros.mp4")

            video_processor.add_intro_outro(
                video_path=processed_path, output_path=temp_with_intros
            )

            # Reemplazar el archivo procesado con el que tiene cortinillas
            if os.path.exists(temp_with_intros):
                # Eliminar el archivo sin cortinillas
                if os.path.exists(processed_path):
                    os.remove(processed_path)
                    logger.info(f"🗑️  Eliminado archivo sin cortinillas: {processed_path}")
                
                # Mover el archivo con cortinillas al nombre final
                os.rename(temp_with_intros, processed_path)
                logger.info(f"✅ Cortinillas agregadas y archivo final: {processed_path}")
            else:
                logger.warning("⚠️ No se pudo agregar cortinillas, usando video sin cortinillas")

        # ===== 5. ACTUALIZAR BASE DE DATOS CON RESULTADO =====
        # SOLO AHORA consultamos la BD para actualizar el resultado
        db = get_db_session()
        video = db.query(Video).filter(Video.id == video_id).first()

        if not video:
            logger.warning(
                f"⚠️ Video {video_id} no encontrado en BD, pero el archivo fue procesado"
            )
            logger.info(f"   Archivo procesado guardado en: {processed_path}")
            db.close()  # Cerrar sesión antes de salir
            # El video fue procesado exitosamente aunque no esté en BD
            return {
                "status": "success",
                "video_id": video_id,
                "processed_path": processed_path,
                "warning": "Video no encontrado en BD",
            }

        # Actualizar registro en BD
        video.status = VideoStatus.processed  # SQLAlchemy maneja el enum automáticamente
        video.processed_at = datetime.utcnow()
        
        # Generar URL pública para el video procesado
        # El backend puede servir el archivo desde /app/uploads/processed/{video_id}_processed.mp4
        # Ejemplo: https://anb.com/api/videos/{video_id}/download
        base_path = os.getenv("BASE_PATH", "http://localhost:80/api/videos")
        video.processed_url = f"{base_path}/processed/{video_id}"

        # Campos que NO existen en init.sql:
        # - processed_path (ruta interna, el worker la conoce por convención)
        # - processed_duration (metadata)
        # - error_message (para errores)

        db.commit()

        # Obtener info del video para logging
        video_info = video_processor.get_video_info(processed_path)
        duration = int(video_info["duration"])

        logger.info("=" * 60)
        logger.info(f"✅ Video {video_id} procesado exitosamente")
        logger.info(f"   Path procesado: {processed_path}")
        logger.info(f"   Duración: {duration}s")
        logger.info(f"   URL pública: {video.processed_url}")
        # Calcular tiempo total de procesamiento (manejar timezone)
        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        if video.uploaded_at.tzinfo is None:
            # Si uploaded_at es naive, asumir UTC
            uploaded_utc = video.uploaded_at.replace(tzinfo=timezone.utc)
        else:
            uploaded_utc = video.uploaded_at
        processing_time = (now_utc - uploaded_utc).total_seconds()
        logger.info(f"   Tiempo total: ~{int(processing_time)}s")
        logger.info("=" * 60)
        
        db.close()  # Cerrar sesión antes de salir

        return {
            "status": "success",
            "video_id": video_id,
            "processed_path": processed_path,
            "duration": duration,
            "task_id": self.request.id,
        }

    except SoftTimeLimitExceeded:
        logger.error(f"⏱️ Tiempo límite excedido para video {video_id}")
        logger.error("   Razón: Tiempo límite de procesamiento excedido")

        # NOTA: El ENUM video_status en init.sql solo tiene 'uploaded' y 'processed'
        # NO existe 'failed', por lo tanto NO actualizamos la BD
        # El video permanecerá en estado 'uploaded' cuando falle
        if self.request.retries >= self.max_retries:
            logger.warning(f"💀 Video {video_id} falló definitivamente")
            logger.warning(f"   El video permanece en estado 'uploaded' en la BD")
            logger.warning(f"   Para agregar estado 'failed': ALTER TYPE video_status ADD VALUE 'failed';")
        raise

    except VideoProcessingError as e:
        logger.error(f"❌ Error de procesamiento: {e}")
        logger.error(f"   Intento: {self.request.retries + 1}/{self.max_retries + 1}")

        # NOTA: El ENUM video_status en init.sql solo tiene 'uploaded' y 'processed'
        # NO existe 'failed', por lo tanto NO actualizamos la BD
        # El video permanecerá en estado 'uploaded' cuando falle
        if self.request.retries >= self.max_retries:
            logger.warning(f"💀 Video {video_id} falló definitivamente")
            logger.warning(f"   El video permanece en estado 'uploaded' en la BD")
            logger.warning(f"   Para agregar estado 'failed': ALTER TYPE video_status ADD VALUE 'failed';")
        raise

    except Exception as e:
        logger.error(f"❌ Error inesperado procesando video {video_id}: {e}")
        logger.error(f"   Intento: {self.request.retries + 1}/{self.max_retries + 1}")

        # NOTA: El ENUM video_status en init.sql solo tiene 'uploaded' y 'processed'
        # NO existe 'failed', por lo tanto NO actualizamos la BD
        # El video permanecerá en estado 'uploaded' cuando falle
        if self.request.retries >= self.max_retries:
            logger.warning(f"💀 Video {video_id} falló definitivamente")
            logger.warning(f"   El video permanece en estado 'uploaded' en la BD")
            logger.warning(f"   Para agregar estado 'failed': ALTER TYPE video_status ADD VALUE 'failed';")
        raise

    finally:
        # Limpiar archivos temporales (opcional)
        # for temp_file in temp_files:
        #     if os.path.exists(temp_file):
        #         os.remove(temp_file)

        logger.info(f"🧹 Procesamiento finalizado para video {video_id}")


@app.task(name="tasks.video_processor.handle_failed_video", queue="dlq")
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
        # NOTA: El ENUM video_status en init.sql solo tiene 'uploaded' y 'processed'
        # No existe 'failed', por lo que no podemos actualizar el status en BD
        # El video permanecerá en estado 'uploaded'
        
        logger.warning(f"⚠️ Video {video_id} falló definitivamente")
        logger.warning(
            f"   Razón: Falló después de {config.CELERY_TASK_MAX_RETRIES} reintentos"
        )
        logger.warning(f"   Error: {error_message}")
        logger.warning("   Video permanece en estado 'uploaded' (no existe estado 'failed' en BD)")
        
        # TODO: Para implementar estado 'failed', actualizar init.sql:
        # ALTER TYPE video_status ADD VALUE 'failed';
        
        # Mantener para referencia futura cuando se agregue 'failed' al ENUM
        """
        db = get_db_session()
        video = db.query(Video).filter(Video.id == video_id).first()

        if video:
            # Solo podemos marcar como failed (init.sql no tiene error_message)
            video.status = VideoStatus.failed.value
            db.commit()
            logger.info(f"✅ Video {video_id} marcado como 'failed' en base de datos")
        db.close()
        """
        
        # Aquí podrías en el futuro:
        # - Enviar email al usuario con el error
        # - Registrar en sistema de monitoreo
        # - Crear ticket de soporte

    except Exception as e:
        logger.error(f"❌ Error en DLQ para video {video_id}: {e}")


@app.task(name="tasks.video_processor.cleanup_temp_files")
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
