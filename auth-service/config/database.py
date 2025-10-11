"""
Configuración de base de datos con SQLAlchemy
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuración de base de datos desde variables de entorno
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://auth_user:auth_password@postgres-db:5432/auth_db"
)

# Motor de SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verificar conexiones antes de usar
    pool_recycle=300,    # Reciclar conexiones cada 5 minutos
    echo=os.getenv("DEBUG", "False").lower() == "true"  # Log SQL queries en debug
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos ORM
Base = declarative_base()

# Dependency para obtener sesión de BD
def get_database_session():
    """
    Dependency para FastAPI que provee una sesión de base de datos
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función para probar conexión
def test_connection():
    """
    Probar conexión a la base de datos
    """
    try:
        connection = engine.connect()
        connection.close()
        print("✅ Conexión a base de datos exitosa")
        return True
    except Exception as e:
        print(f"❌ Error conectando a base de datos: {e}")
        return False