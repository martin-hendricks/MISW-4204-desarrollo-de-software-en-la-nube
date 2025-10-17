import argparse
import os
import uuid
import time
import shutil
import sys
from datetime import datetime
from celery import Celery, group
from celery.result import GroupResult
import redis

# --- Configuración --- #

# Lee la URL de Redis desde una variable de entorno, con un valor por defecto
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Ruta base donde el worker espera encontrar los videos originales
# Esta ruta es DENTRO del contenedor del productor, que mapea al volumen compartido
UPLOAD_FOLDER = '/app/uploads/original'

# Timeout por defecto para esperar resultados (en segundos)
DEFAULT_TIMEOUT = 600  # 10 minutos

# --- Cliente de Celery ---

# Se crea una instancia de Celery para poder enviar tareas
# No es un worker, solo un cliente
celery_app = Celery(
    'producer',
    broker=REDIS_URL,
    backend=REDIS_URL  # Usamos Redis como backend para poder consultar el estado
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/Bogota',
    enable_utc=True,
    broker_connection_retry_on_startup=True,
)

# --- Funciones de Utilidad --- #

def log(message: str, level: str = "INFO"):
    """Imprime un mensaje de log con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}", flush=True)

def check_redis_connection() -> bool:
    """Verifica que Redis esté disponible y acepte conexiones."""
    try:
        log("Verificando conexión a Redis...")
        # Parsear la URL de Redis
        if REDIS_URL.startswith('redis://'):
            redis_host = REDIS_URL.split('//')[1].split(':')[0]
            redis_port = int(REDIS_URL.split(':')[-1].split('/')[0])
        else:
            log(f"Formato de URL de Redis no reconocido: {REDIS_URL}", "ERROR")
            return False

        # Intentar conectar
        r = redis.Redis(host=redis_host, port=redis_port, socket_connect_timeout=5)
        r.ping()
        log(f"✅ Conexión a Redis exitosa ({redis_host}:{redis_port})", "SUCCESS")
        return True
    except redis.ConnectionError as e:
        log(f"❌ Error de conexión a Redis: {e}", "ERROR")
        log(f"   URL de Redis: {REDIS_URL}", "ERROR")
        return False
    except Exception as e:
        log(f"❌ Error inesperado al conectar a Redis: {e}", "ERROR")
        return False

def check_upload_folder() -> bool:
    """Verifica que la carpeta de uploads exista, si no, la crea."""
    try:
        if not os.path.exists(UPLOAD_FOLDER):
            log(f"Carpeta {UPLOAD_FOLDER} no existe. Creándola...", "WARNING")
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            log(f"✅ Carpeta {UPLOAD_FOLDER} creada exitosamente", "SUCCESS")
        else:
            log(f"✅ Carpeta {UPLOAD_FOLDER} existe", "SUCCESS")
        return True
    except Exception as e:
        log(f"❌ Error al verificar/crear carpeta {UPLOAD_FOLDER}: {e}", "ERROR")
        return False

# --- Lógica Principal --- #

def run_test(num_videos: int, video_path: str, timeout: int = DEFAULT_TIMEOUT, debug: bool = False, no_wait: bool = False):
    """
    Ejecuta la prueba de carga contra el worker.

    Args:
        num_videos: Número de tareas de procesamiento de video a encolar.
        video_path: Ruta al archivo de video local que se usará para la prueba.
        timeout: Tiempo máximo de espera en segundos (default: 600).
        debug: Activar modo debug con información adicional.
        no_wait: Si es True, solo encola las tareas y termina sin esperar resultados.
    """
    log("=" * 60)
    log("🚀 Iniciando prueba de rendimiento del Worker")
    log(f"   - Tareas a generar: {num_videos}")
    log(f"   - Archivo de video: {video_path}")
    log(f"   - Destino de worker: {UPLOAD_FOLDER}")
    log(f"   - Timeout: {timeout} segundos")
    log(f"   - Redis URL: {REDIS_URL}")
    log(f"   - Modo Debug: {'Activado' if debug else 'Desactivado'}")
    log(f"   - Modo: {'Solo encolar (no esperar)' if no_wait else 'Encolar y esperar resultados'}")
    log("=" * 60)

    # --- Validaciones previas ---
    log("\n[Paso 0/4] Validando prerrequisitos...")

    # Verificar conexión a Redis
    if not check_redis_connection():
        log("❌ No se puede continuar sin conexión a Redis.", "ERROR")
        log("   Verifica que Redis esté corriendo y la URL sea correcta.", "ERROR")
        sys.exit(1)

    # Verificar carpeta de uploads
    if not check_upload_folder():
        log("❌ No se puede continuar sin la carpeta de uploads.", "ERROR")
        sys.exit(1)

    # --- 1. Preparar archivos y tareas ---
    log("\n[Paso 1/4] Preparando archivos y tareas...")

    if not os.path.exists(video_path):
        log(f"❌ Error: El archivo de video de prueba '{video_path}' no existe.", "ERROR")
        log("   Por favor, asegúrate de que el archivo exista y vuelve a intentarlo.", "ERROR")
        sys.exit(1)

    # Obtener tamaño del archivo
    file_size = os.path.getsize(video_path)
    file_size_mb = file_size / (1024 * 1024)
    log(f"   - Tamaño del archivo: {file_size_mb:.2f} MB")

    task_signatures = []
    files_copied = 0

    for i in range(num_videos):
        video_id = i + 1  # Usamos un ID simple y predecible
        new_filename = f"{video_id}.mp4"
        destination_path = os.path.join(UPLOAD_FOLDER, new_filename)

        # Copiar el archivo de video de prueba al volumen compartido
        try:
            shutil.copy(video_path, destination_path)
            files_copied += 1
            if debug and files_copied % 10 == 0:
                log(f"   - Copiados {files_copied}/{num_videos} archivos...", "DEBUG")
        except Exception as e:
            log(f"❌ Error copiando archivo a {destination_path}: {e}", "ERROR")
            log("   Asegúrate de que el volumen 'video_storage' esté montado correctamente.", "ERROR")
            sys.exit(1)

        # Crear la "firma" de la tarea de Celery
        # IMPORTANTE: Especificar la cola 'video_processing' que es donde escucha el worker
        signature = celery_app.signature(
            'tasks.video_processor.process_video',
            args=(video_id,),
            queue='video_processing'
        )
        task_signatures.append(signature)

    log(f"✅ {num_videos} archivos copiados y tareas preparadas.", "SUCCESS")

    # --- 2. Ejecutar y cronometrar ---
    log("\n[Paso 2/4] Encolando tareas en Redis...")

    try:
        # Agrupar todas las tareas y ejecutarlas en paralelo
        task_group = group(task_signatures)
        result_group = task_group.apply_async()
        log(f"✅ {len(task_signatures)} tareas encoladas exitosamente.", "SUCCESS")

        if debug:
            log(f"   - Group ID: {result_group.id}", "DEBUG")
            log(f"   - Total tasks in group: {len(result_group)}", "DEBUG")

    except Exception as e:
        log(f"❌ Error al encolar tareas: {e}", "ERROR")
        log("   Verifica que el worker esté corriendo y que la configuración de Celery sea correcta.", "ERROR")
        sys.exit(1)

    # --- 3. Esperar resultados o terminar ---
    if no_wait:
        log("\n[Paso 3/4] Modo 'no-wait' activado - No se esperarán resultados")
        log(f"✅ {len(task_signatures)} tareas encoladas en la cola 'video_processing'")
        log("\n" + "=" * 60)
        log("📊 Resumen de Encolado")
        log("-" * 60)
        log(f"   - Videos encolados:        {num_videos}")
        log(f"   - Tamaño por video:        {file_size_mb:.2f} MB")
        log(f"   - Datos totales:           {file_size_mb * num_videos:.2f} MB")
        log("   - Cola: video_processing")
        log("")
        log("💡 Para monitorear el procesamiento:")
        log("   - Grafana: http://localhost:3000")
        log("   - Logs del worker: docker logs -f <worker-container-name>")
        log("=" * 60)
        return

    log("\n[Paso 3/4] Esperando resultados...")
    log(f"   Timeout configurado: {timeout} segundos")
    log("   ⚠️  NOTA: El worker NO tiene result_backend configurado.")
    log("   Las tareas se procesarán pero completed_count() puede no funcionar correctamente.")
    log("   Monitorea los logs del worker para ver el progreso real.")

    start_time = time.time()
    elapsed_time = 0
    last_completed = 0

    try:
        total_tasks = len(result_group)
        while not result_group.ready() and elapsed_time < timeout:
            try:
                completed_count = result_group.completed_count()
                progress = (completed_count / total_tasks) * 100
                elapsed_time = time.time() - start_time

                # Mostrar progreso
                print(f"   Progreso: {completed_count}/{total_tasks} tareas completadas ({progress:.2f}%) - Tiempo: {elapsed_time:.1f}s   \r", end="", flush=True)

                # Log adicional si hay cambios y debug está activo
                if debug and completed_count != last_completed:
                    print()  # Nueva línea para el log
                    log(f"   - Completadas: {completed_count}/{total_tasks}", "DEBUG")
                    last_completed = completed_count

                time.sleep(2)  # Esperar 2 segundos entre cada sondeo
            except Exception as e:
                if debug:
                    log(f"   Error al obtener estado: {e}", "DEBUG")
                time.sleep(2)

        print()  # Nueva línea después del progreso

        # Verificar si terminó por timeout
        if elapsed_time >= timeout:
            log(f"⚠️  Timeout alcanzado después de {timeout} segundos.", "WARNING")
            completed_count = result_group.completed_count()
            log(f"   Tareas completadas: {completed_count}/{total_tasks}", "WARNING")
            if completed_count < total_tasks:
                log("   Algunas tareas no se completaron. Revisa los logs del worker.", "WARNING")
        else:
            end_time = time.time()
            log(f"✅ Todas las {total_tasks} tareas han finalizado.", "SUCCESS")

    except KeyboardInterrupt:
        log("\n⚠️  Prueba interrumpida por el usuario.", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"❌ Error durante la espera de resultados: {e}", "ERROR")
        if debug:
            import traceback
            log(traceback.format_exc(), "DEBUG")
        sys.exit(1)

    # --- 4. Calcular y mostrar resultados ---
    log("\n[Paso 4/4] Calculando y mostrando resultados...")

    end_time = time.time()
    total_time = end_time - start_time
    videos_per_second = num_videos / total_time if total_time > 0 else 0
    videos_per_minute = videos_per_second * 60

    log("\n" + "=" * 60)
    log("📊 Resultados de la Prueba de Rendimiento")
    log("-" * 60)
    log(f"   - Videos procesados:       {num_videos}")
    log(f"   - Tamaño por video:        {file_size_mb:.2f} MB")
    log(f"   - Datos totales:           {file_size_mb * num_videos:.2f} MB")
    log(f"   - Tiempo total:            {total_time:.2f} segundos")
    log(f"   - Throughput (videos/seg): {videos_per_second:.2f}")
    log(f"   - Throughput (videos/min): {videos_per_minute:.2f}")
    log("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script para pruebas de carga del worker de Celery.")
    parser.add_argument(
        '--num-videos',
        type=int,
        default=10,
        help='Número de videos a procesar en la prueba.'
    )
    parser.add_argument(
        '--video-file',
        type=str,
        default='./assets/dummy_file_50mb.mp4',
        help='Ruta al archivo de video a utilizar para la prueba.'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f'Tiempo máximo de espera en segundos (default: {DEFAULT_TIMEOUT}).'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Activar modo debug con información adicional.'
    )
    parser.add_argument(
        '--no-wait',
        action='store_true',
        help='Solo encolar tareas sin esperar resultados (recomendado para pruebas de carga).'
    )

    args = parser.parse_args()

    run_test(args.num_videos, args.video_file, args.timeout, args.debug, args.no_wait)