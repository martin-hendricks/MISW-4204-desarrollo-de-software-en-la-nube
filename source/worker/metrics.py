"""
Módulo centralizado de métricas de CloudWatch para Worker
Compatible con Celery multiprocess mediante Embedded Metric Format (EMF)
"""
import os
import sys
import psutil

# Agregar directorio shared al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.cloudwatch_metrics import CloudWatchMetrics, MetricUnit

# Inicializar cliente CloudWatch para Worker
cw_metrics = CloudWatchMetrics(
    namespace=os.getenv("CLOUDWATCH_NAMESPACE", "ANB/Worker"),
    service_name="VideoProcessor"
)

# Obtener el proceso actual para métricas de sistema
current_process = psutil.Process(os.getpid())
