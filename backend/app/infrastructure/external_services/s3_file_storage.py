import boto3
from typing import Optional
from fastapi import UploadFile
from app.shared.interfaces.file_storage import FileStorageInterface


class S3FileStorage(FileStorageInterface):
    """Implementación de almacenamiento de archivos en AWS S3"""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client('s3', region_name=region)
    
    async def save_file(self, file: UploadFile, filename: str) -> str:
        """Guarda un archivo en S3"""
        try:
            content = await file.read()
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=content,
                ContentType=file.content_type or 'video/mp4'
            )
            return f"s3://{self.bucket_name}/{filename}"
        except Exception as e:
            raise Exception(f"Error al subir archivo a S3: {str(e)}")
    
    async def delete_file(self, filename: str) -> bool:
        """Elimina un archivo de S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            return True
        except Exception:
            return False
    
    async def get_file_url(self, filename: str) -> str:
        """Genera la URL presignada para acceder al archivo"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': filename},
                ExpiresIn=3600  # 1 hora
            )
            return url
        except Exception as e:
            raise Exception(f"Error al generar URL de S3: {str(e)}")
    
    async def file_exists(self, filename: str) -> bool:
        """Verifica si un archivo existe en S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=filename)
            return True
        except:
            return False
    
    async def get_file_size(self, filename: str) -> Optional[int]:
        """Obtiene el tamaño de un archivo en S3"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=filename)
            return response['ContentLength']
        except:
            return None
