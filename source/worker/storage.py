"""
Abstracción de almacenamiento para Worker
Soporta almacenamiento local (NFS) y S3
"""
import os
import shutil
from abc import ABC, abstractmethod
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class StorageInterface(ABC):
    """Interface abstracta para almacenamiento de archivos"""

    @abstractmethod
    def download_file(self, remote_key: str, local_path: str) -> None:
        """Descarga un archivo del almacenamiento remoto a path local"""
        pass

    @abstractmethod
    def upload_file(self, local_path: str, remote_key: str) -> None:
        """Sube un archivo local al almacenamiento remoto"""
        pass

    @abstractmethod
    def file_exists(self, remote_key: str) -> bool:
        """Verifica si un archivo existe en el almacenamiento"""
        pass

    @abstractmethod
    def get_full_path(self, remote_key: str) -> str:
        """Obtiene el path completo del archivo (para logging)"""
        pass


class LocalStorage(StorageInterface):
    """
    Almacenamiento local/NFS
    Los archivos ya están en el filesystem montado
    """

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        logger.info(f"📁 LocalStorage inicializado: {base_dir}")

    def download_file(self, remote_key: str, local_path: str) -> None:
        """
        En almacenamiento local, los archivos YA están en el filesystem
        Solo necesitamos copiar si el destino es diferente
        """
        source_path = os.path.join(self.base_dir, remote_key)

        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Archivo no encontrado: {source_path}")

        # Si el source y dest son el mismo, no hacer nada
        if os.path.abspath(source_path) == os.path.abspath(local_path):
            logger.debug(f"Archivo ya está en destino: {local_path}")
            return

        # Copiar archivo
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        shutil.copy2(source_path, local_path)
        logger.debug(f"📥 Copiado: {source_path} -> {local_path}")

    def upload_file(self, local_path: str, remote_key: str) -> None:
        """Copia el archivo procesado a la ubicación final"""
        dest_path = os.path.join(self.base_dir, remote_key)

        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Archivo local no encontrado: {local_path}")

        # Crear directorio destino
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Copiar o mover archivo
        if os.path.abspath(local_path) == os.path.abspath(dest_path):
            logger.debug(f"Archivo ya está en destino: {dest_path}")
            return

        shutil.copy2(local_path, dest_path)
        logger.debug(f"📤 Copiado: {local_path} -> {dest_path}")

    def file_exists(self, remote_key: str) -> bool:
        """Verifica si existe el archivo"""
        full_path = os.path.join(self.base_dir, remote_key)
        return os.path.exists(full_path)

    def get_full_path(self, remote_key: str) -> str:
        """Retorna el path completo"""
        return os.path.join(self.base_dir, remote_key)


class S3Storage(StorageInterface):
    """
    Almacenamiento S3
    Descarga archivos bajo demanda y sube resultados
    """

    def __init__(self, bucket_name: str, region: str = 'us-east-1', session_token: str = None):
        try:
            import boto3
            self.bucket_name = bucket_name
            self.region = region

            # Configurar cliente S3 con session token (para AWS Academy)
            if session_token:
                self.s3_client = boto3.client(
                    's3',
                    region_name=region,
                    aws_session_token=session_token
                )
                logger.info(f"☁️ S3Storage inicializado con session token: bucket={bucket_name}, region={region}")
            else:
                self.s3_client = boto3.client('s3', region_name=region)
                logger.info(f"☁️ S3Storage inicializado: bucket={bucket_name}, region={region}")
        except ImportError:
            raise ImportError("boto3 no está instalado. Ejecuta: pip install boto3")

    def download_file(self, remote_key: str, local_path: str) -> None:
        """Descarga archivo de S3 a path local"""
        try:
            # Crear directorio local
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Descargar de S3
            logger.debug(f"📥 Descargando de S3: s3://{self.bucket_name}/{remote_key}")
            self.s3_client.download_file(self.bucket_name, remote_key, local_path)
            logger.info(f"✅ Descargado: {remote_key} -> {local_path}")

        except Exception as e:
            logger.error(f"❌ Error descargando de S3: {e}")
            raise

    def upload_file(self, local_path: str, remote_key: str) -> None:
        """Sube archivo local a S3"""
        try:
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Archivo local no encontrado: {local_path}")

            # Subir a S3
            logger.debug(f"📤 Subiendo a S3: s3://{self.bucket_name}/{remote_key}")
            self.s3_client.upload_file(local_path, self.bucket_name, remote_key)
            logger.info(f"✅ Subido: {local_path} -> s3://{self.bucket_name}/{remote_key}")

        except Exception as e:
            logger.error(f"❌ Error subiendo a S3: {e}")
            raise

    def file_exists(self, remote_key: str) -> bool:
        """Verifica si existe un archivo en S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=remote_key)
            return True
        except:
            return False

    def get_full_path(self, remote_key: str) -> str:
        """Retorna la URI de S3"""
        return f"s3://{self.bucket_name}/{remote_key}"


def get_storage_backend() -> StorageInterface:
    """
    Factory para obtener el backend de almacenamiento según configuración
    Lee la variable STORAGE_TYPE del entorno
    """
    from config import config

    storage_type = os.getenv('STORAGE_TYPE', 'local').lower()

    if storage_type == 's3':
        return S3Storage(
            bucket_name=config.S3_BUCKET_NAME,
            region=config.AWS_REGION,
            session_token=config.AWS_SESSION_TOKEN
        )
    else:
        return LocalStorage(base_dir=config.UPLOAD_BASE_DIR)
