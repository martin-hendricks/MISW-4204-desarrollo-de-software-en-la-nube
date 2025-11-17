"""
Módulo centralizado para métricas CloudWatch usando boto3 PutMetricData API
Compatible con Backend (FastAPI) y Worker (Celery multiprocess)

Publica métricas directamente a CloudWatch mediante boto3, sin necesidad de CloudWatch Agent.

Características:
- Auto-detección de metadata de instancia EC2 (InstanceId, AvailabilityZone, etc.)
- Soporte para métricas individuales y batch
- Batching automático para reducir API calls
- Free tier: 1M API calls/mes + 10k métricas custom/mes
"""

import json
import time
import os
import sys
from enum import Enum
from typing import Dict, List, Optional
import logging
import boto3
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricUnit(Enum):
    """Unidades de CloudWatch estándar"""
    MILLISECONDS = "Milliseconds"
    SECONDS = "Seconds"
    MICROSECONDS = "Microseconds"
    BYTES = "Bytes"
    KILOBYTES = "Kilobytes"
    MEGABYTES = "Megabytes"
    GIGABYTES = "Gigabytes"
    PERCENT = "Percent"
    COUNT = "Count"
    COUNT_PER_SECOND = "Count/Second"
    BITS = "Bits"
    BITS_PER_SECOND = "Bits/Second"


class CloudWatchMetrics:
    """
    Cliente de métricas CloudWatch usando Embedded Metric Format (EMF)

    Usage:
        cw = CloudWatchMetrics(namespace="ANB/Backend", service_name="API")

        # Métrica individual
        cw.put_metric("RequestDuration", 125.5, MetricUnit.MILLISECONDS,
                      dimensions={"Method": "GET", "Endpoint": "/api/videos"})

        # Múltiples métricas (más eficiente)
        cw.put_metrics([
            {"name": "RequestCount", "value": 1, "unit": MetricUnit.COUNT},
            {"name": "ErrorCount", "value": 0, "unit": MetricUnit.COUNT}
        ], dimensions={"Method": "GET"})
    """

    def __init__(self, namespace: str, service_name: str, enable_logging: bool = True):
        """
        Inicializa el cliente CloudWatch

        Args:
            namespace: Namespace de CloudWatch (ej: "ANB/Backend")
            service_name: Nombre del servicio (ej: "API", "VideoProcessor")
            enable_logging: Si es False, solo loguea sin enviar a CloudWatch (útil para testing)
        """
        self.namespace = namespace
        self.service_name = service_name
        self.enable_logging = enable_logging
        self.instance_metadata = self._get_instance_metadata()

        # Inicializar cliente boto3 CloudWatch
        self.cloudwatch = boto3.client('cloudwatch', region_name=os.getenv('AWS_REGION', 'us-east-1'))

        logger.info(f"CloudWatch Metrics initialized - Namespace: {namespace}, Service: {service_name}")
        logger.debug(f"Instance metadata: {self.instance_metadata}")

    def _get_instance_metadata(self) -> Dict[str, str]:
        """
        Obtiene metadata de la instancia EC2 automáticamente usando IMDS v2
        Funciona en EC2, ECS, y local (fallback)

        Returns:
            Dict con InstanceId, AvailabilityZone, InstanceType, Environment
        """
        try:
            import requests

            # IMDS v2: Primero obtener token (método seguro recomendado por AWS)
            # La IP 169.254.169.254 es el AWS Instance Metadata Service (IMDS)
            # - Solo accesible desde DENTRO de instancias EC2 (no desde Internet)
            # - IMDSv2 requiere token de sesión (previene SSRF attacks)
            # - Documentación: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html
            imds_base = 'http://169.254.169.254'
            token_url = f'{imds_base}/latest/api/token'
            token_headers = {'X-aws-ec2-metadata-token-ttl-seconds': '21600'}
            token_response = requests.put(token_url, headers=token_headers, timeout=0.5)
            token = token_response.text

            headers = {'X-aws-ec2-metadata-token': token}

            # Obtener metadata de instancia (solo metadata pública, NO credenciales)
            instance_id = requests.get(
                f'{imds_base}/latest/meta-data/instance-id',
                headers=headers,
                timeout=0.5
            ).text

            availability_zone = requests.get(
                f'{imds_base}/latest/meta-data/placement/availability-zone',
                headers=headers,
                timeout=0.5
            ).text

            instance_type = requests.get(
                f'{imds_base}/latest/meta-data/instance-type',
                headers=headers,
                timeout=0.5
            ).text

            return {
                "InstanceId": instance_id,
                "AvailabilityZone": availability_zone,
                "InstanceType": instance_type,
                "Environment": os.getenv("ENVIRONMENT", "production")
            }
        except Exception as e:
            # Fallback para desarrollo local, Docker, o cuando IMDS no está disponible
            logger.debug(f"Could not fetch EC2 metadata (running locally?): {e}")
            return {
                "InstanceId": os.getenv("HOSTNAME", "local"),
                "AvailabilityZone": os.getenv("AWS_REGION", "local"),
                "InstanceType": "local",
                "Environment": os.getenv("ENVIRONMENT", "development")
            }

    def put_metric(
        self,
        metric_name: str,
        value: float,
        unit: MetricUnit,
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[int] = None
    ):
        """
        Publica una métrica individual a CloudWatch usando boto3

        Args:
            metric_name: Nombre de la métrica (ej: "RequestDuration")
            value: Valor de la métrica
            unit: Unidad de la métrica (MetricUnit enum)
            dimensions: Dimensiones adicionales (ej: {"Method": "GET", "Endpoint": "/api/videos"})
            timestamp: Timestamp en milisegundos (opcional, usa tiempo actual si no se provee)

        Example:
            cw.put_metric("RequestDuration", 125.5, MetricUnit.MILLISECONDS,
                         dimensions={"Method": "GET", "Endpoint": "/api/videos"})
        """
        if not self.enable_logging:
            return

        # Merge dimensions: Service + instance metadata + custom
        all_dimensions = {
            "Service": self.service_name,
            **self.instance_metadata,
            **(dimensions or {})
        }

        # Convertir dimensiones a formato CloudWatch
        cw_dimensions = [{"Name": k, "Value": v} for k, v in all_dimensions.items()]

        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[{
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit.value,
                    'Timestamp': datetime.fromtimestamp(timestamp / 1000) if timestamp else datetime.now(),
                    'Dimensions': cw_dimensions
                }]
            )
        except Exception as e:
            logger.error(f"Error publishing metric {metric_name}: {e}")

    def put_metrics(
        self,
        metrics: List[Dict],
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[int] = None
    ):
        """
        Publica múltiples métricas en una sola llamada API (batching - más eficiente)

        Args:
            metrics: Lista de métricas con formato:
                     [{"name": "RequestCount", "value": 1, "unit": MetricUnit.COUNT}, ...]
            dimensions: Dimensiones compartidas para todas las métricas
            timestamp: Timestamp en milisegundos (opcional)

        Example:
            cw.put_metrics([
                {"name": "RequestCount", "value": 1, "unit": MetricUnit.COUNT},
                {"name": "RequestDuration", "value": 125.5, "unit": MetricUnit.MILLISECONDS},
                {"name": "ErrorCount", "value": 0, "unit": MetricUnit.COUNT}
            ], dimensions={"Method": "GET", "Endpoint": "/api/videos"})
        """
        if not self.enable_logging or not metrics:
            return

        # Merge dimensions
        all_dimensions = {
            "Service": self.service_name,
            **self.instance_metadata,
            **(dimensions or {})
        }

        # Convertir dimensiones a formato CloudWatch
        cw_dimensions = [{"Name": k, "Value": v} for k, v in all_dimensions.items()]

        # Construir lista de métricas
        metric_data = []
        ts = datetime.fromtimestamp(timestamp / 1000) if timestamp else datetime.now()

        for metric in metrics:
            metric_data.append({
                'MetricName': metric["name"],
                'Value': metric["value"],
                'Unit': metric["unit"].value,
                'Timestamp': ts,
                'Dimensions': cw_dimensions
            })

        try:
            # Publicar todas las métricas en una sola llamada API (batching)
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metric_data
            )
        except Exception as e:
            logger.error(f"Error publishing metrics batch: {e}")

    def increment_counter(
        self,
        counter_name: str,
        dimensions: Optional[Dict[str, str]] = None,
        value: int = 1
    ):
        """
        Helper para incrementar un contador (equivalente a Prometheus Counter.inc())

        Args:
            counter_name: Nombre del contador
            dimensions: Dimensiones adicionales
            value: Valor a incrementar (default: 1)
        """
        self.put_metric(counter_name, value, MetricUnit.COUNT, dimensions)

    def record_gauge(
        self,
        gauge_name: str,
        value: float,
        unit: MetricUnit,
        dimensions: Optional[Dict[str, str]] = None
    ):
        """
        Helper para registrar un gauge (equivalente a Prometheus Gauge.set())

        Args:
            gauge_name: Nombre del gauge
            value: Valor actual
            unit: Unidad (PERCENT, BYTES, COUNT, etc.)
            dimensions: Dimensiones adicionales
        """
        self.put_metric(gauge_name, value, unit, dimensions)

    def record_histogram(
        self,
        histogram_name: str,
        value: float,
        unit: MetricUnit,
        dimensions: Optional[Dict[str, str]] = None
    ):
        """
        Helper para registrar un valor de histograma (equivalente a Prometheus Histogram.observe())
        CloudWatch calcula automáticamente p50, p95, p99 con statisticValues

        Args:
            histogram_name: Nombre del histograma
            value: Valor observado
            unit: Unidad (SECONDS, MILLISECONDS, etc.)
            dimensions: Dimensiones adicionales
        """
        self.put_metric(histogram_name, value, unit, dimensions)


# Instancia global para testing
_test_metrics = None

def get_test_metrics(namespace: str = "Test", service_name: str = "TestService") -> CloudWatchMetrics:
    """
    Obtiene instancia de métricas para testing (no publica a CloudWatch)
    """
    global _test_metrics
    if _test_metrics is None:
        _test_metrics = CloudWatchMetrics(namespace, service_name, enable_logging=False)
    return _test_metrics
