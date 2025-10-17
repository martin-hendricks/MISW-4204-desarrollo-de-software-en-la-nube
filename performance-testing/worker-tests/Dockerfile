FROM python:3.11-slim

WORKDIR /app

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el script del productor
COPY producer.py .

# Copiar los assets de video
COPY assets/ ./assets/

CMD ["python", "producer.py"]
