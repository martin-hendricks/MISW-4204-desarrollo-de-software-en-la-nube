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
COPY cloudwatch /app/cloudwatch

# Copiar código de la aplicación
COPY worker /app

# Crear directorios para videos y assets
RUN mkdir -p /app/uploads/original /app/uploads/processed /app/uploads/temp /app/assets

# Exponer puerto para Health API
EXPOSE 8001

# El comando se define en docker-compose.yml para ejecutar:
# 1. API de health checks (python main.py)
# 2. Worker de Celery
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]