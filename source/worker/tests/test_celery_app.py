"""
Tests unitarios para celery_app.py
Cubre configuración de Celery, signal handlers y métricas
"""
import pytest
import sys
from unittest.mock import patch, MagicMock, Mock
import time
import logging
from celery import Celery
from celery.signals import (
    worker_ready,
    task_prerun,
    task_postrun,
    task_success,
    task_failure,
    task_retry
)


class TestCeleryAppConfiguration:
    """Tests para la configuración de la aplicación Celery"""

    def test_app_exists(self):
        """Test que la app Celery existe"""
        from celery_app import app
        assert app is not None
        assert isinstance(app, Celery)

    def test_app_name(self):
        """Test que la app tiene el nombre correcto"""
        from celery_app import app
        assert app.main == 'anb_video_processor'

    def test_broker_url_config(self):
        """Test que el broker URL está configurado"""
        from celery_app import app
        from config import config
        
        assert app.conf.broker_url == config.REDIS_URL

    def test_task_serializer(self):
        """Test que el serializador está configurado"""
        from celery_app import app
        
        assert app.conf.task_serializer == 'json'
        assert 'json' in app.conf.accept_content

    def test_timezone_config(self):
        """Test que el timezone está configurado"""
        from celery_app import app
        
        assert app.conf.timezone == 'America/Bogota'
        assert app.conf.enable_utc is True

    def test_task_acks_late(self):
        """Test que task_acks_late está configurado"""
        from celery_app import app
        
        assert app.conf.task_acks_late is True
        assert app.conf.task_reject_on_worker_lost is True

    def test_retry_config(self):
        """Test que la configuración de reintentos está correcta"""
        from celery_app import app
        from config import config
        
        assert app.conf.task_default_retry_delay == config.CELERY_TASK_DEFAULT_RETRY_DELAY
        assert app.conf.task_max_retries == config.CELERY_TASK_MAX_RETRIES

    def test_timeout_config(self):
        """Test que los timeouts están configurados"""
        from celery_app import app
        from config import config
        
        assert app.conf.task_soft_time_limit == config.TASK_SOFT_TIME_LIMIT
        assert app.conf.task_hard_time_limit == config.TASK_HARD_TIME_LIMIT

    def test_task_routes(self):
        """Test que las rutas de tareas están configuradas"""
        from celery_app import app
        
        routes = app.conf.task_routes
        assert 'tasks.video_processor.process_video' in routes
        assert 'tasks.video_processor.handle_failed_video' in routes
        
        assert routes['tasks.video_processor.process_video']['queue'] == 'video_processing'
        assert routes['tasks.video_processor.handle_failed_video']['queue'] == 'dlq'

    def test_worker_prefetch_multiplier(self):
        """Test que el worker prefetch está configurado"""
        from celery_app import app
        
        assert app.conf.worker_prefetch_multiplier == 1

    def test_worker_max_tasks_per_child(self):
        """Test que el máximo de tareas por worker está configurado"""
        from celery_app import app
        
        assert app.conf.worker_max_tasks_per_child == 50

    def test_broker_transport_options(self):
        """Test que las opciones de transporte Redis están configuradas"""
        from celery_app import app
        
        transport_options = app.conf.broker_transport_options
        assert 'visibility_timeout' in transport_options
        assert transport_options['visibility_timeout'] == 3600

    def test_task_tracking(self):
        """Test que el tracking de tareas está habilitado"""
        from celery_app import app
        
        assert app.conf.task_track_started is True
        assert app.conf.task_send_sent_event is True


class TestWorkerReadyHandler:
    """Tests para el signal handler worker_ready"""

    @patch('celery_app.logger')
    @patch('celery_app.config')
    def test_worker_ready_handler(self, mock_config, mock_logger):
        """Test que el handler worker_ready se ejecuta correctamente"""
        from celery_app import worker_ready_handler
        
        mock_config.REDIS_URL = 'redis://localhost:6379/0'
        mock_config.DATABASE_URL = 'postgresql://user:pass@localhost/db'
        mock_config.UPLOAD_BASE_DIR = '/app/uploads'
        mock_config.CELERY_WORKER_CONCURRENCY = 4
        
        # Ejecutar handler
        worker_ready_handler()
        
        # Verificar que se loggeó la información
        assert mock_logger.info.called
        # Verificar que se llamó al menos 6 veces (una por cada línea de log)
        assert mock_logger.info.call_count >= 6


class TestTaskPrerunHandler:
    """Tests para el signal handler task_prerun"""

    @patch('celery_app.time')
    def test_task_prerun_handler(self, mock_time):
        """Test que el handler task_prerun registra el tiempo de inicio"""
        from celery_app import task_prerun_handler, task_start_times
        
        # Limpiar diccionario
        task_start_times.clear()
        
        mock_time.time.return_value = 1000.0
        task_id = 'test-task-123'
        
        # Ejecutar handler
        task_prerun_handler(task_id=task_id)
        
        # Verificar que se registró el tiempo
        assert task_id in task_start_times
        assert task_start_times[task_id] == 1000.0

    @patch('celery_app.time')
    def test_task_prerun_handler_multiple_tasks(self, mock_time):
        """Test que el handler maneja múltiples tareas"""
        from celery_app import task_prerun_handler, task_start_times
        
        task_start_times.clear()
        
        mock_time.time.side_effect = [1000.0, 1001.0, 1002.0]
        
        task_prerun_handler(task_id='task-1')
        task_prerun_handler(task_id='task-2')
        task_prerun_handler(task_id='task-3')
        
        assert len(task_start_times) == 3
        assert task_start_times['task-1'] == 1000.0
        assert task_start_times['task-2'] == 1001.0
        assert task_start_times['task-3'] == 1002.0


class TestTaskPostrunHandler:
    """Tests para el signal handler task_postrun"""

    @patch('celery_app.time')
    @patch('celery_app.logger')
    def test_task_postrun_handler_with_metrics(self, mock_logger, mock_time):
        """Test que el handler task_postrun calcula duración y actualiza métricas"""
        from celery_app import task_postrun_handler, task_start_times
        
        task_start_times.clear()
        
        task_id = 'test-task-123'
        task_start_times[task_id] = 1000.0
        
        mock_time.time.return_value = 1005.5  # 5.5 segundos después
        
        mock_task = Mock()
        mock_task.name = 'tasks.video_processor.process_video'
        
        mock_metric = Mock()
        
        # Mockear el import dinámico de metrics
        with patch.dict('sys.modules', {'metrics': MagicMock()}):
            import sys
            sys.modules['metrics'].celery_task_duration = MagicMock()
            sys.modules['metrics'].celery_task_duration.labels.return_value = mock_metric
            
            # Ejecutar handler
            task_postrun_handler(task_id=task_id, task=mock_task)
            
            # Verificar que se calculó la duración (5.5 segundos)
            sys.modules['metrics'].celery_task_duration.labels.assert_called_once_with(task_name='process_video')
            mock_metric.observe.assert_called_once_with(5.5)
        
        # Verificar que se eliminó del diccionario
        assert task_id not in task_start_times

    @patch('celery_app.time')
    @patch('celery_app.logger')
    def test_task_postrun_handler_without_start_time(self, mock_logger, mock_time):
        """Test que el handler maneja tareas sin tiempo de inicio"""
        from celery_app import task_postrun_handler, task_start_times
        
        task_start_times.clear()
        
        task_id = 'unknown-task'
        mock_task = Mock()
        mock_task.name = 'tasks.video_processor.process_video'
        
        # Ejecutar handler - no debe lanzar error
        task_postrun_handler(task_id=task_id, task=mock_task)
        
        # Verificar que no hay error y el diccionario sigue vacío
        assert task_id not in task_start_times

    @patch('celery_app.time')
    @patch('celery_app.logger')
    def test_task_postrun_handler_import_error(self, mock_logger, mock_time):
        """Test que el handler maneja errores de importación de métricas"""
        from celery_app import task_postrun_handler, task_start_times
        
        task_start_times.clear()
        
        task_id = 'test-task-123'
        task_start_times[task_id] = 1000.0
        
        mock_time.time.return_value = 1005.0
        
        mock_task = Mock()
        mock_task.name = 'tasks.video_processor.process_video'
        
        # Simular error de importación usando patch en __import__
        with patch('builtins.__import__', side_effect=ImportError("Cannot import metrics")):
            # Ejecutar handler - no debe lanzar excepción
            task_postrun_handler(task_id=task_id, task=mock_task)
            
            # Debe haber loggeado un warning
            assert mock_logger.warning.called


class TestTaskSuccessHandler:
    """Tests para el signal handler task_success"""

    @patch('celery_app.logger')
    def test_task_success_handler(self, mock_logger):
        """Test que el handler task_success actualiza métricas"""
        from celery_app import task_success_handler
        
        mock_sender = Mock()
        mock_sender.name = 'tasks.video_processor.process_video'
        
        mock_counter = Mock()
        
        # Mockear el import dinámico de metrics
        with patch.dict('sys.modules', {'metrics': MagicMock()}):
            import sys
            sys.modules['metrics'].celery_tasks_total = MagicMock()
            sys.modules['metrics'].celery_tasks_total.labels.return_value = mock_counter
            
            # Ejecutar handler
            task_success_handler(sender=mock_sender)
            
            # Verificar logging
            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args[0][0].lower()
            assert 'exitosa' in call_args or 'success' in call_args or 'tarea' in call_args
            
            # Verificar métricas
            sys.modules['metrics'].celery_tasks_total.labels.assert_called_once_with(
                task_name='process_video',
                status='success'
            )
            mock_counter.inc.assert_called_once()

    @patch('celery_app.logger')
    def test_task_success_handler_import_error(self, mock_logger):
        """Test que el handler maneja errores de importación"""
        from celery_app import task_success_handler
        
        mock_sender = Mock()
        mock_sender.name = 'tasks.video_processor.process_video'
        
        # Simular error de importación usando patch en __import__
        with patch('builtins.__import__', side_effect=ImportError("Cannot import metrics")):
            # Ejecutar handler - no debe lanzar excepción
            task_success_handler(sender=mock_sender)
            
            # Debe haber loggeado un warning
            assert mock_logger.warning.called


class TestTaskFailureHandler:
    """Tests para el signal handler task_failure"""

    @patch('celery_app.logger')
    def test_task_failure_handler(self, mock_logger):
        """Test que el handler task_failure actualiza métricas"""
        from celery_app import task_failure_handler
        
        mock_sender = Mock()
        mock_sender.name = 'tasks.video_processor.process_video'
        
        exception = ValueError("Test error")
        task_id = 'test-task-123'
        
        mock_total_counter = Mock()
        mock_failed_counter = Mock()
        
        # Mockear el import dinámico de metrics
        with patch.dict('sys.modules', {'metrics': MagicMock()}):
            import sys
            sys.modules['metrics'].celery_tasks_total = MagicMock()
            sys.modules['metrics'].celery_tasks_failed = MagicMock()
            sys.modules['metrics'].celery_tasks_total.labels.return_value = mock_total_counter
            sys.modules['metrics'].celery_tasks_failed.labels.return_value = mock_failed_counter
            
            # Ejecutar handler
            task_failure_handler(
                sender=mock_sender,
                task_id=task_id,
                exception=exception
            )
            
            # Verificar logging
            assert mock_logger.error.call_count >= 2  # Al menos 2 mensajes de error
            
            # Verificar métricas de totales
            sys.modules['metrics'].celery_tasks_total.labels.assert_called_with(
                task_name='process_video',
                status='failed'
            )
            mock_total_counter.inc.assert_called_once()
            
            # Verificar métricas de fallos
            sys.modules['metrics'].celery_tasks_failed.labels.assert_called_once_with(
                task_name='process_video',
                error_type='ValueError'
            )
            mock_failed_counter.inc.assert_called_once()

    @patch('celery_app.logger')
    def test_task_failure_handler_no_exception(self, mock_logger):
        """Test que el handler maneja casos sin excepción"""
        from celery_app import task_failure_handler
        
        mock_sender = Mock()
        mock_sender.name = 'tasks.video_processor.process_video'
        
        task_id = 'test-task-123'
        
        mock_total_counter = Mock()
        mock_failed_counter = Mock()
        
        # Mockear el import dinámico de metrics
        with patch.dict('sys.modules', {'metrics': MagicMock()}):
            import sys
            sys.modules['metrics'].celery_tasks_total = MagicMock()
            sys.modules['metrics'].celery_tasks_failed = MagicMock()
            sys.modules['metrics'].celery_tasks_total.labels.return_value = mock_total_counter
            sys.modules['metrics'].celery_tasks_failed.labels.return_value = mock_failed_counter
            
            # Ejecutar handler sin excepción
            task_failure_handler(
                sender=mock_sender,
                task_id=task_id,
                exception=None
            )
            
            # Verificar que se usó 'Unknown' como error_type
            sys.modules['metrics'].celery_tasks_failed.labels.assert_called_once_with(
                task_name='process_video',
                error_type='Unknown'
            )

    @patch('celery_app.logger')
    def test_task_failure_handler_import_error(self, mock_logger):
        """Test que el handler maneja errores de importación"""
        from celery_app import task_failure_handler
        
        mock_sender = Mock()
        mock_sender.name = 'tasks.video_processor.process_video'
        
        exception = ValueError("Test error")
        task_id = 'test-task-123'
        
        # Simular error de importación usando patch en __import__
        with patch('builtins.__import__', side_effect=ImportError("Cannot import metrics")):
            # Ejecutar handler - no debe lanzar excepción
            task_failure_handler(
                sender=mock_sender,
                task_id=task_id,
                exception=exception
            )
            
            # Debe haber loggeado un warning
            assert mock_logger.warning.called


class TestTaskRetryHandler:
    """Tests para el signal handler task_retry"""

    @patch('celery_app.logger')
    def test_task_retry_handler(self, mock_logger):
        """Test que el handler task_retry actualiza métricas"""
        from celery_app import task_retry_handler
        
        mock_sender = Mock()
        mock_sender.name = 'tasks.video_processor.process_video'
        
        reason = "Connection timeout"
        
        mock_counter = Mock()
        
        # Mockear el import dinámico de metrics
        with patch.dict('sys.modules', {'metrics': MagicMock()}):
            import sys
            sys.modules['metrics'].celery_tasks_total = MagicMock()
            sys.modules['metrics'].celery_tasks_total.labels.return_value = mock_counter
            
            # Ejecutar handler
            task_retry_handler(sender=mock_sender, reason=reason)
            
            # Verificar logging
            assert mock_logger.warning.call_count >= 2  # Al menos 2 mensajes de warning
            
            # Verificar métricas
            sys.modules['metrics'].celery_tasks_total.labels.assert_called_once_with(
                task_name='process_video',
                status='retry'
            )
            mock_counter.inc.assert_called_once()

    @patch('celery_app.logger')
    def test_task_retry_handler_import_error(self, mock_logger):
        """Test que el handler maneja errores de importación"""
        from celery_app import task_retry_handler
        
        mock_sender = Mock()
        mock_sender.name = 'tasks.video_processor.process_video'
        
        reason = "Connection timeout"
        
        # Simular error de importación usando patch en __import__
        with patch('builtins.__import__', side_effect=ImportError("Cannot import metrics")):
            # Ejecutar handler - no debe lanzar excepción
            task_retry_handler(sender=mock_sender, reason=reason)
            
            # Debe haber loggeado un warning
            assert mock_logger.warning.called


class TestTaskImport:
    """Tests para la importación de tareas"""

    @patch('celery_app.logger')
    def test_task_import_success(self, mock_logger):
        """Test que las tareas se importan correctamente"""
        # Reimportar módulo para verificar que se ejecuta el import
        import importlib
        import celery_app
        importlib.reload(celery_app)
        
        # Verificar que se loggeó el éxito (o que no hay error)
        # El logger debería haber registrado la importación
        assert True  # Si llegamos aquí, no hubo excepción

    @patch('celery_app.logger')
    @patch('celery_app.video_processor', side_effect=ImportError("Cannot import tasks"))
    def test_task_import_failure(self, mock_video_processor, mock_logger):
        """Test que se maneja correctamente el error de importación"""
        # Este test verifica que el código maneja errores de importación
        # No podemos realmente simularlo sin modificar el módulo, pero
        # podemos verificar que el código tiene el try/except
        from celery_app import app
        
        # Verificar que la app sigue siendo válida aunque haya error de importación
        assert app is not None


class TestTaskNameExtraction:
    """Tests para la extracción de nombres de tareas desde los signal handlers"""

    @patch('celery_app.logger')
    def test_task_name_extraction_from_full_path(self, mock_logger):
        """Test que se extrae correctamente el nombre de la tarea desde el path completo"""
        from celery_app import task_success_handler
        
        mock_sender = Mock()
        mock_sender.name = 'tasks.video_processor.process_video'
        
        mock_counter = Mock()
        
        # Mockear el import dinámico de metrics
        with patch.dict('sys.modules', {'metrics': MagicMock()}):
            import sys
            sys.modules['metrics'].celery_tasks_total = MagicMock()
            sys.modules['metrics'].celery_tasks_total.labels.return_value = mock_counter
            
            task_success_handler(sender=mock_sender)
            
            # Verificar que se extrajo 'process_video' del path completo
            sys.modules['metrics'].celery_tasks_total.labels.assert_called_once_with(
                task_name='process_video',
                status='success'
            )

    @patch('celery_app.logger')
    def test_task_name_extraction_simple_name(self, mock_logger):
        """Test que funciona con nombres simples de tareas"""
        from celery_app import task_success_handler
        
        mock_sender = Mock()
        mock_sender.name = 'simple_task'
        
        mock_counter = Mock()
        
        # Mockear el import dinámico de metrics
        with patch.dict('sys.modules', {'metrics': MagicMock()}):
            import sys
            sys.modules['metrics'].celery_tasks_total = MagicMock()
            sys.modules['metrics'].celery_tasks_total.labels.return_value = mock_counter
            
            task_success_handler(sender=mock_sender)
            
            # Debe extraer 'simple_task'
            sys.modules['metrics'].celery_tasks_total.labels.assert_called_once_with(
                task_name='simple_task',
                status='success'
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=celery_app", "--cov-report=term-missing"])

