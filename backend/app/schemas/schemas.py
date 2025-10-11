from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class VideoStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Esquemas para autenticación
class PlayerSignup(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password1: str
    password2: str
    city: str
    country: str

    @validator('password2')
    def passwords_match(cls, v, values, **kwargs):
        if 'password1' in values and v != values['password1']:
            raise ValueError('Las contraseñas no coinciden')
        return v

    @validator('password1')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if len(v) > 72:
            raise ValueError('La contraseña no puede tener más de 72 caracteres')
        return v


class PlayerLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# Esquemas para jugadores
class PlayerBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    city: str
    country: str


class PlayerCreate(PlayerBase):
    password: str


class Player(PlayerBase):
    id: int
    is_active: bool
    created_at: datetime
    username: str

    class Config:
        from_attributes = True


# Esquemas para videos
class VideoBase(BaseModel):
    title: str


class VideoCreate(VideoBase):
    pass


class Video(VideoBase):
    id: int
    player_id: int
    filename: str
    status: VideoStatus
    original_url: Optional[str]
    processed_url: Optional[str]
    votes_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class VideoDetail(Video):
    player: Player


class VideoUploadResponse(BaseModel):
    task_id: str
    message: str


# Esquemas para votos
class VoteCreate(BaseModel):
    video_id: int


class Vote(VoteCreate):
    id: int
    voter_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Esquemas para tareas
class TaskBase(BaseModel):
    video_id: int
    status: TaskStatus
    progress: float


class Task(TaskBase):
    id: int
    task_id: str
    error_message: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Esquemas para rankings
class PlayerRanking(BaseModel):
    position: int
    username: str
    city: str
    votes: int


class RankingResponse(BaseModel):
    rankings: List[PlayerRanking]
    total_players: int


# Esquemas para respuestas de error
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


# Esquemas para respuestas de éxito
class SuccessResponse(BaseModel):
    message: str


class VideoDeleteResponse(SuccessResponse):
    pass


class VoteResponse(SuccessResponse):
    pass
