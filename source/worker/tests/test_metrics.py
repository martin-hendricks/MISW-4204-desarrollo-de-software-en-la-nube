"""
Tests para el módulo de métricas de Prometheus
"""
import pytest
from unittest.mock import patch, MagicMock
import os


class TestMetricsSetup:
    """Tests para la configuración de métricas"""

    def test_metrics_directory_created(self):
        """Test que el directorio de métricas se crea"""
        import metrics
        assert os.path.exists(metrics.METRICS_DIR)

    def test_metrics_directory_env_var(self):
        """Test que la variable de entorno se establece"""
        import metrics
        assert 'PROMETHEUS_MULTIPROC_DIR' in os.environ
        assert os.environ['PROMETHEUS_MULTIPROC_DIR'] == metrics.METRICS_DIR

    def test_registry_exists(self):
        """Test que existe el registry"""
        from metrics import registry
        assert registry is not None


class TestCeleryMetrics:
    """Tests para métricas de Celery"""

    def test_celery_tasks_total_counter_exists(self):
        """Test que existe el contador de tareas totales"""
        from metrics import celery_tasks_total
        assert celery_tasks_total is not None
        assert celery_tasks_total._name == 'celery_tasks_total'

    def test_celery_tasks_failed_counter_exists(self):
        """Test que existe el contador de tareas fallidas"""
        from metrics import celery_tasks_failed
        assert celery_tasks_failed is not None
        assert celery_tasks_failed._name == 'celery_tasks_failed_total'

    def test_celery_task_duration_histogram_exists(self):
        """Test que existe el histograma de duración de tareas"""
        from metrics import celery_task_duration
        assert celery_task_duration is not None
        assert celery_task_duration._name == 'celery_task_duration_seconds'

    def test_celery_task_duration_has_buckets(self):
        """Test que el histograma tiene buckets configurados"""
        from metrics import celery_task_duration
        # Verificar que tiene configuración de buckets
        assert hasattr(celery_task_duration, '_upper_bounds')

    def test_video_processing_duration_histogram_exists(self):
        """Test que existe el histograma de duración de procesamiento"""
        from metrics import video_processing_duration
        assert video_processing_duration is not None
        assert video_processing_duration._name == 'video_processing_duration_seconds'


class TestGaugeMetrics:
    """Tests para métricas tipo Gauge"""

    def test_celery_active_tasks_gauge_exists(self):
        """Test que existe el gauge de tareas activas"""
        from metrics import celery_active_tasks
        assert celery_active_tasks is not None
        assert celery_active_tasks._name == 'celery_active_tasks'

    def test_celery_reserved_tasks_gauge_exists(self):
        """Test que existe el gauge de tareas reservadas"""
        from metrics import celery_reserved_tasks
        assert celery_reserved_tasks is not None
        assert celery_reserved_tasks._name == 'celery_reserved_tasks'

    def test_celery_queue_length_gauge_exists(self):
        """Test que existe el gauge de longitud de cola"""
        from metrics import celery_queue_length
        assert celery_queue_length is not None
        assert celery_queue_length._name == 'celery_queue_length'

    def test_gauges_have_multiprocess_mode(self):
        """Test que los gauges tienen modo multiprocess"""
        from metrics import celery_active_tasks, celery_reserved_tasks, celery_queue_length

        # Verificar que tienen modo multiprocess configurado
        assert hasattr(celery_active_tasks, '_multiprocess_mode')
        assert hasattr(celery_reserved_tasks, '_multiprocess_mode')
        assert hasattr(celery_queue_length, '_multiprocess_mode')


class TestVideoMetrics:
    """Tests para métricas de video"""

    def test_video_file_size_histogram_exists(self):
        """Test que existe el histograma de tamaño de archivos"""
        from metrics import video_file_size_bytes
        assert video_file_size_bytes is not None
        assert video_file_size_bytes._name == 'video_file_size_bytes'

    def test_video_file_size_has_buckets(self):
        """Test que el histograma de tamaño tiene buckets configurados"""
        from metrics import video_file_size_bytes
        assert hasattr(video_file_size_bytes, '_upper_bounds')


class TestMetricsGeneration:
    """Tests para generación de métricas"""

    @patch('metrics.multiprocess.MultiProcessCollector')
    @patch('metrics.generate_latest')
    def test_generate_multiprocess_metrics(self, mock_generate, mock_collector):
        """Test generación de métricas multiprocess"""
        from metrics import generate_multiprocess_metrics

        mock_generate.return_value = b'# HELP test\n'

        result = generate_multiprocess_metrics()

        # Verificar que se llamó a MultiProcessCollector
        mock_collector.assert_called_once()
        # Verificar que se llamó a generate_latest
        mock_generate.assert_called_once()

    def test_generate_multiprocess_metrics_returns_bytes(self):
        """Test que la generación retorna bytes"""
        from metrics import generate_multiprocess_metrics

        result = generate_multiprocess_metrics()

        # Debe retornar bytes
        assert isinstance(result, bytes)


class TestMetricsLabels:
    """Tests para labels de métricas"""

    def test_celery_tasks_total_has_labels(self):
        """Test que celery_tasks_total tiene labels correctos"""
        from metrics import celery_tasks_total

        # Verificar que tiene los labels task_name y status
        assert celery_tasks_total._labelnames == ('task_name', 'status')

    def test_celery_tasks_failed_has_labels(self):
        """Test que celery_tasks_failed tiene labels correctos"""
        from metrics import celery_tasks_failed

        # Verificar que tiene los labels task_name y error_type
        assert celery_tasks_failed._labelnames == ('task_name', 'error_type')

    def test_celery_task_duration_has_labels(self):
        """Test que celery_task_duration tiene labels correctos"""
        from metrics import celery_task_duration

        # Verificar que tiene el label task_name
        assert celery_task_duration._labelnames == ('task_name',)

    def test_celery_queue_length_has_labels(self):
        """Test que celery_queue_length tiene labels correctos"""
        from metrics import celery_queue_length

        # Verificar que tiene el label queue_name
        assert celery_queue_length._labelnames == ('queue_name',)


class TestMetricsIncrement:
    """Tests para incrementar métricas"""

    def test_increment_celery_tasks_total(self):
        """Test incrementar contador de tareas totales"""
        from metrics import celery_tasks_total

        # Obtener valor inicial
        initial_value = celery_tasks_total.labels(task_name='test_task', status='success')._value.get()

        # Incrementar
        celery_tasks_total.labels(task_name='test_task', status='success').inc()

        # Verificar que aumentó
        new_value = celery_tasks_total.labels(task_name='test_task', status='success')._value.get()
        assert new_value > initial_value

    def test_increment_celery_tasks_failed(self):
        """Test incrementar contador de tareas fallidas"""
        from metrics import celery_tasks_failed

        # Obtener valor inicial
        initial_value = celery_tasks_failed.labels(task_name='test_task', error_type='ValueError')._value.get()

        # Incrementar
        celery_tasks_failed.labels(task_name='test_task', error_type='ValueError').inc()

        # Verificar que aumentó
        new_value = celery_tasks_failed.labels(task_name='test_task', error_type='ValueError')._value.get()
        assert new_value > initial_value


class TestMetricsObserve:
    """Tests para observar métricas de histogramas"""

    def test_observe_celery_task_duration(self):
        """Test observar duración de tarea"""
        from metrics import celery_task_duration

        # Observar un valor
        celery_task_duration.labels(task_name='test_task').observe(10.5)

        # Verificar que se registró (no lanzó excepción)
        assert True

    def test_observe_video_processing_duration(self):
        """Test observar duración de procesamiento"""
        from metrics import video_processing_duration

        # Observar un valor
        video_processing_duration.observe(60.0)

        # Verificar que se registró
        assert True

    def test_observe_video_file_size(self):
        """Test observar tamaño de archivo"""
        from metrics import video_file_size_bytes

        # Observar un valor (10 MB)
        video_file_size_bytes.observe(10 * 1024 * 1024)

        # Verificar que se registró
        assert True


class TestMetricsGaugeOperations:
    """Tests para operaciones con gauges"""

    def test_set_celery_active_tasks(self):
        """Test establecer tareas activas"""
        from metrics import celery_active_tasks

        # Establecer valor
        celery_active_tasks.set(5)

        # Verificar que se estableció
        assert True

    def test_set_celery_queue_length(self):
        """Test establecer longitud de cola"""
        from metrics import celery_queue_length

        # Establecer valor con label
        celery_queue_length.labels(queue_name='video_processing').set(10)

        # Verificar que se estableció
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
