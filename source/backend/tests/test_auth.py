import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app_test_main import app

client = TestClient(app)


def test_signup_success():
    """Test para registro exitoso de usuario"""
    import uuid
    unique_email = f"john.doe.{uuid.uuid4().hex[:8]}@example.com"
    user_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": unique_email,
        "password1": "StrongPass123",
        "password2": "StrongPass123",
        "city": "Bogotá",
        "country": "Colombia"
    }
    
    response = client.post("/auth/signup", json=user_data)
    if response.status_code != 201:
        print(f"Error response: {response.json()}")
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
    client.post("/auth/signup", json=user_data)
    
    # Segundo registro con mismo email
    response = client.post("/auth/signup", json=user_data)
    assert response.status_code == 400
    assert "ya está registrado" in response.json()["detail"]


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
    
    response = client.post("/auth/signup", json=user_data)
    assert response.status_code == 422
    assert "Las contraseñas no coinciden" in str(response.json())


def test_login_success():
    """Test para login exitoso"""
    import uuid
    unique_email = f"jane.smith.{uuid.uuid4().hex[:8]}@example.com"
    # Primero crear un usuario
    user_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": unique_email,
        "password1": "StrongPass123",
        "password2": "StrongPass123",
        "city": "Medellín",
        "country": "Colombia"
    }
    client.post("/auth/signup", json=user_data)
    
    # Luego hacer login
    login_data = {
        "email": unique_email,
        "password": "StrongPass123"
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "Bearer"


def test_login_invalid_credentials():
    """Test para login con credenciales inválidas"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword"
    }
    
    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Credenciales inválidas" in response.json()["detail"]


def test_get_current_user():
    """Test para obtener información del usuario actual"""
    import uuid
    unique_email = f"test.user.{uuid.uuid4().hex[:8]}@example.com"
    
    # Primero crear un usuario
    user_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": unique_email,
        "password1": "StrongPass123",
        "password2": "StrongPass123",
        "city": "Bogotá",
        "country": "Colombia"
    }
    client.post("/auth/signup", json=user_data)
    
    # Luego hacer login para obtener token
    login_data = {
        "email": unique_email,
        "password": "StrongPass123"
    }
    login_response = client.post("/auth/login", json=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Ahora probar el endpoint /auth/me
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    assert "email" in response.json()
    assert "first_name" in response.json()


def test_get_current_user_unauthorized():
    """Test para obtener usuario actual sin autenticación"""
    response = client.get("/auth/me")
    assert response.status_code == 403
