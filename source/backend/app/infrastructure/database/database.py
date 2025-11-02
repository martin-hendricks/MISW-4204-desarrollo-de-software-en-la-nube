from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os

# Configuración de la base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/fileprocessing"
)

# Crear el motor de la base de datos con connection pooling optimizado
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Número de conexiones permanentes en el pool
    max_overflow=40,  # Conexiones adicionales permitidas bajo alta carga
    pool_pre_ping=True,  # Verifica que la conexión esté viva antes de usarla
    pool_recycle=3600,  # Recicla conexiones después de 1 hora
    echo=False  # Desactivar logging SQL para mejor performance
)

# Crear la sesión de la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
