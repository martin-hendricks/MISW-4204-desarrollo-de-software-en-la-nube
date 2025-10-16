#!/usr/bin/env python3
"""
Script para ejecutar migraciones de base de datos
"""
import subprocess
import sys
import os

def run_command(command):
    """Ejecuta un comando y maneja errores"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error ejecutando: {command}")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Función principal"""
    print("🗄️  Ejecutando migraciones de base de datos...")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("alembic.ini"):
        print("❌ No se encontró alembic.ini. Asegúrate de estar en el directorio backend/")
        sys.exit(1)
    
    # Ejecutar migraciones
    if run_command("alembic upgrade head"):
        print("✅ Migraciones completadas exitosamente")
    else:
        print("❌ Error en las migraciones")
        sys.exit(1)

if __name__ == "__main__":
    main()
