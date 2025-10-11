"""
Modelos de base de datos con SQLAlchemy
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from config.database import Base

class Player(Base):
    """
    Modelo de jugador para la base de datos
    """
    __tablename__ = "players"

    # Campos de la tabla
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)    
    # Timestamps automáticos
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )

    def __repr__(self):
        return f"<Player(id={self.id}, email='{self.email}', name='{self.first_name} {self.last_name}')>"

    def to_dict(self):
        """
        Convertir el modelo a diccionario (útil para logging/debugging)
        """
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "city": self.city,
            "country": self.country,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }