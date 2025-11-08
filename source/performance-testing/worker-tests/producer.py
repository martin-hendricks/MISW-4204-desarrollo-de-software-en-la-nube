import argparse
import os
import uuid
import time
import shutil
import sys
from datetime import datetime
from celery import Celery, group
from celery.result import GroupResult
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# --- Configuración --- #

# Leer configuración de AWS SQS desde variables de entorno
USE_SQS = os.getenv('USE_SQS', 'true').lower() == 'true'
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL', '')
SQS_DLQ_URL = os.getenv('SQS_DLQ_URL', '')

# Ruta base donde el worker espera encontrar los videos originales
# Esta ruta es DENTRO del contenedor del productor, que mapea al volumen compartido
UPLOAD_FOLDER = '/app/uploads/original'

# Timeout por defecto para esperar resultados (en segundos)
DEFAULT_TIMEOUT = 600  # 10 minutos

# --- Cliente de Celery ---

# Configuración para AWS SQS
if USE_SQS:
    if not SQS_QUEUE_URL:
        print("ERROR: SQS_QUEUE_URL no está configurado. Por favor, configura las variables de entorno necesarias.")
        sys.exit(1)

    broker_url = 'sqs://'
    broker_transport_options = {
        'region': AWS_REGION,
        'predefined_queues': {
            'video_processing': {
                'url': SQS_QUEUE_URL,
            }
        },
        'polling_interval': 20,
        'visibility_timeout': 3600,  # 1 hora
    }

    if SQS_DLQ_URL:
        broker_transport_options['predefined_queues']['dlq'] = {
            'url': SQS_DLQ_URL,
        }

    # Se crea una instancia de Celery para poder enviar tareas
    # No es un worker, solo un cliente
    celery_app = Celery(
        'producer',
        broker=broker_url,
        backend=None  # SQS no soporta result backend
    )

    celery_app.conf.update(
        broker_transport_options=broker_transport_options,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='America/Bogota',
        enable_utc=True,
        broker_connection_retry_on_startup=True,
        task_ignore_result=True,  # No almacenar resultados
    )
else:
    # Fallback a Redis (para desarrollo local)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    celery_app = Celery(
        'producer',
        broker=REDIS_URL,
        backend=REDIS_URL
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

def check_sqs_connection() -> bool:
    """Verifica que AWS SQS esté disponible y las credenciales sean válidas."""
    try:
        log("Verificando conexión a AWS SQS...")

        # Crear cliente de SQS
        sqs_client = boto3.client('sqs', region_name=AWS_REGION)

        # Verificar que la cola principal existe
        if not SQS_QUEUE_URL:
            log("❌ SQS_QUEUE_URL no está configurado", "ERROR")
            return False

        # Intentar obtener atributos de la cola (verifica credenciales y existencia)
        response = sqs_client.get_queue_attributes(
            QueueUrl=SQS_QUEUE_URL,
            AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
        )

        # Obtener estadísticas de la cola
        attrs = response.get('Attributes', {})
        messages_available = attrs.get('ApproximateNumberOfMessages', '0')
        messages_in_flight = attrs.get('ApproximateNumberOfMessagesNotVisible', '0')

        log(f"✅ Conexión a AWS SQS exitosa (Región: {AWS_REGION})", "SUCCESS")
        log(f"   - Cola: {SQS_QUEUE_URL.split('/')[-1]}", "INFO")
        log(f"   - Mensajes disponibles: {messages_available}", "INFO")
        log(f"   - Mensajes en procesamiento: {messages_in_flight}", "INFO")

        return True

    except NoCredentialsError:
        log("❌ No se encontraron credenciales de AWS", "ERROR")
        log("   Configura AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY y AWS_SESSION_TOKEN", "ERROR")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AWS.SimpleQueueService.NonExistentQueue':
            log(f"❌ La cola SQS no existe: {SQS_QUEUE_URL}", "ERROR")
        else:
            log(f"❌ Error de AWS SQS: {error_code} - {e.response['Error']['Message']}", "ERROR")
        return False
    except Exception as e:
        log(f"❌ Error inesperado al conectar a SQS: {e}", "ERROR")
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
    log(f"   - Broker: {'AWS SQS' if USE_SQS else 'Redis'}")
    if USE_SQS:
        log(f"   - AWS Region: {AWS_REGION}")
        log(f"   - SQS Queue: {SQS_QUEUE_URL.split('/')[-1] if SQS_QUEUE_URL else 'No configurada'}")
    else:
        log(f"   - Redis URL: {REDIS_URL}")
    log(f"   - Modo Debug: {'Activado' if debug else 'Desactivado'}")
    log(f"   - Modo: {'Solo encolar (no esperar)' if no_wait else 'Encolar y esperar resultados'}")
    log("=" * 60)

    # --- Validaciones previas ---
    log("\n[Paso 0/4] Validando prerrequisitos...")

    # Verificar conexión al broker (SQS o Redis)
    if USE_SQS:
        if not check_sqs_connection():
            log("❌ No se puede continuar sin conexión a AWS SQS.", "ERROR")
            log("   Verifica que las credenciales de AWS estén configuradas y la cola exista.", "ERROR")
            sys.exit(1)
    else:
        # Si estás usando Redis localmente, puedes agregar check_redis_connection() aquí
        log("⚠️  Usando Redis - asegúrate de que esté disponible", "WARNING")

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
    broker_name = "AWS SQS" if USE_SQS else "Redis"
    log(f"\n[Paso 2/4] Encolando tareas en {broker_name}...")

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

    if USE_SQS:
        log("   ⚠️  NOTA: AWS SQS no soporta result backend.")
        log("   No se puede rastrear el progreso de las tareas desde el producer.")
        log("   Recomendaciones para monitorear:")
        log("   - Logs del worker: docker logs -f <worker-container>")
        log("   - CloudWatch Metrics: Revisa métricas TaskCount, TaskDuration")
        log("   - AWS SQS Console: Monitorea mensajes en la cola")
    else:
        log("   ⚠️  NOTA: El worker NO tiene result_backend configurado.")
        log("   Las tareas se procesarán pero completed_count() puede no funcionar correctamente.")
        log("   Monitorea los logs del worker para ver el progreso real.")

    start_time = time.time()
    elapsed_time = 0
    last_completed = 0

    if USE_SQS:
        # Con SQS, no podemos rastrear el progreso de las tareas
        # Solo monitoreamos la cola para ver cuántos mensajes quedan
        try:
            log("\n   Monitoreando la cola de SQS...")
            sqs_client = boto3.client('sqs', region_name=AWS_REGION)
            total_tasks = len(result_group)

            while elapsed_time < timeout:
                try:
                    # Obtener estadísticas de la cola
                    response = sqs_client.get_queue_attributes(
                        QueueUrl=SQS_QUEUE_URL,
                        AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
                    )

                    attrs = response.get('Attributes', {})
                    messages_available = int(attrs.get('ApproximateNumberOfMessages', '0'))
                    messages_in_flight = int(attrs.get('ApproximateNumberOfMessagesNotVisible', '0'))
                    messages_remaining = messages_available + messages_in_flight

                    elapsed_time = time.time() - start_time

                    # Mostrar progreso
                    print(f"   Mensajes en cola: {messages_available} | En procesamiento: {messages_in_flight} | Tiempo: {elapsed_time:.1f}s   \r", end="", flush=True)

                    # Si no hay mensajes, asumimos que todo se procesó
                    if messages_remaining == 0:
                        print()  # Nueva línea
                        log("✅ La cola está vacía. Todas las tareas fueron procesadas.", "SUCCESS")
                        break

                    time.sleep(5)  # Esperar 5 segundos entre cada sondeo

                except Exception as e:
                    if debug:
                        log(f"   Error al obtener estado de SQS: {e}", "DEBUG")
                    time.sleep(5)

            print()  # Nueva línea después del progreso

            # Verificar si terminó por timeout
            if elapsed_time >= timeout:
                log(f"⚠️  Timeout alcanzado después de {timeout} segundos.", "WARNING")
                log(f"   Aún hay {messages_remaining} mensajes en la cola.", "WARNING")
                log("   Revisa los logs del worker y CloudWatch para más detalles.", "WARNING")

        except KeyboardInterrupt:
            log("\n⚠️  Prueba interrumpida por el usuario.", "WARNING")
            sys.exit(1)
        except Exception as e:
            log(f"❌ Error durante el monitoreo de SQS: {e}", "ERROR")
            if debug:
                import traceback
                log(traceback.format_exc(), "DEBUG")
            sys.exit(1)
    else:
        # Con Redis, podemos rastrear el progreso (si result_backend está configurado)
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