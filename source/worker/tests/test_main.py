"""
Tests básicos para la API de Health Check del Worker
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app


class TestHealthAPI:
    """Tests básicos para health check"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test endpoint raíz"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "ANB Video Processing Worker"
        assert data["status"] == "running"
    
    def test_health_check_basic(self, client):
        """Test health check básico"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "worker"
    
    @patch("main.test_db_connection")
    @patch("main.celery_app")
    def test_detailed_health_check(
        self, mock_celery, mock_db_connection, client
    ):
        """Test health check detallado"""
        mock_db_connection.return_value = True
        mock_celery.backend.client.ping.return_value = True
        
        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            response = client.get("/health/detailed")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestCeleryEndpoints:
    """Tests básicos para endpoints de Celery"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @patch("main.celery_app")
    def test_celery_ping(self, mock_celery, client):
        """Test ping a workers de Celery"""
        mock_celery.control.ping.return_value = [{"worker1": {"ok": "pong"}}]
        
        response = client.get("/celery/ping")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

