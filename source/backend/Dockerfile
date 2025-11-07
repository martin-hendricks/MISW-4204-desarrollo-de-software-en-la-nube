FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy cloudwatch module (shared with worker)
COPY ../cloudwatch /app/cloudwatch

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads/original /app/uploads/processed /app/uploads/temp

# Expose port
EXPOSE 8000

# Start the application using start.py
CMD ["python", "start.py"]