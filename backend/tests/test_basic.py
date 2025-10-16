"""Tests básicos para verificar que la aplicación funciona"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test para el endpoint raíz"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "ANB Rising Stars Showcase API" in data["message"]


def test_health_endpoint():
    """Test para el endpoint de salud"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "backend"


def test_config_endpoint():
    """Test para el endpoint de configuración"""
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "file_storage_type" in data
    assert "database_url" in data


def test_docs_endpoint():
    """Test para el endpoint de documentación"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_redoc_endpoint():
    """Test para el endpoint de ReDoc"""
    response = client.get("/redoc")
    assert response.status_code == 200
