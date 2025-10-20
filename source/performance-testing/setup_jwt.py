#!/usr/bin/env python3
"""
Script de inicialización automática para pruebas de performance.
Este script:
1. Crea un usuario de prueba (si no existe)
2. Obtiene un JWT token válido
3. Actualiza los archivos JMeter (.jmx) con el token
"""

import os
import sys
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

# Configuración
API_BASE_URL = os.getenv("API_BASE_URL", "http://host.docker.internal:80")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "performance_test@example.com")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "PerformanceTest123!")
MAX_RETRIES = 30
RETRY_DELAY = 2

# Rutas de archivos JMeter
JMETER_FILES = [
    "/scripts/smoke_test.jmx",
    "/scripts/ramp_up_test.jmx",
    "/scripts/sustained_test.jmx"
]


def wait_for_api():
    """Espera a que la API esté disponible"""
    print(f"Esperando a que la API esté disponible en {API_BASE_URL}...")

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                print("API disponible!")
                return True
        except requests.exceptions.RequestException as e:
            print(f"Intento {attempt + 1}/{MAX_RETRIES}: API no disponible aún... ({e})")
            time.sleep(RETRY_DELAY)

    print("ERROR: La API no está disponible después de múltiples intentos")
    return False


def create_test_user():
    """Crea un usuario de prueba (si no existe)"""
    print(f"\nCreando usuario de prueba: {TEST_USER_EMAIL}")

    user_data = {
        "first_name": "Performance",
        "last_name": "Test",
        "email": TEST_USER_EMAIL,
        "password1": TEST_USER_PASSWORD,
        "password2": TEST_USER_PASSWORD,
        "city": "Bogota",
        "country": "Colombia"
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/auth/signup",
            json=user_data,
            timeout=10
        )

        if response.status_code == 201:
            print("Usuario de prueba creado exitosamente")
            return True
        elif response.status_code == 400 and ("ya existe" in response.text.lower() or "ya está registrado" in response.text.lower()):
            print("Usuario de prueba ya existe, continuando...")
            return True
        else:
            print(f"Error al crear usuario: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al crear usuario: {e}")
        return False


def get_jwt_token():
    """Obtiene un JWT token válido"""
    print(f"\nObteniendo JWT token para: {TEST_USER_EMAIL}")

    login_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/auth/login",
            json=login_data,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print(f"JWT token obtenido exitosamente")
                print(f"Token (primeros 20 chars): {token[:20]}...")
                return token
            else:
                print("ERROR: No se encontró el token en la respuesta")
                return None
        else:
            print(f"Error al obtener token: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al obtener token: {e}")
        return None


def update_jmeter_file(file_path, jwt_token):
    """Actualiza un archivo JMeter con el JWT token"""
    print(f"\nActualizando archivo: {file_path}")

    if not os.path.exists(file_path):
        print(f"ADVERTENCIA: Archivo no encontrado: {file_path}")
        return False

    try:
        # Parsear el XML
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Buscar y actualizar el header de Authorization
        updated = False
        for elem in root.iter('stringProp'):
            if elem.get('name') == 'Header.value' and elem.text and 'Bearer' in elem.text:
                old_value = elem.text
                elem.text = f"Bearer {jwt_token}"
                print(f"  Token actualizado exitosamente")
                print(f"  Valor anterior: {old_value[:30]}...")
                print(f"  Valor nuevo: Bearer {jwt_token[:20]}...")
                updated = True
                break

        if updated:
            # Guardar el archivo actualizado
            tree.write(file_path, encoding='UTF-8', xml_declaration=True)
            print(f"  Archivo guardado: {file_path}")
            return True
        else:
            print(f"  ADVERTENCIA: No se encontró el header Authorization en el archivo")
            return False

    except Exception as e:
        print(f"ERROR al actualizar archivo {file_path}: {e}")
        return False


def main():
    """Función principal"""
    print("=" * 80)
    print("SCRIPT DE INICIALIZACIÓN DE PRUEBAS DE PERFORMANCE")
    print("=" * 80)

    # Paso 1: Esperar a que la API esté disponible
    if not wait_for_api():
        print("\nERROR CRÍTICO: La API no está disponible")
        sys.exit(1)

    # Paso 2: Crear usuario de prueba
    if not create_test_user():
        print("\nERROR: No se pudo crear el usuario de prueba")
        sys.exit(1)

    # Paso 3: Obtener JWT token
    jwt_token = get_jwt_token()
    if not jwt_token:
        print("\nERROR: No se pudo obtener el JWT token")
        sys.exit(1)

    # Paso 4: Actualizar archivos JMeter
    print("\n" + "=" * 80)
    print("ACTUALIZANDO ARCHIVOS JMETER")
    print("=" * 80)

    success_count = 0
    for jmeter_file in JMETER_FILES:
        if update_jmeter_file(jmeter_file, jwt_token):
            success_count += 1

    # Resultado final
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"Archivos actualizados: {success_count}/{len(JMETER_FILES)}")

    if success_count == len(JMETER_FILES):
        print("\n✓ CONFIGURACIÓN COMPLETADA EXITOSAMENTE")
        print("Las pruebas de JMeter están listas para ejecutarse")
        sys.exit(0)
    else:
        print("\n⚠ CONFIGURACIÓN COMPLETADA CON ADVERTENCIAS")
        print("Algunos archivos no se pudieron actualizar")
        sys.exit(0)


if __name__ == "__main__":
    main()
