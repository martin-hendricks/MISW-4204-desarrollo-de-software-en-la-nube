import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_signup_success():
    """Test para registro exitoso de usuario"""
    user_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password1": "StrongPass123",
        "password2": "StrongPass123",
        "city": "Bogotá",
        "country": "Colombia"
    }
    
    response = client.post("/api/auth/signup", json=user_data)
    assert response.status_code == 201
    assert "Usuario creado exitosamente" in response.json()["message"]


def test_signup_duplicate_email():
    """Test para registro con email duplicado"""
    user_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password1": "StrongPass123",
        "password2": "StrongPass123",
        "city": "Bogotá",
        "country": "Colombia"
    }
    
    # Primer registro
    client.post("/api/auth/signup", json=user_data)
    
    # Segundo registro con mismo email
    response = client.post("/api/auth/signup", json=user_data)
    assert response.status_code == 400
    assert "El email ya está registrado" in response.json()["detail"]


def test_signup_password_mismatch():
    """Test para registro con contraseñas que no coinciden"""
    user_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe2@example.com",
        "password1": "StrongPass123",
        "password2": "DifferentPass123",
        "city": "Bogotá",
        "country": "Colombia"
    }
    
    response = client.post("/api/auth/signup", json=user_data)
    assert response.status_code == 422
    assert "Las contraseñas no coinciden" in str(response.json())


def test_login_success():
    """Test para login exitoso"""
    # Primero crear un usuario
    user_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "password1": "StrongPass123",
        "password2": "StrongPass123",
        "city": "Medellín",
        "country": "Colombia"
    }
    client.post("/api/auth/signup", json=user_data)
    
    # Luego hacer login
    login_data = {
        "email": "jane.smith@example.com",
        "password": "StrongPass123"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_invalid_credentials():
    """Test para login con credenciales inválidas"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword"
    }
    
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Credenciales inválidas" in response.json()["detail"]


def test_get_current_user(auth_headers):
    """Test para obtener información del usuario actual"""
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert "email" in response.json()
    assert "first_name" in response.json()


def test_get_current_user_unauthorized():
    """Test para obtener usuario actual sin autenticación"""
    response = client.get("/api/auth/me")
    assert response.status_code == 403
