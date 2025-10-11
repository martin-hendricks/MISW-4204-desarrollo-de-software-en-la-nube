from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    first_name: str = Field(..., min_length=2, max_length=100, description="Nombre del usuario")
    last_name: str = Field(..., min_length=2, max_length=100, description="Apellido del usuario")
    city: str = Field(..., min_length=2, max_length=100, description="Ciudad de residencia")
    country: str = Field(..., min_length=2, max_length=100, description="País de residencia")
    password1: str = Field(..., min_length=8, description="Contraseña del usuario (mínimo 8 caracteres)")
    password2: str = Field(..., min_length=8, description="Confirmación de contraseña")

    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v.strip():
            raise ValueError('El nombre y apellido no pueden estar vacíos')
        if not v.replace(' ', '').isalpha():
            raise ValueError('El nombre y apellido solo pueden contener letras y espacios')
        return v.strip().title()

    @validator('city', 'country')
    def validate_location(cls, v):
        if not v.strip():
            raise ValueError('La ciudad y país no pueden estar vacíos')
        return v.strip().title()

    @validator('password1')
    def validate_password1(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('La contraseña debe tener al menos una letra mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('La contraseña debe tener al menos una letra minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('La contraseña debe tener al menos un número')
        return v

    @validator('password2')
    def validate_passwords_match(cls, v, values):
        if 'password1' in values and v != values['password1']:
            raise ValueError('Las contraseñas no coinciden')
        return v

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    city: str
    country: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None