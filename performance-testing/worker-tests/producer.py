import argparse
import os
import uuid
import time
import shutil
from celery import Celery
from celery.result import GroupResult

# --- Configuración --- #

# Lee la URL de Redis desde una variable de entorno, con un valor por defecto
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Ruta base donde el worker espera encontrar los videos originales
# Esta ruta es DENTRO del contenedor del productor, que mapea al volumen compartido
UPLOAD_FOLDER = '/app/uploads/original'

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
)

# --- Lógica Principal --- #

def run_test(num_videos: int, video_path: str):
    """
    Ejecuta la prueba de carga contra el worker.

    Args:
        num_videos: Número de tareas de procesamiento de video a encolar.
        video_path: Ruta al archivo de video local que se usará para la prueba.
    """
    print("=" * 60)
    print(f"🚀 Iniciando prueba de rendimiento del Worker")
    print(f"   - Tareas a generar: {num_videos}")
    print(f"   - Archivo de video: {video_path}")
    print(f"   - Destino de worker: {UPLOAD_FOLDER}")
    print("=" * 60)

    # --- 1. Preparar archivos y tareas ---
    print("\n[Paso 1/3] Preparando archivos y tareas...")

    if not os.path.exists(video_path):
        print(f"❌ Error: El archivo de video de prueba '{video_path}' no existe.")
        print("   Por favor, asegúrate de que el archivo exista y vuelve a intentarlo.")
        return

    task_signatures = []
    for i in range(num_videos):
        video_id = i + 1 # Usamos un ID simple y predecible
        new_filename = f"{video_id}.mp4"
        destination_path = os.path.join(UPLOAD_FOLDER, new_filename)

        # Copiar el archivo de video de prueba al volumen compartido
        # para que el worker pueda encontrarlo.
        try:
            shutil.copy(video_path, destination_path)
        except Exception as e:
            print(f"❌ Error copiando archivo a {destination_path}: {e}")
            print("   Asegúrate de que el volumen 'video_storage' esté montado correctamente.")
            return

        # Crear la "firma" de la tarea de Celery
        # Esto define la tarea que queremos ejecutar y sus argumentos
        signature = celery_app.signature(
            'tasks.video_processor.process_video',
            args=(video_id,)
        )
        task_signatures.append(signature)
    
    print(f"✅ {num_videos} archivos copiados y tareas preparadas.")

    # --- 2. Ejecutar y cronometrar ---
    print("\n[Paso 2/3] Encolando tareas y esperando resultados...")
    
    start_time = time.time()

    # Agrupar todas las tareas y ejecutarlas en paralelo
    task_group = celery_app.group(task_signatures)
    result_group = task_group.apply_async()

    # Bucle para esperar a que todas las tareas del grupo terminen
    total_tasks = len(result_group)
    while not result_group.ready():
        completed_count = result_group.completed_count()
        progress = (completed_count / total_tasks) * 100
        print(f"   Progreso: {completed_count}/{total_tasks} tareas completadas ({progress:.2f}%)   \r", end="")
        time.sleep(2) # Esperar 2 segundos entre cada sondeo

    end_time = time.time()
    print(f"\n✅ Todas las {total_tasks} tareas han finalizado.")

    # --- 3. Calcular y mostrar resultados ---
    print("\n[Paso 3/3] Calculando y mostrando resultados...")

    total_time = end_time - start_time
    videos_per_second = num_videos / total_time
    videos_per_minute = videos_per_second * 60

    print("\n" + "=" * 60)
    print("📊 Resultados de la Prueba de Rendimiento")
    print("-" * 60)
    print(f"   - Videos procesados:      {num_videos}")
    print(f"   - Tiempo total:           {total_time:.2f} segundos")
    print(f"   - Throughput (videos/seg): {videos_per_second:.2f}")
    print(f"   - Throughput (videos/min): {videos_per_minute:.2f}")
    print("=" * 60)

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
        default='./assets/test_video.mp4',
        help='Ruta al archivo de video a utilizar para la prueba.'
    )
    
    args = parser.parse_args()
    
    run_test(args.num_videos, args.video_file)
