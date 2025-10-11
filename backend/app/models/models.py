from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Player(Base):
    """Modelo para los jugadores registrados en la plataforma"""
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
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    videos = relationship("Video", back_populates="player")
    votes = relationship("Vote", back_populates="voter")

    @property
    def username(self):
        """Genera un username basado en el nombre y apellido"""
        return f"{self.first_name.lower()}.{self.last_name.lower()}"


class Video(Base):
    """Modelo para los videos de habilidades subidos por los jugadores"""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    title = Column(String(200), nullable=False)
    filename = Column(String(255), nullable=False)
    status = Column(String(20), default="uploaded")  # uploaded, processing, processed, failed
    original_url = Column(String(500))
    processed_url = Column(String(500))
    votes_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    player = relationship("Player", back_populates="videos")
    votes = relationship("Vote", back_populates="video")
    tasks = relationship("Task", back_populates="video")


class Vote(Base):
    """Modelo para los votos emitidos por los usuarios"""
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    voter_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    video = relationship("Video", back_populates="votes")
    voter = relationship("Player", back_populates="votes")

    # Restricción única: un usuario solo puede votar una vez por video
    __table_args__ = (
        {"extend_existing": True}
    )


class Task(Base):
    """Modelo para las tareas de procesamiento asíncrono"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    task_id = Column(String(100), unique=True, nullable=False)  # ID de la tarea en Celery
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    progress = Column(Float, default=0.0)  # Progreso de 0.0 a 100.0
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    # Relaciones
    video = relationship("Video", back_populates="tasks")
