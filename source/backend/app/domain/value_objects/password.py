from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Password:
    """Value Object para contraseña con validación"""
    
    value: str
    hashed_value: Optional[str] = None
    
    def __post_init__(self):
        """Valida la contraseña"""
        # Solo validar si no es un valor dummy (cuando viene de la BD)
        if self.value != "dummy" and not self._is_valid_password(self.value):
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
    
    def _is_valid_password(self, password: str) -> bool:
        """Valida que la contraseña cumpla con los requisitos mínimos"""
        return len(password) >= 8
    
    def __str__(self) -> str:
        return "***"  # Nunca exponer la contraseña en texto plano
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Password):
            return False
        return self.value == other.value
