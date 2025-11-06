"""
Tarea principal de procesamiento de videos ANB Rising Stars
MODIFICADO: Soporta almacenamiento Local/NFS y S3
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
from storage import get_storage_backend

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

    Flujo MODIFICADO para soportar Local/NFS y S3:
    1. Definir claves de almacenamiento (original/{id}.mp4, processed/{id}.mp4)
    2. Verificar que el archivo original existe en el storage
    3. Descargar archivo original a directorio temporal
    4. Procesar video con FFmpeg localmente:
       - Recortar a 30s
       - Escalar a 720p 16:9
       - Agregar logo ANB
       - Eliminar audio
    5. Agregar cortinillas (intro/outro) si existen
    6. Subir archivo procesado al storage (NFS o S3)
    7. Actualizar PostgreSQL con el resultado
    8. Limpiar archivos temporales

    Args:
        video_id: ID del video

    Returns:
        Diccionario con resultado del procesamiento

    Raises:
        VideoProcessingError: Si falla el procesamiento
        SoftTimeLimitExceeded: Si excede el tiempo límite
    """
    temp_files = []
    storage = get_storage_backend()  # Obtener backend según configuración

    try:
        logger.info(f"🎬 Video {video_id}: Iniciando procesamiento")
        logger.info(f"   Storage: {storage.__class__.__name__}")
        logger.debug(f"   Task ID: {self.request.id}, Intento: {self.request.retries + 1}/{self.max_retries + 1}")

        # ===== 1. DEFINIR RUTAS =====
        # Remote keys (S3) o rutas relativas (local/NFS)
        original_key = f"original/{video_id}.mp4"
        processed_key = f"processed/{video_id}.mp4"

        # Paths locales temporales para procesamiento
        temp_original = os.path.join(config.TEMP_DIR, f"{video_id}_original.mp4")
        temp_processed = os.path.join(config.TEMP_DIR, f"{video_id}_processed.mp4")
        temp_files.extend([temp_original, temp_processed])

        logger.debug(f"📂 Remote: {original_key} -> {processed_key}")
        logger.debug(f"📂 Local temp: {temp_original} -> {temp_processed}")

        # ===== 2. VERIFICAR QUE EXISTE EL ARCHIVO ORIGINAL =====
        if not storage.file_exists(original_key):
            error_msg = f"Archivo original no encontrado: {storage.get_full_path(original_key)}"
            logger.error(f"❌ {error_msg}")
            raise VideoProcessingError(error_msg)

        # ===== 3. DESCARGAR ARCHIVO ORIGINAL =====
        logger.debug("📥 Descargando archivo original...")
        storage.download_file(original_key, temp_original)

        # Obtener tamaño para métricas
        file_size_bytes = os.path.getsize(temp_original)
        file_size_mb = file_size_bytes / (1024 * 1024)
        logger.debug(f"✅ Archivo descargado: {file_size_mb:.2f} MB")

        # Registrar métrica de tamaño de archivo en CloudWatch
        try:
            from metrics import cw_metrics
            from shared.cloudwatch_metrics import MetricUnit

            cw_metrics.record_histogram(
                histogram_name="VideoFileSize",
                value=file_size_bytes,
                unit=MetricUnit.BYTES,
                dimensions={"TaskName": "process_video"}
            )
        except ImportError:
            pass

        # ===== 4. PROCESAR VIDEO CON FFMPEG =====
        logger.debug("⚙️ Procesando con FFmpeg...")
        video_processor.process_video(
            input_path=temp_original,
            output_path=temp_processed,
            add_logo=True
        )

        # Verificar que se creó el archivo procesado
        if not os.path.exists(temp_processed):
            raise VideoProcessingError(f"No se generó el video procesado: {temp_processed}")

        file_size = os.path.getsize(temp_processed)
        logger.info(f"✅ Video procesado: {temp_processed} ({file_size} bytes)")

        # Validar video
        if not video_processor.validate_video(temp_processed):
            logger.warning("⚠️ Video procesado no cumple todas las validaciones")

        # ===== 5. AGREGAR CORTINILLAS (OPCIONAL) =====
        if os.path.exists(config.INTRO_VIDEO_PATH) or os.path.exists(config.OUTRO_VIDEO_PATH):
            logger.debug("🎬 Agregando cortinillas...")
            temp_with_intros = os.path.join(config.TEMP_DIR, f"{video_id}_with_intros.mp4")
            temp_files.append(temp_with_intros)

            video_processor.add_intro_outro(
                video_path=temp_processed,
                output_path=temp_with_intros
            )

            if os.path.exists(temp_with_intros):
                # Usar el archivo con cortinillas
                os.remove(temp_processed)
                os.rename(temp_with_intros, temp_processed)
                logger.info(f"✅ Cortinillas agregadas: {temp_processed}")

        # ===== 6. SUBIR ARCHIVO PROCESADO =====
        logger.debug("📤 Subiendo archivo procesado...")
        storage.upload_file(temp_processed, processed_key)
        logger.info(f"✅ Archivo subido: {storage.get_full_path(processed_key)}")

        # ===== 7. ACTUALIZAR BASE DE DATOS CON RESULTADO =====
        db = get_db_session()
        video = db.query(Video).filter(Video.id == video_id).first()

        if not video:
            logger.warning(f"⚠️ Video {video_id} no encontrado en BD")
            db.close()
            return {
                "status": "success",
                "video_id": video_id,
                "processed_key": processed_key,
                "warning": "Video no encontrado en BD",
            }

        # Actualizar registro
        video.status = VideoStatus.processed
        video.processed_at = datetime.utcnow()

        # Generar URL pública
        base_path = os.getenv("BASE_PATH", "http://localhost:80/api/videos")
        video.processed_url = f"{base_path}/processed/{video_id}"

        db.commit()

        # Métricas finales
        video_info = video_processor.get_video_info(temp_processed)
        duration = int(video_info["duration"])
        file_size_mb = video_info["size_bytes"] / (1024 * 1024)

        from datetime import timezone
        now_utc = datetime.now(timezone.utc)
        if video.uploaded_at.tzinfo is None:
            uploaded_utc = video.uploaded_at.replace(tzinfo=timezone.utc)
        else:
            uploaded_utc = video.uploaded_at
        processing_time = int((now_utc - uploaded_utc).total_seconds())

        logger.info(
            f"✅ Video {video_id}: Procesado exitosamente "
            f"({duration}s, {file_size_mb:.1f}MB, {processing_time}s) - {video.processed_url}"
        )

        db.close()

        return {
            "status": "success",
            "video_id": video_id,
            "processed_key": processed_key,
            "duration": duration,
            "task_id": self.request.id,
            "storage_type": config.STORAGE_TYPE
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
        # ===== 8. LIMPIAR ARCHIVOS TEMPORALES =====
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"🗑️ Eliminado: {temp_file}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo eliminar {temp_file}: {e}")


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
