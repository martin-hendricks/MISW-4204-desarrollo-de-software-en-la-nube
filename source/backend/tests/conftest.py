import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.database.database import get_db, Base
from app.infrastructure.external_services.jwt_auth_service import JWTAuthService
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import os
import sys

# Importar la app de tests que maneja la configuración correctamente
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app_test_main import app

# Usar los modelos existentes de la aplicación
from app.infrastructure.database.models import PlayerModel, VideoModel

# Base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear tablas de prueba
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def db_session():
    """Fixture para obtener una sesión de base de datos de prueba"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def clean_database():
    """Fixture que limpia la base de datos antes de cada test"""
    # Limpiar todas las tablas antes de cada test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Limpiar después de cada test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def test_player(db_session):
    """Fixture para crear un jugador de prueba"""
    import asyncio
    auth_service = JWTAuthService()
    password_hash = asyncio.run(auth_service.hash_password("testpassword"))
    
    player = PlayerModel(
        first_name="Test",
        last_name="Player",
        email="test@example.com",
        password_hash=password_hash,
        city="Bogotá",
        country="Colombia"
    )
    db_session.add(player)
    db_session.commit()
    db_session.refresh(player)
    return player


@pytest.fixture
def test_video(db_session, test_player):
    """Fixture para crear un video de prueba"""
    from app.infrastructure.database.models import VideoStatusEnum
    video = VideoModel(
        player_id=test_player.id,
        title="Test Video",
        status=VideoStatusEnum.PROCESSED,
        original_url="/uploads/test_video.mp4",
        processed_url="/uploads/processed_test_video.mp4",
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    return video


@pytest.fixture
def auth_headers(test_player):
    """Fixture para obtener headers de autenticación"""
    # Simular login para obtener token
    login_data = {
        "email": test_player.email,
        "password": "testpassword"
    }
    response = client.post("/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        # Si falla el login, crear un usuario y hacer login
        import uuid
        unique_email = f"test.user.{uuid.uuid4().hex[:8]}@example.com"
        
        # Crear usuario
        user_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": unique_email,
            "password1": "testpassword",
            "password2": "testpassword",
            "city": "Bogotá",
            "country": "Colombia"
        }
        client.post("/auth/signup", json=user_data)
        
        # Hacer login
        login_data = {
            "email": unique_email,
            "password": "testpassword"
        }
        response = client.post("/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()["access_token"]
            return {"Authorization": f"Bearer {token}"}
        else:
            return {}


@pytest.fixture
def auth_video(auth_headers, db_session):
    """Fixture para crear un video del usuario autenticado"""
    from app.infrastructure.database.models import VideoModel, VideoStatusEnum
    import uuid
    
    # Crear un usuario específico para el video
    import asyncio
    auth_service = JWTAuthService()
    password_hash = asyncio.run(auth_service.hash_password("testpassword"))
    
    player = PlayerModel(
        first_name="Video",
        last_name="Owner",
        email=f"video.owner.{uuid.uuid4().hex[:8]}@example.com",
        password_hash=password_hash,
        city="Bogotá",
        country="Colombia"
    )
    db_session.add(player)
    db_session.commit()
    db_session.refresh(player)
    
    video = VideoModel(
        player_id=player.id,
        title="Auth Test Video",
        status=VideoStatusEnum.PROCESSED,
        original_url="/uploads/auth_test_video.mp4",
        processed_url="/uploads/processed_auth_test_video.mp4",
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    
    # Crear headers para este usuario específico
    login_data = {
        "email": player.email,
        "password": "testpassword"
    }
    response = client.post("/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        return {"video": video, "headers": headers}
    else:
        return {"video": video, "headers": {}}
