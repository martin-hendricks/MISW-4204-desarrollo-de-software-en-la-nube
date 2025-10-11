import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import get_db, Base
from app.models.models import Player, Video, Vote, Task
from app.auth import get_password_hash
import os

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
    player = Player(
        first_name="Test",
        last_name="Player",
        email="test@example.com",
        password_hash=get_password_hash("testpassword"),
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
    video = Video(
        player_id=test_player.id,
        title="Test Video",
        filename="test_video.mp4",
        status="processed",
        original_url="/uploads/test_video.mp4",
        processed_url="/uploads/processed_test_video.mp4",
        votes_count=0
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
    response = client.post("/api/auth/login", json=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
