from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class PlayerCreateDTO(BaseModel):
    """DTO para crear un jugador"""
    first_name: str
    last_name: str
    email: str
    password1: str
    password2: str
    city: str
    country: str
    
    @field_validator('password2')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password1' in info.data and v != info.data['password1']:
            raise ValueError('Las contraseñas no coinciden')
        return v


class PlayerLoginDTO(BaseModel):
    """DTO para login de jugador"""
    email: str
    password: str


class PlayerResponseDTO(BaseModel):
    """DTO de respuesta para jugador"""
    message: str = "Usuario creado exitosamente."


class TokenResponseDTO(BaseModel):
    """DTO de respuesta para token"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600


class PlayerRankingDTO(BaseModel):
    """DTO para ranking de jugadores"""
    position: int
    username: str
    city: str
    votes: int
