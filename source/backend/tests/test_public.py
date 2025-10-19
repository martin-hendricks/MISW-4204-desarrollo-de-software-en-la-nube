import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app_test_main import app

client = TestClient(app)


def test_list_videos_for_voting(test_video):
    """Test para listar videos disponibles para votación"""
    response = client.get("/public/videos")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_vote_for_video_success(auth_headers, test_video):
    """Test para votar por un video exitosamente"""
    response = client.post(
        f"/public/videos/{test_video.id}/vote",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    assert "Voto registrado exitosamente" in response.json()["message"]


def test_vote_for_video_duplicate(auth_headers, test_video):
    """Test para votar dos veces por el mismo video"""
    # Primer voto
    client.post(
        f"/public/videos/{test_video.id}/vote",
        headers=auth_headers
    )
    
    # Segundo voto (debería fallar)
    response = client.post(
        f"/public/videos/{test_video.id}/vote",
        headers=auth_headers
    )
    
    assert response.status_code == 400
    assert "Ya has votado por este video" in response.json()["detail"]


def test_vote_for_video_unauthorized(test_video):
    """Test para votar sin autenticación"""
    response = client.post(f"/public/videos/{test_video.id}/vote")
    assert response.status_code == 403


def test_vote_for_nonexistent_video(auth_headers):
    """Test para votar por un video que no existe"""
    response = client.post(
        "/public/videos/999/vote",
        headers=auth_headers
    )
    
    assert response.status_code == 404


def test_get_rankings():
    """Test para obtener rankings sin filtro"""
    response = client.get("/public/rankings")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_rankings_with_city_filter():
    """Test para obtener rankings con filtro de ciudad"""
    response = client.get("/public/rankings?city=Bogotá")
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_rankings_invalid_city():
    """Test para obtener rankings con ciudad vacía"""
    response = client.get("/public/rankings?city=")
    
    assert response.status_code == 400
    assert "inválido" in response.json()["detail"]


def test_health_check():
    """Test para el endpoint de health check"""
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """Test para el endpoint raíz"""
    response = client.get("/")
    
    assert response.status_code == 200
    assert "ANB Rising Stars Showcase API" in response.json()["message"]
    assert "docs" in response.json()
