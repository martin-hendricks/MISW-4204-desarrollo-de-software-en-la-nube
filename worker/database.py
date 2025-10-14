"""
Conexión a PostgreSQL
NOTA: El backend crea las tablas, el worker solo se conecta
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from config import config
import logging

logger = logging.getLogger(__name__)

# Crear engine de SQLAlchemy
engine = create_engine(
    config.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verificar conexión antes de usar
    echo=False  # Set True para debug SQL
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    """
    Crea una nueva sesión de base de datos
    
    Usage:
        db = get_db_session()
        try:
            # usar db
        finally:
            db.close()
    """
    return SessionLocal()


def test_db_connection() -> bool:
    """
    Prueba la conexión a la base de datos
    
    Returns:
        True si la conexión es exitosa
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        logger.info("✅ Conexión a PostgreSQL exitosa")
        return True
    except Exception as e:
        logger.error(f"❌ Error conectando a PostgreSQL: {e}")
        return False

