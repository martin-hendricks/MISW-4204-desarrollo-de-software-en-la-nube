"""
Script para inicializar la base de datos y crear tablas
"""
import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine, test_connection, Base
from models.db_models import User

def create_tables():
    """
    Crear todas las tablas en la base de datos
    """
    print("🔄 Creando tablas en la base de datos...")
    
    try:
        # Probar conexión primero
        if not test_connection():
            print("❌ No se pudo conectar a la base de datos")
            return False
            
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")
        
        # Mostrar las tablas creadas
        print("\n📋 Tablas creadas:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def drop_tables():
    """
    Eliminar todas las tablas (usar con cuidado)
    """
    print("⚠️  ELIMINANDO todas las tablas...")
    
    try:
        Base.metadata.drop_all(bind=engine)
        print("✅ Tablas eliminadas exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error eliminando tablas: {e}")
        return False

def reset_database():
    """
    Reiniciar base de datos (eliminar y crear tablas)
    """
    print("🔄 Reiniciando base de datos...")
    
    if drop_tables():
        return create_tables()
    return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gestión de base de datos")
    parser.add_argument(
        "action", 
        choices=["create", "drop", "reset", "test"],
        help="Acción a realizar"
    )
    
    args = parser.parse_args()
    
    if args.action == "create":
        create_tables()
    elif args.action == "drop":
        confirmation = input("¿Estás seguro de eliminar todas las tablas? (sí/no): ")
        if confirmation.lower() in ["sí", "si", "yes", "y"]:
            drop_tables()
        else:
            print("❌ Operación cancelada")
    elif args.action == "reset":
        confirmation = input("¿Estás seguro de reiniciar la base de datos? (sí/no): ")
        if confirmation.lower() in ["sí", "si", "yes", "y"]:
            reset_database()
        else:
            print("❌ Operación cancelada")
    elif args.action == "test":
        if test_connection():
            print("✅ Conexión exitosa")
        else:
            print("❌ Error de conexión")