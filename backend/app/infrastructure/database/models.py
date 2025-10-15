"""Modelos SQLAlchemy para la base de datos"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database.database import Base
import enum


class PlayerModel(Base):
    """Modelo SQLAlchemy para Players"""
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relaciones
    videos = relationship("VideoModel", back_populates="player", cascade="all, delete-orphan")
    votes = relationship("VoteModel", back_populates="player", cascade="all, delete-orphan")


class VideoStatusEnum(str, enum.Enum):
    """Enum para estados de video"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class VideoModel(Base):
    """Modelo SQLAlchemy para Videos"""
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    status = Column(Enum(VideoStatusEnum, name='video_status', create_type=False, values_callable=lambda x: [e.value for e in x]), default=VideoStatusEnum.UPLOADED, nullable=False)
    original_url = Column(String(500))
    processed_url = Column(String(500))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relaciones
    player = relationship("PlayerModel", back_populates="videos")
    votes = relationship("VoteModel", back_populates="video", cascade="all, delete-orphan")


class VoteModel(Base):
    """Modelo SQLAlchemy para Votes"""
    __tablename__ = "votes"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relaciones
    video = relationship("VideoModel", back_populates="votes")
    player = relationship("PlayerModel", back_populates="votes")
    
    # Constraint para evitar votos duplicados
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

