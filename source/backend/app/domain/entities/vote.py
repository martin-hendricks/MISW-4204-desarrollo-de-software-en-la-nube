from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Vote:
    """Entidad de dominio para un voto"""
    
    id: Optional[int]
    video_id: int
    player_id: int
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validaciones después de la inicialización"""
        if self.video_id <= 0:
            raise ValueError("El ID del video debe ser válido")
        
        if self.player_id <= 0:
            raise ValueError("El ID del votante debe ser válido")
    
    def is_valid(self) -> bool:
        """Verifica si el voto es válido"""
        return self.video_id > 0 and self.player_id > 0
