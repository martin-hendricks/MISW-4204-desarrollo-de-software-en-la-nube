#!/usr/bin/env python3
"""
Script de prueba para el Worker ANB Rising Stars

Simula el comportamiento del backend:
1. Crea un video de prueba
2. Registra en la base de datos
3. Encola tarea de procesamiento
4. Monitorea el estado
"""

import os
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from celery import Celery
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Video, Base
from config import config

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def create_test_video(video_id: int, duration: int = 10):
    """
    Crea un video de prueba usando FFmpeg
    
    Args:
        video_id: ID del video
        duration: Duración en segundos
    """
    print_info(f"Creando video de prueba (ID: {video_id}, Duración: {duration}s)...")
    
    original_dir = config.ORIGINAL_DIR
    os.makedirs(original_dir, exist_ok=True)
    
    video_path = os.path.join(original_dir, f"{video_id}.mp4")
    
    # Crear video de prueba con FFmpeg
    # Video con color sólido y texto
    import subprocess
    
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'color=c=blue:s=1920x1080:d={duration}',
        '-vf', f"drawtext=text='Test Video {video_id}':fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-t', str(duration),
        '-y',  # Sobrescribir si existe
        video_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and os.path.exists(video_path):
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            print_success(f"Video creado: {video_path} ({size_mb:.2f} MB)")
            return video_path
        else:
            print_error(f"Error creando video: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print_error("Timeout creando video")
        return None
    except FileNotFoundError:
        print_error("FFmpeg no está instalado. Instalalo con: brew install ffmpeg (Mac) o apt-get install ffmpeg (Linux)")
        return None


def create_db_record(video_id: int, title: str, user_id: int = 1):
    """
    Crea un registro en la base de datos
    
    Args:
        video_id: ID del video
        title: Título del video
        user_id: ID del usuario
    """
    print_info(f"Creando registro en base de datos...")
    
    try:
        # Conectar a la base de datos
        engine = create_engine(config.DATABASE_URL)
        
        # Crear tablas si no existen
        Base.metadata.create_all(engine)
        
        Session = sessionmaker(bind=engine)
        db = Session()
        
        # Verificar si ya existe
        existing = db.query(Video).filter(Video.id == video_id).first()
        if existing:
            print_warning(f"Video {video_id} ya existe en BD, eliminando...")
            db.delete(existing)
            db.commit()
        
        # Crear nuevo registro
        video = Video(
            id=video_id,
            user_id=user_id,
            title=title,
            status="uploaded",
            original_path=f"{config.ORIGINAL_DIR}/{video_id}.mp4",
            uploaded_at=datetime.utcnow()
        )
        
        db.add(video)
        db.commit()
        db.refresh(video)
        
        print_success(f"Registro creado: ID={video.id}, Status={video.status}")
        
        db.close()
        return video_id
        
    except Exception as e:
        print_error(f"Error creando registro en BD: {e}")
        return None


def enqueue_task(video_id: int):
    """
    Encola tarea de procesamiento en Celery
    
    Args:
        video_id: ID del video
    """
    print_info(f"Encolando tarea de procesamiento...")
    
    try:
        # Crear cliente Celery
        celery_app = Celery('test_client', broker=config.REDIS_URL)
        
        # Encolar tarea
        task = celery_app.send_task(
            'tasks.video_processor.process_video',
            args=[video_id]
        )
        
        print_success(f"Tarea encolada: Task ID={task.id}")
        return task.id
        
    except Exception as e:
        print_error(f"Error encolando tarea: {e}")
        return None


def monitor_task(video_id: int, timeout: int = 120):
    """
    Monitorea el estado del video en la BD
    
    Args:
        video_id: ID del video
        timeout: Tiempo máximo de espera en segundos
    """
    print_info(f"Monitoreando procesamiento (timeout: {timeout}s)...")
    
    try:
        engine = create_engine(config.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < timeout:
            db = Session()
            video = db.query(Video).filter(Video.id == video_id).first()
            
            if video:
                if video.status != last_status:
                    elapsed = time.time() - start_time
                    print(f"  [{elapsed:6.2f}s] Status: {video.status}")
                    last_status = video.status
                
                if video.status == "processed":
                    db.close()
                    print_success(f"¡Video procesado exitosamente!")
                    return True
                
                if video.status == "failed":
                    db.close()
                    print_error(f"Procesamiento falló: {video.error_message}")
                    return False
            
            db.close()
            time.sleep(2)  # Verificar cada 2 segundos
        
        print_warning(f"Timeout esperando procesamiento")
        return False
        
    except Exception as e:
        print_error(f"Error monitoreando tarea: {e}")
        return False


def verify_result(video_id: int):
    """
    Verifica que el video fue procesado correctamente
    
    Args:
        video_id: ID del video
    """
    print_info(f"Verificando resultado...")
    
    try:
        # Verificar BD
        engine = create_engine(config.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db = Session()
        
        video = db.query(Video).filter(Video.id == video_id).first()
        
        if not video:
            print_error("Video no encontrado en BD")
            return False
        
        print(f"\n{Colors.BOLD}Estado en Base de Datos:{Colors.ENDC}")
        print(f"  ID:             {video.id}")
        print(f"  Título:         {video.title}")
        print(f"  Usuario:        {video.user_id}")
        print(f"  Status:         {video.status}")
        print(f"  Original Path:  {video.original_path}")
        print(f"  Processed Path: {video.processed_path}")
        print(f"  Uploaded At:    {video.uploaded_at}")
        print(f"  Processed At:   {video.processed_at}")
        print(f"  Duration:       {video.processed_duration}s")
        print(f"  Error:          {video.error_message or 'None'}")
        
        db.close()
        
        # Verificar archivo procesado
        if video.processed_path and os.path.exists(video.processed_path):
            size_mb = os.path.getsize(video.processed_path) / (1024 * 1024)
            print_success(f"Archivo procesado existe: {video.processed_path} ({size_mb:.2f} MB)")
            
            # Obtener info del video con FFmpeg
            import subprocess
            try:
                cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', video.processed_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    import json
                    info = json.loads(result.stdout)
                    
                    print(f"\n{Colors.BOLD}Información del Video Procesado:{Colors.ENDC}")
                    
                    if 'format' in info:
                        duration = float(info['format'].get('duration', 0))
                        size = int(info['format'].get('size', 0))
                        print(f"  Duración:       {duration:.2f}s")
                        print(f"  Tamaño:         {size / (1024*1024):.2f} MB")
                    
                    if 'streams' in info:
                        for stream in info['streams']:
                            if stream['codec_type'] == 'video':
                                print(f"  Resolución:     {stream['width']}x{stream['height']}")
                                print(f"  Codec:          {stream['codec_name']}")
                                print(f"  FPS:            {stream.get('r_frame_rate', 'N/A')}")
            except:
                pass
            
            return True
        else:
            print_error(f"Archivo procesado no existe: {video.processed_path}")
            return False
            
    except Exception as e:
        print_error(f"Error verificando resultado: {e}")
        return False


def cleanup(video_id: int):
    """Limpia archivos de prueba"""
    print_info("Limpiando archivos de prueba...")
    
    try:
        original_path = f"{config.ORIGINAL_DIR}/{video_id}.mp4"
        processed_path = f"{config.PROCESSED_DIR}/{video_id}_processed.mp4"
        
        for path in [original_path, processed_path]:
            if os.path.exists(path):
                os.remove(path)
                print_success(f"Eliminado: {path}")
        
        # Opcional: eliminar de BD
        # engine = create_engine(config.DATABASE_URL)
        # Session = sessionmaker(bind=engine)
        # db = Session()
        # video = db.query(Video).filter(Video.id == video_id).first()
        # if video:
        #     db.delete(video)
        #     db.commit()
        # db.close()
        
    except Exception as e:
        print_error(f"Error limpiando: {e}")


def main():
    """Función principal de prueba"""
    
    print_header("🧪 Test Worker ANB Rising Stars")
    
    # Generar ID único
    video_id = int(time.time())  # Usar timestamp como ID
    
    print(f"{Colors.BOLD}Configuración:{Colors.ENDC}")
    print(f"  Video ID:       {video_id}")
    print(f"  Redis URL:      {config.REDIS_URL}")
    print(f"  Database URL:   {config.DATABASE_URL.split('@')[-1]}")  # Ocultar credenciales
    print(f"  Upload Dir:     {config.UPLOAD_BASE_DIR}")
    print()
    
    try:
        # 1. Crear video de prueba
        print_header("📹 Paso 1: Crear Video de Prueba")
        video_path = create_test_video(video_id, duration=35)  # 35s para probar recorte a 30s
        
        if not video_path:
            print_error("No se pudo crear el video de prueba")
            return
        
        # 2. Crear registro en BD
        print_header("💾 Paso 2: Registrar en Base de Datos")
        db_id = create_db_record(
            video_id=video_id,
            title=f"Video de Prueba {video_id}",
            user_id=999
        )
        
        if not db_id:
            print_error("No se pudo crear el registro en BD")
            return
        
        # 3. Encolar tarea
        print_header("🚀 Paso 3: Encolar Tarea de Procesamiento")
        task_id = enqueue_task(video_id)
        
        if not task_id:
            print_error("No se pudo encolar la tarea")
            return
        
        # 4. Monitorear procesamiento
        print_header("⏳ Paso 4: Monitorear Procesamiento")
        success = monitor_task(video_id, timeout=120)
        
        # 5. Verificar resultado
        print_header("🔍 Paso 5: Verificar Resultado")
        verify_result(video_id)
        
        # Resumen final
        print_header("📊 Resumen")
        if success:
            print_success("¡Prueba completada exitosamente! ✨")
            print()
            print(f"{Colors.BOLD}Archivos generados:{Colors.ENDC}")
            print(f"  Original:  {config.ORIGINAL_DIR}/{video_id}.mp4")
            print(f"  Procesado: {config.PROCESSED_DIR}/{video_id}_processed.mp4")
            print()
            print(f"{Colors.BOLD}Puedes verificar en:{Colors.ENDC}")
            print(f"  Flower:    http://localhost:5555")
            print(f"  Health:    http://localhost:8001/health")
        else:
            print_error("La prueba no se completó correctamente")
        
        # Preguntar si limpiar
        print()
        response = input(f"{Colors.WARNING}¿Deseas eliminar los archivos de prueba? (s/N): {Colors.ENDC}").lower()
        if response == 's':
            cleanup(video_id)
        else:
            print_info("Archivos de prueba conservados para inspección")
        
    except KeyboardInterrupt:
        print()
        print_warning("Prueba interrumpida por el usuario")
    except Exception as e:
        print_error(f"Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

