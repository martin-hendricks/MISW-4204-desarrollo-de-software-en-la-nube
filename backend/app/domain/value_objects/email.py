import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Email:
    """Value Object para email con validación"""
    
    value: str
    
    def __post_init__(self):
        """Valida el formato del email"""
        if not self._is_valid_email(self.value):
            raise ValueError("Formato de email inválido")
    
    def _is_valid_email(self, email: str) -> bool:
        """Valida el formato del email usando regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def __str__(self) -> str:
        return self.value
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Email):
            return False
        return self.value.lower() == other.value.lower()
    
    def __hash__(self) -> int:
        return hash(self.value.lower())
