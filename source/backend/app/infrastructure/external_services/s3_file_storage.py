import boto3
from typing import Optional
from fastapi import UploadFile
from app.shared.interfaces.file_storage import FileStorageInterface, LocationType


class S3FileStorage(FileStorageInterface):
    """Implementación de almacenamiento de archivos en AWS S3"""

    def __init__(self, bucket_name: str, region: str = "us-east-1", session_token: str = None):
        self.bucket_name = bucket_name
        self.region = region

        # Configurar cliente S3 con session token (para AWS Academy)
        if session_token:
            self.s3_client = boto3.client(
                's3',
                region_name=region,
                aws_session_token=session_token
            )
        else:
            self.s3_client = boto3.client('s3', region_name=region)
    
    def _get_s3_key(self, filename: str, location: LocationType) -> str:
        """Obtiene la clave S3 basada en la ubicación"""
        return f"{location}/{filename}"
    
    async def save_file(self, file: UploadFile, filename: str, location: LocationType = "original") -> str:
        """Guarda un archivo en S3"""
        try:
            content = await file.read()
            s3_key = self._get_s3_key(filename, location)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType=file.content_type or 'video/mp4'
            )
            return f"s3://{self.bucket_name}/{s3_key}"
        except Exception as e:
            raise Exception(f"Error al subir archivo a S3: {str(e)}")
    
    async def delete_file(self, filename: str, location: LocationType = "original") -> bool:
        """Elimina un archivo de S3"""
        try:
            s3_key = self._get_s3_key(filename, location)
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except Exception:
            return False
    
    async def get_file_url(self, filename: str, location: LocationType = "original") -> str:
        """Genera la URL presignada para acceder al archivo"""
        try:
            s3_key = self._get_s3_key(filename, location)
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=3600  # 1 hora
            )
            return url
        except Exception as e:
            raise Exception(f"Error al generar URL de S3: {str(e)}")
    
    async def file_exists(self, filename: str, location: LocationType = "original") -> bool:
        """Verifica si un archivo existe en S3"""
        try:
            s3_key = self._get_s3_key(filename, location)
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except:
            return False
    
    async def get_file_size(self, filename: str, location: LocationType = "original") -> Optional[int]:
        """Obtiene el tamaño de un archivo en S3"""
        try:
            s3_key = self._get_s3_key(filename, location)
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return response['ContentLength']
        except:
            return None
    
    async def get_file_content(self, filename: str, location: LocationType = "original") -> bytes:
        """Obtiene el contenido del archivo como bytes desde S3"""
        try:
            s3_key = self._get_s3_key(filename, location)
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
        except Exception as e:
            raise FileNotFoundError(f"Archivo no encontrado: {filename} en ubicación {location}")
