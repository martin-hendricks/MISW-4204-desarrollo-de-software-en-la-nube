import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.infrastructure.database.database import get_db, Base
from app.infrastructure.external_services.jwt_auth_service import JWTAuthService
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import os

# Modelos SQLAlchemy para tests
class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    title = Column(String(200), nullable=False)
    filename = Column(String(255), nullable=False)
    status = Column(String(20), default="uploaded")
    original_url = Column(String(500))
    processed_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
async def test_player(db_session):
    """Fixture para crear un jugador de prueba"""
    auth_service = JWTAuthService()
    password_hash = await auth_service.hash_password("testpassword")
    
    player = Player(
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
async def test_video(db_session, test_player):
    """Fixture para crear un video de prueba"""
    video = Video(
        player_id=test_player.id,
        title="Test Video",
        filename="test_video.mp4",
        status="processed",
        original_url="/uploads/test_video.mp4",
        processed_url="/uploads/processed_test_video.mp4",
    )
    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)
    return video


@pytest.fixture
async def auth_headers(test_player):
    """Fixture para obtener headers de autenticación"""
    # Simular login para obtener token
    login_data = {
        "email": test_player.email,
        "password": "testpassword"
    }
    response = client.post("/api/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    else:
        # Si falla el login, retornar headers vacíos
        return {}
