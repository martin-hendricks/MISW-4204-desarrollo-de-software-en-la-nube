FROM python:3.11-slim

WORKDIR /app

# Instalar FFmpeg y dependencias del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy cloudwatch module (shared with backend)
COPY ../cloudwatch /app/cloudwatch

# Copiar código de la aplicación
COPY worker /app

# Copiar assets (logo, intro, outro) - se sobrescriben los que vienen en worker/assets
COPY worker/assets /app/assets

# Crear directorios para videos
RUN mkdir -p /app/uploads/original /app/uploads/processed /app/uploads/temp

# Exponer puerto para Health API
EXPOSE 8001

# El comando se define en docker-compose.yml para ejecutar:
# 1. API de health checks (python main.py)
# 2. Worker de Celery
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]