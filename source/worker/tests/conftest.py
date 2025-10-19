"""
Configuración de pytest - Se ejecuta antes de importar los módulos
"""
import os
import tempfile
import pytest

# ===== CONFIGURAR VARIABLES DE ENTORNO ANTES DE IMPORTAR =====
# Esto se ejecuta antes de que pytest importe los módulos de test
# Así evitamos que config.py intente crear /app/uploads en el sistema local

# Usar directorio temporal para uploads en tests
TEST_UPLOAD_DIR = tempfile.mkdtemp()

os.environ["UPLOAD_DIR"] = TEST_UPLOAD_DIR
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["DATABASE_URL"] = "postgresql://user:password@localhost:5432/test"
os.environ["LOG_LEVEL"] = "ERROR"  # Menos logs en tests


@pytest.fixture(scope="session", autouse=True)
def cleanup_temp_dirs():
    """Limpiar directorios temporales después de todos los tests"""
    yield
    # Cleanup después de todos los tests
    import shutil
    try:
        shutil.rmtree(TEST_UPLOAD_DIR, ignore_errors=True)
    except:
        pass

