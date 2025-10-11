#!/usr/bin/env python3
"""
Script de inicio para la API ANB Rising Stars Showcase
"""
import uvicorn
import os
from app.main import app

if __name__ == "__main__":
    # Configuración por defecto
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print("🏀 Iniciando ANB Rising Stars Showcase API...")
    print(f"📍 Servidor: http://{host}:{port}")
    print(f"📚 Documentación: http://{host}:{port}/docs")
    print(f"🔄 Reload: {'Activado' if reload else 'Desactivado'}")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
