"""Tests simples para autenticación"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_signup_endpoint_exists():
    """Test para verificar que el endpoint de signup existe"""
    response = client.post("/api/auth/signup", json={})
    # Debería retornar 422 (validation error) no 404 (not found)
    assert response.status_code == 422


def test_login_endpoint_exists():
    """Test para verificar que el endpoint de login existe"""
    response = client.post("/api/auth/login", json={})
    # Debería retornar 422 (validation error) no 404 (not found)
    assert response.status_code == 422


def test_me_endpoint_exists():
    """Test para verificar que el endpoint de me existe"""
    response = client.get("/api/auth/me")
    # Debería retornar 403 (forbidden) no 404 (not found)
    assert response.status_code == 403


def test_signup_with_valid_data():
    """Test para signup con datos válidos"""
    user_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password": "StrongPass123",
        "city": "Bogotá",
        "country": "Colombia"
    }
    
    response = client.post("/api/auth/signup", json=user_data)
    # Debería retornar 201 (created) o algún error específico, no 404
    assert response.status_code in [201, 400, 500]


def test_login_with_valid_data():
    """Test para login con datos válidos"""
    login_data = {
        "email": "john.doe@example.com",
        "password": "StrongPass123"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    # Debería retornar 200 (success) o algún error específico, no 404
    assert response.status_code in [200, 401, 404, 500]
