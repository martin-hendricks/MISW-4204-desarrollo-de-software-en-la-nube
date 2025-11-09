# Guía de Despliegue - Instancia Worker

## Resumen
Esta instancia EC2 contiene:
- ✅ Celery Worker (Procesamiento de videos con FFmpeg) - 2 workers
- ✅ Health Check API (FastAPI) - Puerto 8001
- ✅ Integración con AWS SQS (Message Broker)
- ✅ Integración con AWS S3 (Almacenamiento de archivos)

---

## Requisitos Previos

### 1. Instancia EC2 configurada
- ✅ Ubuntu Server 22.04 LTS
- ✅ Tipo: t2.medium o superior (recomendado t2.large para procesamiento)
- ✅ Docker y Docker Compose instalados
- ✅ Security Group configurado (ver abajo)

### 2. Servicios externos funcionando
- ✅ RDS PostgreSQL creado y accesible
- ✅ AWS SQS colas creadas (main queue y DLQ) - las mismas que usa el Backend
- ✅ AWS S3 bucket creado - el mismo que usa el Backend
- ✅ Backend desplegado y funcionando

### 3. Información que necesitas tener a mano
- IP pública de la instancia Backend (para BASE_PATH)
- Endpoint de RDS PostgreSQL
- Usuario y contraseña de RDS
- SQS Queue URL y DLQ URL (las mismas que el Backend)
- S3 Bucket Name (el mismo que el Backend)
- AWS credentials (las mismas que el Backend)

### 4. Assets de video
- Logo ANB (anb_logo.png)
- Video intro (intro.mp4) - máximo 2.5 segundos
- Video outro (outro.mp4) - máximo 2.5 segundos

---

## Security Group - Worker Instance

### Inbound Rules

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | Your IP | Administración SSH |
| Custom TCP | TCP | 8001 | Your IP | Health API (debug) |
| Custom TCP | TCP | 8001 | Backend SG | Health checks desde Backend |

### Outbound Rules
- All traffic (default)

**IMPORTANTE:** El Worker necesita poder conectarse a:
- RDS PostgreSQL (puerto 5432)
- AWS SQS (puerto 443 - HTTPS)
- AWS S3 (puerto 443 - HTTPS)

---

## ⚠️ IMPORTANTE: Configuración Previa al Despliegue

**Antes de ejecutar `docker-compose up`**, debes configurar el archivo `.env` con los valores correctos:

### 📝 Archivo que DEBES editar:

| Archivo | Qué configurar |
|---------|----------------|
| **`.env`** | `DATABASE_URL` (RDS endpoint - el mismo que el Backend) |
| **`.env`** | `BASE_PATH` (URL pública del Backend - IP PÚBLICA del Backend) |
| **`.env`** | `SQS_QUEUE_URL` y `SQS_DLQ_URL` (las mismas que el Backend) |
| **`.env`** | `S3_BUCKET_NAME` y credenciales AWS (las mismas que el Backend) |

### 🔄 ¿Necesitas recrear contenedores después de cambiar configuración?

**SÍ, debes recrear** si cambias cualquiera de estos valores después del primer despliegue:

```bash
# Detener y eliminar contenedores actuales
docker-compose down

# Editar archivos de configuración
nano .env

# Reconstruir y levantar con nueva configuración
docker-compose up -d --build
```

**NO necesitas recrear** si solo cambias:
- Logs
- Concurrencia de Celery (`CELERY_CONCURRENCY`)
- Variables de configuración que no afectan conectividad

**NOTA:** Si cambias `CELERY_CONCURRENCY`, solo necesitas reiniciar:
```bash
docker-compose restart worker
```

---

## Pasos de Despliegue

### Paso 1: Conectarse a la instancia

```bash
ssh -i "your-key.pem" ubuntu@<WORKER_PUBLIC_IP>
```

### Paso 2: Clonar/Copiar los archivos del proyecto

```bash
# Crear directorio de trabajo
mkdir -p ~/anb-worker
cd ~/anb-worker

# Opción A: Clonar repositorio (si está en GitHub)
git clone <your-repo-url> .
cd source/deployment/worker-instance

# Opción B: Copiar archivos manualmente usando SCP desde tu máquina local
# Desde tu máquina local:
# scp -i "your-key.pem" -r ./source/deployment/worker-instance ubuntu@<WORKER_PUBLIC_IP>:~/anb-worker/
# scp -i "your-key.pem" -r ./source/worker ubuntu@<WORKER_PUBLIC_IP>:~/anb-worker/
```

### Paso 3: Preparar carpeta de assets

```bash
cd ~/anb-worker/deployment/worker-instance

# Crear carpeta de assets
mkdir -p assets

# Copiar assets desde tu máquina local
# Desde tu máquina local:
# scp -i "your-key.pem" anb_logo.png ubuntu@<WORKER_PUBLIC_IP>:~/anb-worker/deployment/worker-instance/assets/
# scp -i "your-key.pem" intro.mp4 ubuntu@<WORKER_PUBLIC_IP>:~/anb-worker/deployment/worker-instance/assets/
# scp -i "your-key.pem" outro.mp4 ubuntu@<WORKER_PUBLIC_IP>:~/anb-worker/deployment/worker-instance/assets/

# Verificar que los archivos están presentes
ls -lh assets/
```

**Requisitos de los assets:**
- `anb_logo.png`: Logo ANB en formato PNG con transparencia (recomendado 200x200px)
- `intro.mp4`: Video intro, máximo 2.5 segundos, 1280x720
- `outro.mp4`: Video outro, máximo 2.5 segundos, 1280x720

### Paso 4: Configurar variables de entorno

```bash
cd ~/anb-worker/deployment/worker-instance

# Copiar archivo de ejemplo
cp .env.example .env

# Editar con tus valores reales
nano .env
```

**Variables que DEBES cambiar:**

```bash
# RDS Database (mismo que Backend)
DATABASE_URL=postgresql://admin:YourPassword@anb-db.xxx.us-east-1.rds.amazonaws.com:5432/anbdb

# AWS SQS (mismas URLs que Backend)
USE_SQS=true
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/anb-video-processing
SQS_DLQ_URL=https://sqs.us-east-1.amazonaws.com/123456789/anb-video-processing-dlq

# AWS S3 (mismo bucket y credenciales que Backend)
STORAGE_TYPE=s3
S3_BUCKET_NAME=anb-videos-bucket
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# Base Path (IP PÚBLICA del Backend)
BASE_PATH=http://<BACKEND_PUBLIC_IP>/api/videos
```

### Paso 5: Configurar Almacenamiento S3

**Pre-requisito:** El bucket S3 debe estar creado y configurado (mismo que el Backend)

```bash
# Dar permisos de ejecución
chmod +x setup-s3.sh

# Ejecutar el script
./setup-s3.sh
```

El script:
- ✅ Valida las credenciales AWS (deben ser las **mismas** que en Backend)
- ✅ Instala AWS CLI
- ✅ Configura las credenciales (incluyendo session_token si existe)
- ✅ Verifica acceso al bucket S3

**Verificar acceso a S3:**

```bash
aws s3 ls s3://anb-videos-bucket-2025-team-2/
```

Deberías ver el mismo contenido que desde el Backend:

```
                           PRE original/
                           PRE processed/
```

---

### Paso 6: Construir y levantar el servicio

```bash
cd ~/anb-worker/deployment/worker-instance

# Construir la imagen
docker-compose build

# Levantar el servicio en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Paso 7: Verificar que el worker está corriendo

```bash
# Ver estado del contenedor
docker-compose ps

# Deberías ver:
# NAME          IMAGE                     STATUS
# anb-worker    worker-instance-worker    Up (healthy)

# Ver logs del worker
docker-compose logs -f worker

# Deberías ver líneas como:
# [2025-01-15 10:30:00] [INFO] celery.worker.strategy: Starting Celery worker
# [2025-01-15 10:30:01] [INFO] Connected to SQS
# [2025-01-15 10:30:02] [INFO] Ready to accept tasks
```

### Paso 8: Verificar health check

```bash
# Desde la instancia Worker
curl http://localhost:8001/health

# Deberías ver algo como:
# {
#   "status": "healthy",
#   "celery_status": "running",
#   "sqs_connection": "ok",
#   "database_connection": "ok",
#   "s3_access": "ok"
# }
```

### Paso 9: Verificar tareas de Celery

```bash
# Ver workers activos
docker exec -it anb-worker celery -A celery_app inspect active

# Ver estadísticas
docker exec -it anb-worker celery -A celery_app inspect stats
```

Deberías ver:
- 2 workers activos (configurable con CELERY_CONCURRENCY)
- Queues: `video_processing` y `dlq`
- Estado: Online

---

## Verificación de Funcionamiento Completo

### Prueba End-to-End

1. **Subir un video desde el Backend:**

```bash
# Desde tu máquina local
curl -X POST http://<BACKEND_PUBLIC_IP>/api/videos/upload \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -F "file=@test_video.mp4"
```

2. **Ver el progreso en los logs:**

```bash
# En la instancia Worker
docker-compose logs -f worker | grep process_video
```

Deberías ver la tarea `process_video` progresando:
- `PENDING` → `STARTED` → `SUCCESS`

3. **Verificar en S3:**

```bash
# Verificar archivos en S3
aws s3 ls s3://anb-videos-bucket/original/
aws s3 ls s3://anb-videos-bucket/processed/

# Deberías ver el video original y el procesado
```

4. **Consultar estado en la API:**

```bash
# Verificar estado del video
curl -X GET http://<BACKEND_PUBLIC_IP>/api/videos \
  -H "Authorization: Bearer <JWT_TOKEN>"

# El video debería tener status: "processed"
```

---

## Comandos Útiles

### Ver logs

```bash
# Logs del worker
docker-compose logs -f worker

# Últimas 100 líneas
docker-compose logs --tail=100 worker

# Filtrar por palabra clave
docker-compose logs -f worker | grep ERROR
```

### Reiniciar worker

```bash
# Reiniciar contenedor
docker-compose restart worker

# Reiniciar solo Celery (dentro del contenedor)
docker-compose exec worker pkill -HUP celery
```

### Ver estado de Celery

```bash
# Entrar al contenedor
docker exec -it anb-worker bash

# Ver workers activos
celery -A celery_app inspect active

# Ver tareas en cola
celery -A celery_app inspect reserved

# Ver estadísticas
celery -A celery_app inspect stats

# Salir
exit
```

### Monitorear procesamiento en tiempo real

```bash
# Ver logs con timestamp
docker-compose logs -f --timestamps worker

# Monitorear archivos procesados en S3
watch -n 5 'aws s3 ls s3://anb-videos-bucket/processed/ | tail -n 10'
```

---

## Troubleshooting

### Error: "Cannot connect to SQS"

```bash
# Verificar que las colas existen
aws sqs list-queues

# Verificar URL de la cola
aws sqs get-queue-attributes --queue-url <YOUR_QUEUE_URL>

# Verificar credenciales
cat .env | grep SQS_QUEUE_URL
cat .env | grep AWS_

# Ver logs del worker
docker-compose logs worker
```

### Error: "Cannot connect to S3"

```bash
# Verificar acceso al bucket
aws s3 ls s3://<YOUR_BUCKET_NAME>

# Verificar credenciales
cat .env | grep S3_BUCKET_NAME
cat .env | grep AWS_

# Ver logs del worker
docker-compose logs worker
```

### Error: "Cannot connect to database"

```bash
# Verificar que RDS es alcanzable
telnet <RDS_ENDPOINT> 5432

# Verificar credenciales en .env
cat .env | grep DATABASE_URL
```

### Error: "FFmpeg not found"

```bash
# Verificar que FFmpeg está instalado en el contenedor
docker exec -it anb-worker ffmpeg -version

# Si no está, rebuild la imagen
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Error: "Logo/Intro/Outro not found"

```bash
# Verificar que los assets están montados en el contenedor
docker exec -it anb-worker ls -la /app/assets/

# Deberías ver:
# anb_logo.png
# intro.mp4
# outro.mp4

# Si no están, verifica la carpeta en el host
ls -la ~/anb-worker/deployment/worker-instance/assets/
```

### Worker no procesa tareas

```bash
# Ver logs detallados
docker-compose logs -f worker

# Verificar conexión a SQS
docker exec -it anb-worker python -c "
from celery_app import app
app.connection().connect()
print('SQS OK')
"

# Verificar que las colas están configuradas
docker exec -it anb-worker celery -A celery_app inspect active_queues
```

### Tareas quedan en estado PENDING

```bash
# Ver tareas activas
docker exec -it anb-worker celery -A celery_app inspect active

# Verificar routing de tareas
docker exec -it anb-worker celery -A celery_app inspect registered

# Reiniciar worker
docker-compose restart worker
```

### Procesamiento muy lento

```bash
# Ver recursos del sistema
htop  # o: top

# Ver estadísticas de Docker
docker stats anb-worker

# Considerar:
# 1. Aumentar tipo de instancia (t2.large → t2.xlarge)
# 2. Reducir concurrency en .env: CELERY_CONCURRENCY=2
# 3. Escalar horizontalmente (crear más instancias Worker)
```

---

## Escalamiento Horizontal

Para agregar más workers (procesar más videos en paralelo):

### Opción 1: Aumentar concurrency en esta instancia

```bash
# Editar .env
nano .env

# Cambiar:
CELERY_CONCURRENCY=8  # de 4 a 8

# Reiniciar
docker-compose restart worker
```

### Opción 2: Crear más instancias Worker idénticas

1. Crear nueva instancia EC2 idéntica
2. Repetir todos los pasos de despliegue
3. Ambas instancias consumirán de la misma cola SQS
4. Load balancing automático por SQS

---

## Monitoreo Continuo

### Health Check API

```bash
# Verificar salud cada 30 segundos
watch -n 30 'curl -s http://localhost:8001/health | jq'
```


### Alertas (opcional)

Configurar alertas cuando:
- Worker deja de procesar tareas
- Tareas fallan repetidamente
- Errores de acceso a S3 o SQS

---

## Backup y Mantenimiento

### Logs

```bash
# Exportar logs para análisis
docker-compose logs worker > worker-logs-$(date +%F).log
```

### Limpiar contenedores viejos

```bash
# Limpiar imágenes sin usar
docker system prune -a

# Ver espacio usado
docker system df
```

### Actualizar código

```bash
# Pull cambios
git pull origin main

# Rebuild y redeploy
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Siguientes Pasos

Una vez que el Worker esté funcionando:

1. ✅ Worker desplegado y procesando tareas
2. ⏭️ Probar flujo completo end-to-end
3. ⏭️ Configurar monitoreo y alertas
4. ⏭️ Optimizar performance según carga
5. ⏭️ Documentar métricas de procesamiento

---

## Comandos Rápidos de Referencia

```bash
# Configurar S3
./setup-s3.sh

# Levantar worker
docker-compose up -d

# Ver logs
docker-compose logs -f worker

# Verificar salud
curl http://localhost:8001/health

# Ver tareas activas
docker exec -it anb-worker celery -A celery_app inspect active

# Monitorear archivos procesados en S3
watch -n 5 'aws s3 ls s3://anb-videos-bucket/processed/ | tail -n 10'

# Reiniciar
docker-compose restart worker

# Detener
docker-compose down
```
