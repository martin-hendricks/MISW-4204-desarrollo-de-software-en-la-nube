"""
Interfaz para el sistema de colas de tareas
Abstrae la implementación específica (Celery, RabbitMQ, etc.)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class TaskQueueInterface(ABC):
    """Interface para el sistema de colas de tareas"""
    
    @abstractmethod
    async def publish_video_processing_task(self, video_id: int) -> str:
        """
        Publica una tarea de procesamiento de video
        
        Args:
            video_id: ID del video a procesar
            
        Returns:
            Task ID de la tarea publicada
        """
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Obtiene el estado de una tarea
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            Diccionario con el estado de la tarea
        """
        pass
