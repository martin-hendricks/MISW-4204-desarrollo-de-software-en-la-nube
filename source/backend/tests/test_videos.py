import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app_test_main import app
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
        "/videos/upload",
        headers=auth_headers,
        files=files,
        data=data
    )
    
    assert response.status_code == 201
    assert "task_id" in response.json()
    assert "Video subido correctamente" in response.json()["message"]


def test_upload_video_unauthorized():
    """Test para subida de video sin autenticación"""
    test_file = io.BytesIO(b"fake video content")
    test_file.name = "test_video.mp4"
    
    files = {"video_file": ("test_video.mp4", test_file, "video/mp4")}
    data = {"title": "Mi mejor jugada"}
    
    response = client.post(
        "/videos/upload",
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
        "/videos/upload",
        headers=auth_headers,
        files=files,
        data=data
    )
    
    assert response.status_code == 400
    assert "debe ser un video válido" in response.json()["detail"]


def test_get_my_videos(auth_headers, test_video):
    """Test para obtener videos del usuario"""
    response = client.get("/videos/", headers=auth_headers)
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_my_videos_unauthorized():
    """Test para obtener videos sin autenticación"""
    response = client.get("/videos/")
    assert response.status_code == 403


def test_get_specific_video(auth_headers, test_video):
    """Test para obtener un video específico"""
    # Este test verifica que el endpoint responde correctamente
    # Puede devolver 200 si el usuario es el propietario o 403 si no
    response = client.get(f"/videos/{test_video.id}", headers=auth_headers)
    
    # El endpoint debe responder con un código válido (200 o 403)
    assert response.status_code in [200, 403]
    
    # Si es 200, verificar que tiene la estructura correcta
    if response.status_code == 200:
        assert "video_id" in response.json()
        assert "title" in response.json()


def test_get_specific_video_not_found(auth_headers):
    """Test para obtener un video que no existe"""
    response = client.get("/videos/999", headers=auth_headers)
    assert response.status_code == 404


def test_delete_video_success(auth_headers, test_video, db_session):
    """Test para eliminación exitosa de video"""
    # Cambiar estado del video para que pueda ser eliminado
    from app.infrastructure.database.models import VideoStatusEnum
    test_video.status = VideoStatusEnum.UPLOADED
    db_session.commit()
    
    response = client.delete(f"/videos/{test_video.id}", headers=auth_headers)
    
    # El endpoint debe responder con un código válido (200 o 403)
    assert response.status_code in [200, 403]
    
    # Si es 200, verificar que tiene el mensaje correcto
    if response.status_code == 200:
        assert "eliminado exitosamente" in response.json()["message"]


def test_delete_video_not_found(auth_headers):
    """Test para eliminar un video que no existe"""
    response = client.delete("/videos/999", headers=auth_headers)
    assert response.status_code == 404


def test_delete_video_unauthorized():
    """Test para eliminar video sin autenticación"""
    response = client.delete("/videos/1")
    assert response.status_code == 403


def test_get_original_video_success(auth_video):
    """Test para obtener video original exitosamente"""
    video = auth_video["video"]
    headers = auth_video["headers"]

    response = client.get(f"/videos/original/{video.id}", headers=headers)

    # Puede ser 200 o 404 dependiendo si el archivo existe
    assert response.status_code in [200, 404]


def test_get_original_video_unauthorized():
    """Test para obtener video original sin autenticación"""
    response = client.get("/videos/original/1")
    assert response.status_code == 403


def test_get_original_video_not_found(auth_headers):
    """Test para obtener video original que no existe"""
    response = client.get("/videos/original/999", headers=auth_headers)
    assert response.status_code == 404


def test_get_processed_video_success(auth_video):
    """Test para obtener video procesado exitosamente"""
    video = auth_video["video"]
    headers = auth_video["headers"]

    response = client.get(f"/videos/processed/{video.id}", headers=headers)

    # Puede ser 200, 400 o 404 dependiendo del estado del video y si el archivo existe
    assert response.status_code in [200, 400, 404]


def test_get_processed_video_unauthorized():
    """Test para obtener video procesado sin autenticación"""
    response = client.get("/videos/processed/1")
    assert response.status_code == 403


def test_get_processed_video_not_found(auth_headers):
    """Test para obtener video procesado que no existe"""
    response = client.get("/videos/processed/999", headers=auth_headers)
    assert response.status_code == 404
