#!/usr/bin/env python3
"""
Script de inicio para la API ANB Rising Stars Showcase
"""
import uvicorn
import os
import multiprocessing
from app.main import app

if __name__ == "__main__":
    # Configuración por defecto
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    # Calcular número óptimo de workers (2-4 x CPU cores)
    # En modo desarrollo (reload=True) usar 1 worker
    # En producción usar múltiples workers para manejar concurrencia
    cpu_count = multiprocessing.cpu_count()
    workers = 1 if reload else int(os.getenv("WORKERS", min(cpu_count * 2, 8)))

    print("🏀 Iniciando ANB Rising Stars Showcase API...")
    print(f"📍 Servidor: http://{host}:{port}")
    print(f"📚 Documentación: http://{host}:{port}/docs")
    print(f"🔄 Reload: {'Activado' if reload else 'Desactivado'}")
    print(f"👷 Workers: {workers} (CPUs detectados: {cpu_count})")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level="info",
        timeout_keep_alive=5  # Cerrar conexiones idle después de 5 segundos
    )
