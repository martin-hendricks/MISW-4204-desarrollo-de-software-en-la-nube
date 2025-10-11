from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import Password


@dataclass
class Player:
    """Entidad de dominio para un jugador"""
    
    id: Optional[int]
    first_name: str
    last_name: str
    email: Email
    password: Password
    city: str
    country: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones después de la inicialización"""
        if not self.first_name or len(self.first_name.strip()) == 0:
            raise ValueError("El nombre no puede estar vacío")
        
        if not self.last_name or len(self.last_name.strip()) == 0:
            raise ValueError("El apellido no puede estar vacío")
        
        if not self.city or len(self.city.strip()) == 0:
            raise ValueError("La ciudad no puede estar vacía")
        
        if not self.country or len(self.country.strip()) == 0:
            raise ValueError("El país no puede estar vacío")
    
    @property
    def username(self) -> str:
        """Genera un username basado en el nombre y apellido"""
        return f"{self.first_name.lower()}.{self.last_name.lower()}"
    
    @property
    def full_name(self) -> str:
        """Retorna el nombre completo del jugador"""
        return f"{self.first_name} {self.last_name}"
    
    def activate(self) -> None:
        """Activa la cuenta del jugador"""
        self.is_active = True
    
    def deactivate(self) -> None:
        """Desactiva la cuenta del jugador"""
        self.is_active = False
    
    def change_password(self, new_password: str) -> None:
        """Cambia la contraseña del jugador"""
        self.password = Password(new_password)
    
    def update_profile(self, first_name: str = None, last_name: str = None, 
                      city: str = None, country: str = None) -> None:
        """Actualiza el perfil del jugador"""
        if first_name:
            self.first_name = first_name
        if last_name:
            self.last_name = last_name
        if city:
            self.city = city
        if country:
            self.country = country
