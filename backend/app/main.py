from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

# Crear la aplicación FastAPI
app = FastAPI(
    title="ANB Rising Stars Showcase API",
    description="API REST para la plataforma ANB Rising Stars Showcase - Gestión de videos de habilidades de baloncesto",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crear directorio de uploads si no existe
os.makedirs("uploads", exist_ok=True)

# Montar directorio estático para servir archivos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Incluir routers
from app.routers import auth, videos, public

app.include_router(auth.router)
app.include_router(videos.router)
app.include_router(public.router)

@app.get("/")
def read_root():
    return {
        "message": "ANB Rising Stars Showcase API", 
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "backend"}