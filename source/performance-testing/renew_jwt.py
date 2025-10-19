#!/usr/bin/env python3
"""
Script de renovación automática de JWT token para pruebas de performance.
Este script:
1. Se ejecuta continuamente en segundo plano
2. Renueva el JWT token cada cierto intervalo (por defecto 30 minutos)
3. Actualiza automáticamente los archivos JMeter con el nuevo token
"""

import os
import sys
import time
import signal
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# Configuración
API_BASE_URL = os.getenv("API_BASE_URL", "http://host.docker.internal:80")
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "performance_test@example.com")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "PerformanceTest123!")
RENEWAL_INTERVAL = int(os.getenv("RENEWAL_INTERVAL", "1800"))  # 30 minutos por defecto

# Rutas de archivos JMeter
JMETER_FILES = [
    "/scripts/smoke_test.jmx",
    "/scripts/ramp_up_test.jmx",
    "/scripts/sustained_test.jmx"
]

# Variable global para manejo de señales
keep_running = True


def signal_handler(signum, frame):
    """Maneja las señales de terminación"""
    global keep_running
    print("\n" + "=" * 80)
    print(f"Señal {signum} recibida. Deteniendo servicio de renovación...")
    print("=" * 80)
    keep_running = False


def log_message(message, level="INFO"):
    """Imprime un mensaje con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def get_jwt_token():
    """Obtiene un JWT token válido"""
    log_message(f"Renovando JWT token para: {TEST_USER_EMAIL}")

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
                log_message(f"JWT token renovado exitosamente (primeros 20 chars): {token[:20]}...")
                return token
            else:
                log_message("No se encontró el token en la respuesta", "ERROR")
                return None
        else:
            log_message(f"Error al obtener token: {response.status_code} - {response.text}", "ERROR")
            return None

    except requests.exceptions.RequestException as e:
        log_message(f"Error de conexión al obtener token: {e}", "ERROR")
        return None


def update_jmeter_file(file_path, jwt_token):
    """Actualiza un archivo JMeter con el JWT token"""
    if not os.path.exists(file_path):
        log_message(f"Archivo no encontrado: {file_path}", "WARNING")
        return False

    try:
        # Parsear el XML
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Buscar y actualizar el header de Authorization
        updated = False
        for elem in root.iter('stringProp'):
            if elem.get('name') == 'Header.value' and elem.text and 'Bearer' in elem.text:
                elem.text = f"Bearer {jwt_token}"
                updated = True
                break

        if updated:
            # Guardar el archivo actualizado
            tree.write(file_path, encoding='UTF-8', xml_declaration=True)
            return True
        else:
            log_message(f"No se encontró el header Authorization en: {file_path}", "WARNING")
            return False

    except Exception as e:
        log_message(f"Error al actualizar {file_path}: {e}", "ERROR")
        return False


def update_all_jmeter_files(jwt_token):
    """Actualiza todos los archivos JMeter con el nuevo token"""
    success_count = 0
    for jmeter_file in JMETER_FILES:
        if update_jmeter_file(jmeter_file, jwt_token):
            success_count += 1

    log_message(f"Archivos JMeter actualizados: {success_count}/{len(JMETER_FILES)}")
    return success_count == len(JMETER_FILES)


def wait_for_api():
    """Espera a que la API esté disponible"""
    log_message(f"Verificando disponibilidad de la API en {API_BASE_URL}...")

    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                log_message("API disponible")
                return True
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                log_message(f"API no disponible, reintentando... ({attempt + 1}/{max_retries})", "WARNING")
                time.sleep(2)

    log_message("API no disponible después de varios intentos", "ERROR")
    return False


def main():
    """Función principal del servicio de renovación"""
    # Configurar manejadores de señales
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    print("=" * 80)
    print("SERVICIO DE RENOVACIÓN AUTOMÁTICA DE JWT TOKEN")
    print("=" * 80)
    log_message(f"Intervalo de renovación: {RENEWAL_INTERVAL} segundos ({RENEWAL_INTERVAL/60:.1f} minutos)")
    log_message(f"Usuario: {TEST_USER_EMAIL}")
    print("=" * 80)

    # Esperar a que la API esté disponible
    if not wait_for_api():
        log_message("No se puede iniciar el servicio sin acceso a la API", "ERROR")
        sys.exit(1)

    # Primera renovación inmediata
    log_message("Obteniendo token inicial...")
    jwt_token = get_jwt_token()
    if jwt_token:
        update_all_jmeter_files(jwt_token)
    else:
        log_message("No se pudo obtener el token inicial", "ERROR")
        sys.exit(1)

    log_message("Servicio de renovación iniciado correctamente")
    log_message("Presiona Ctrl+C para detener")
    print("=" * 80)

    # Bucle de renovación
    iteration = 0
    while keep_running:
        try:
            # Esperar hasta el próximo intervalo de renovación
            for _ in range(RENEWAL_INTERVAL):
                if not keep_running:
                    break
                time.sleep(1)

            if not keep_running:
                break

            iteration += 1
            log_message(f"--- Renovación #{iteration} ---")

            # Renovar token
            jwt_token = get_jwt_token()
            if jwt_token:
                if update_all_jmeter_files(jwt_token):
                    log_message("Renovación completada exitosamente")
                else:
                    log_message("Renovación parcial: algunos archivos no se actualizaron", "WARNING")
            else:
                log_message("Error en la renovación del token", "ERROR")

            log_message(f"Próxima renovación en {RENEWAL_INTERVAL/60:.1f} minutos")
            print("-" * 80)

        except Exception as e:
            log_message(f"Error inesperado en el bucle de renovación: {e}", "ERROR")
            time.sleep(10)  # Esperar un poco antes de reintentar

    # Limpieza al salir
    print("=" * 80)
    log_message("Servicio de renovación detenido")
    print("=" * 80)
    sys.exit(0)


if __name__ == "__main__":
    main()
