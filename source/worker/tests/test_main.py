"""
Tests comprehensivos para la API de Health Check del Worker
Cubre todos los endpoints, casos de éxito, errores y edge cases
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import patch, MagicMock, Mock, PropertyMock
import os
from main import app


class TestRootEndpoint:
    """Tests para el endpoint raíz (/)"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_root_endpoint_status(self, client):
        """Test que el endpoint raíz retorna 200"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_endpoint_service_name(self, client):
        """Test que el endpoint raíz contiene el nombre del servicio"""
        response = client.get("/")
        data = response.json()
        assert data["service"] == "ANB Video Processing Worker"
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
    
    def test_root_endpoint_contains_endpoints(self, client):
        """Test que el endpoint raíz lista los endpoints disponibles"""
        response = client.get("/")
        data = response.json()
        assert "endpoints" in data
        assert "health" in data["endpoints"]
        assert "health_detailed" in data["endpoints"]
        assert "celery_stats" in data["endpoints"]
        assert "metrics" in data["endpoints"]


class TestHealthCheck:
    """Tests para el endpoint /health"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_health_check_status(self, client):
        """Test que /health retorna 200"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_check_response_structure(self, client):
        """Test estructura de respuesta de /health"""
        response = client.get("/health")
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "worker"
        assert data["version"] == "1.0.0"
        assert "checks" in data
        assert data["checks"]["api"] is True
    
    def test_health_check_uses_health_response_model(self, client):
        """Test que /health usa el modelo HealthResponse"""
        response = client.get("/health")
        data = response.json()
        
        # Verificar que tiene todos los campos del modelo
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "checks" in data


class TestDetailedHealthCheck:
    """Tests para el endpoint /health/detailed"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch("main.test_db_connection")
    @patch("main.celery_app")
    @patch("main.config")
    def test_detailed_health_check_all_healthy(
        self, mock_config, mock_celery, mock_db_connection, client
    ):
        """Test health check detallado cuando todo está saludable"""
        mock_db_connection.return_value = True
        mock_celery.backend.client.ping.return_value = True
        
        # Configurar valores JSON serializables
        mock_config.ORIGINAL_DIR = "/test/original"
        mock_config.PROCESSED_DIR = "/test/processed"
        mock_config.TEMP_DIR = "/test/temp"
        mock_config.REDIS_URL = "redis://localhost:6379/0"
        mock_config.UPLOAD_BASE_DIR = "/test"
        mock_config.CELERY_TASK_MAX_RETRIES = 3
        mock_config.CELERY_WORKER_CONCURRENCY = 4
        
        with patch("os.path.exists") as mock_exists, \
             patch("os.access") as mock_access, \
             patch("subprocess.run") as mock_subprocess:
            mock_exists.return_value = True
            mock_access.return_value = True
            mock_subprocess.return_value = Mock(returncode=0)
            
            response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["checks"]["postgresql"] is True
        assert data["checks"]["redis"] is True
        assert "config" in data
    
    @patch("main.test_db_connection")
    @patch("main.celery_app")
    def test_detailed_health_check_postgresql_failure(
        self, mock_celery, mock_db_connection, client
    ):
        """Test health check cuando PostgreSQL falla"""
        mock_db_connection.return_value = False
        mock_celery.backend.client.ping.return_value = True
        
        with patch("os.path.exists", return_value=True), \
             patch("os.access", return_value=True), \
             patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=0)
            
            response = client.get("/health/detailed")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["postgresql"] is False
    
    @patch("main.test_db_connection")
    @patch("main.celery_app")
    def test_detailed_health_check_redis_failure(
        self, mock_celery, mock_db_connection, client
    ):
        """Test health check cuando Redis falla"""
        mock_db_connection.return_value = True
        mock_celery.backend.client.ping.side_effect = Exception("Redis error")
        
        with patch("redis.from_url") as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            
            with patch("os.path.exists", return_value=True), \
                 patch("os.access", return_value=True), \
                 patch("subprocess.run") as mock_subprocess:
                mock_subprocess.return_value = Mock(returncode=0)
                
                response = client.get("/health/detailed")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["redis"] is False
    
    @patch("main.test_db_connection")
    @patch("main.celery_app")
    @patch("main.config")
    def test_detailed_health_check_storage_failure(
        self, mock_config, mock_celery, mock_db_connection, client
    ):
        """Test health check cuando los directorios de almacenamiento fallan"""
        mock_db_connection.return_value = True
        mock_celery.backend.client.ping.return_value = True
        
        # Configurar valores simples (no properties) para que sean JSON serializables
        mock_config.ORIGINAL_DIR = "/test/original"
        mock_config.PROCESSED_DIR = "/test/processed"
        mock_config.TEMP_DIR = "/test/temp"
        mock_config.UPLOAD_BASE_DIR = "/test"
        mock_config.CELERY_TASK_MAX_RETRIES = 3
        mock_config.CELERY_WORKER_CONCURRENCY = 4
        mock_config.REDIS_URL = "redis://localhost:6379/0"
        
        with patch("os.path.exists", return_value=False), \
             patch("os.access", return_value=False), \
             patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=0)
            
            response = client.get("/health/detailed")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "messages" in data or "checks" in data
    
    @patch("main.test_db_connection")
    @patch("main.celery_app")
    def test_detailed_health_check_ffmpeg_failure(
        self, mock_celery, mock_db_connection, client
    ):
        """Test health check cuando FFmpeg falla"""
        mock_db_connection.return_value = True
        mock_celery.backend.client.ping.return_value = True
        
        with patch("os.path.exists", return_value=True), \
             patch("os.access", return_value=True), \
             patch("subprocess.run") as mock_subprocess:
            mock_subprocess.side_effect = FileNotFoundError("ffmpeg not found")
            
            response = client.get("/health/detailed")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["checks"]["ffmpeg"] is False
    
    @patch("main.test_db_connection")
    @patch("main.celery_app")
    @patch("main.config")
    def test_detailed_health_check_redis_fallback(
        self, mock_config, mock_celery, mock_db_connection, client
    ):
        """Test que health check usa fallback de Redis directo"""
        mock_db_connection.return_value = True
        mock_celery.backend.client.ping.side_effect = Exception("Backend error")
        
        # Configurar valores JSON serializables
        mock_config.REDIS_URL = "redis://localhost:6379/0"
        mock_config.UPLOAD_BASE_DIR = "/test"
        mock_config.CELERY_TASK_MAX_RETRIES = 3
        mock_config.CELERY_WORKER_CONCURRENCY = 4
        
        with patch("redis.from_url") as mock_redis, \
             patch("os.path.exists", return_value=True), \
             patch("os.access", return_value=True), \
             patch("subprocess.run") as mock_subprocess:
            mock_redis_instance = MagicMock()
            mock_redis_instance.ping.return_value = True
            mock_redis.return_value = mock_redis_instance
            mock_subprocess.return_value = Mock(returncode=0)
            
            response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["checks"]["redis"] is True
    
    @patch("main.test_db_connection")
    def test_detailed_health_check_db_exception(self, mock_db_connection, client):
        """Test health check cuando test_db_connection lanza excepción"""
        mock_db_connection.side_effect = Exception("Database connection error")
        
        with patch("main.celery_app") as mock_celery, \
             patch("os.path.exists", return_value=True), \
             patch("os.access", return_value=True), \
             patch("subprocess.run") as mock_subprocess:
            mock_celery.backend.client.ping.return_value = True
            mock_subprocess.return_value = Mock(returncode=0)
            
            response = client.get("/health/detailed")
        
        assert response.status_code == 503
        data = response.json()
        assert data["checks"]["postgresql"] is False
        assert "messages" in data


class TestMetricsEndpoint:
    """Tests para el endpoint /metrics"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch("main.celery_app")
    @patch("main.generate_multiprocess_metrics")
    @patch("main.config")
    def test_metrics_endpoint_success(
        self, mock_config, mock_generate, mock_celery, client
    ):
        """Test endpoint de métricas cuando todo funciona"""
        mock_config.REDIS_URL = "redis://localhost:6379/0"
        
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = {"worker1": [{"id": "task1"}]}
        mock_inspect.reserved.return_value = {"worker1": [{"id": "task2"}]}
        mock_celery.control.inspect.return_value = mock_inspect
        
        mock_generate.return_value = b'# HELP test_metric\n'
        
        with patch("redis.from_url") as mock_redis:
            mock_redis_instance = MagicMock()
            mock_redis_instance.llen.return_value = 5
            mock_redis.return_value = mock_redis_instance
            
            response = client.get("/metrics")
        
        assert response.status_code == 200
        # Verificar content-type (puede tener charset duplicado)
        assert "text/plain" in response.headers["content-type"]
        assert "version=0.0.4" in response.headers["content-type"]
        assert isinstance(response.content, bytes)
    
    @patch("main.celery_app")
    @patch("main.generate_multiprocess_metrics")
    def test_metrics_endpoint_no_active_tasks(
        self, mock_generate, mock_celery, client
    ):
        """Test endpoint de métricas cuando no hay tareas activas"""
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = None
        mock_inspect.reserved.return_value = None
        mock_celery.control.inspect.return_value = mock_inspect
        
        mock_generate.return_value = b'# HELP test_metric\n'
        
        with patch("redis.from_url"):
            response = client.get("/metrics")
        
        assert response.status_code == 200
    
    @patch("main.celery_app")
    @patch("main.generate_multiprocess_metrics")
    @patch("main.logger")
    def test_metrics_endpoint_redis_error(
        self, mock_logger, mock_generate, mock_celery, client
    ):
        """Test endpoint de métricas cuando Redis falla"""
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = {}
        mock_inspect.reserved.return_value = {}
        mock_celery.control.inspect.return_value = mock_inspect
        
        mock_generate.return_value = b'# HELP test_metric\n'
        
        with patch("redis.from_url", side_effect=Exception("Redis error")):
            response = client.get("/metrics")
        
        assert response.status_code == 200  # Aún retorna métricas aunque Redis falle
        mock_logger.warning.assert_called()
    
    @patch("main.celery_app")
    @patch("main.generate_multiprocess_metrics")
    @patch("main.logger")
    def test_metrics_endpoint_celery_error(
        self, mock_logger, mock_generate, mock_celery, client
    ):
        """Test endpoint de métricas cuando Celery falla"""
        mock_celery.control.inspect.side_effect = Exception("Celery error")
        
        mock_generate.return_value = b'# HELP test_metric\n'
        
        response = client.get("/metrics")
        
        assert response.status_code == 200  # Aún retorna métricas aunque Celery falle
        mock_logger.warning.assert_called()


class TestCeleryStats:
    """Tests para el endpoint /celery/stats"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch("main.celery_app")
    def test_celery_stats_success(self, mock_celery, client):
        """Test endpoint de stats cuando funciona"""
        mock_inspect = MagicMock()
        mock_inspect.active.return_value = {"worker1": []}
        mock_inspect.reserved.return_value = {"worker1": []}
        mock_inspect.registered.return_value = {"worker1": ["task1", "task2"]}
        mock_inspect.stats.return_value = {"worker1": {"total": 100}}
        mock_celery.control.inspect.return_value = mock_inspect
        
        response = client.get("/celery/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "celery_stats" in data
        assert "active_tasks" in data["celery_stats"]
        assert "reserved_tasks" in data["celery_stats"]
        assert "registered_tasks" in data["celery_stats"]
        assert "stats" in data["celery_stats"]
    
    @patch("main.celery_app")
    @patch("main.logger")
    def test_celery_stats_error(self, mock_logger, mock_celery, client):
        """Test endpoint de stats cuando falla"""
        mock_celery.control.inspect.side_effect = Exception("Inspect error")
        
        response = client.get("/celery/stats")
        
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert "message" in data
        mock_logger.error.assert_called_once()


class TestCeleryPing:
    """Tests para el endpoint /celery/ping"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch("main.celery_app")
    def test_celery_ping_success(self, mock_celery, client):
        """Test ping cuando hay workers activos"""
        mock_celery.control.ping.return_value = [
            {"worker1": {"ok": "pong"}},
            {"worker2": {"ok": "pong"}}
        ]
        
        response = client.get("/celery/ping")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["workers_online"] == 2
        assert "workers" in data
    
    @patch("main.celery_app")
    def test_celery_ping_no_workers(self, mock_celery, client):
        """Test ping cuando no hay workers"""
        mock_celery.control.ping.return_value = None
        
        response = client.get("/celery/ping")
        
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "no_workers"
        assert "message" in data
    
    @patch("main.celery_app")
    @patch("main.logger")
    def test_celery_ping_error(self, mock_logger, mock_celery, client):
        """Test ping cuando hay error"""
        mock_celery.control.ping.side_effect = Exception("Connection error")
        
        response = client.get("/celery/ping")
        
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert "message" in data
        mock_logger.error.assert_called_once()


class TestAppConfiguration:
    """Tests para configuración de la aplicación FastAPI"""
    
    def test_app_exists(self):
        """Test que la aplicación FastAPI existe"""
        assert app is not None
    
    def test_app_title(self):
        """Test que la aplicación tiene título correcto"""
        assert app.title == "ANB Worker Health API"
    
    def test_app_version(self):
        """Test que la aplicación tiene versión correcta"""
        assert app.version == "1.0.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=main", "--cov-report=term-missing"])
