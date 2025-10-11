import pytest
from fastapi.testclient import TestClient
from app.main import app
import io

client = TestClient(app)


def test_upload_video_success(auth_headers):
    """Test para subida exitosa de video"""
    # Crear un archivo de prueba
    test_file = io.BytesIO(b"fake video content")
    test_file.name = "test_video.mp4"
    
    files = {"video_file": ("test_video.mp4", test_file, "video/mp4")}
    data = {"title": "Mi mejor jugada"}
    
    response = client.post(
        "/api/videos/upload",
        headers=auth_headers,
        files=files,
        data=data
    )
    
    assert response.status_code == 201
    assert "task_id" in response.json()
    assert "Video subido exitosamente" in response.json()["message"]


def test_upload_video_unauthorized():
    """Test para subida de video sin autenticación"""
    test_file = io.BytesIO(b"fake video content")
    test_file.name = "test_video.mp4"
    
    files = {"video_file": ("test_video.mp4", test_file, "video/mp4")}
    data = {"title": "Mi mejor jugada"}
    
    response = client.post(
        "/api/videos/upload",
        files=files,
        data=data
    )
    
    assert response.status_code == 403


def test_upload_video_invalid_file_type(auth_headers):
    """Test para subida de archivo con tipo inválido"""
    test_file = io.BytesIO(b"fake content")
    test_file.name = "test_file.txt"
    
    files = {"video_file": ("test_file.txt", test_file, "text/plain")}
    data = {"title": "Mi mejor jugada"}
    
    response = client.post(
        "/api/videos/upload",
        headers=auth_headers,
        files=files,
        data=data
    )
    
    assert response.status_code == 400
    assert "Tipo de archivo no permitido" in response.json()["detail"]


def test_get_my_videos(auth_headers, test_video):
    """Test para obtener videos del usuario"""
    response = client.get("/api/videos/", headers=auth_headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_my_videos_unauthorized():
    """Test para obtener videos sin autenticación"""
    response = client.get("/api/videos/")
    assert response.status_code == 403


def test_get_specific_video(auth_headers, test_video):
    """Test para obtener un video específico"""
    response = client.get(f"/api/videos/{test_video.id}", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["id"] == test_video.id
    assert response.json()["title"] == test_video.title


def test_get_specific_video_not_found(auth_headers):
    """Test para obtener un video que no existe"""
    response = client.get("/api/videos/999", headers=auth_headers)
    assert response.status_code == 404


def test_delete_video_success(auth_headers, test_video, db_session):
    """Test para eliminación exitosa de video"""
    # Cambiar estado del video para que pueda ser eliminado
    test_video.status = "uploaded"
    db_session.commit()
    
    response = client.delete(f"/api/videos/{test_video.id}", headers=auth_headers)
    
    assert response.status_code == 200
    assert "eliminado exitosamente" in response.json()["message"]


def test_delete_video_not_found(auth_headers):
    """Test para eliminar un video que no existe"""
    response = client.delete("/api/videos/999", headers=auth_headers)
    assert response.status_code == 404


def test_delete_video_unauthorized():
    """Test para eliminar video sin autenticación"""
    response = client.delete("/api/videos/1")
    assert response.status_code == 403
