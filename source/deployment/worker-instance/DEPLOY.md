# Guía de Despliegue - Instancia Worker

## Resumen
Esta instancia EC2 contiene:
- ✅ Celery Worker (Procesamiento de videos con FFmpeg) - 4 workers
- ✅ Health Check API (FastAPI) - Puerto 8001

---

## Requisitos Previos

### 1. Instancia EC2 configurada
- ✅ Ubuntu Server 22.04 LTS
- ✅ Tipo: t2.medium o superior (recomendado t2.large para procesamiento)
- ✅ Docker y Docker Compose instalados
- ✅ Security Group configurado (ver abajo)

### 2. Servicios externos funcionando
- ✅ Servidor NFS configurado y ejecutándose
- ✅ RDS PostgreSQL creado y accesible
- ✅ Backend desplegado y funcionando (con Redis)

### 3. Información que necesitas tener a mano
- IP privada del servidor NFS
- IP privada de la instancia Backend (para Redis)
- IP pública de la instancia Backend (para BASE_PATH)
- Endpoint de RDS PostgreSQL
- Usuario y contraseña de RDS

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
- NFS Server (puerto 2049)
- Backend Redis (puerto 6379)
- RDS PostgreSQL (puerto 5432)

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

# Redis en Backend (usar IP PRIVADA del Backend)
REDIS_URL=redis://172.31.10.5:6379/0

# Base Path (IP PÚBLICA del Backend)
BASE_PATH=http://54.123.45.67/api/videos
```

### Paso 5: Verificar conectividad con Redis (Backend)

```bash
# Instalar redis-tools para probar
sudo apt install -y redis-tools

# Probar conexión con Redis en Backend
# Reemplaza <BACKEND_PRIVATE_IP> con la IP privada real
redis-cli -h <BACKEND_PRIVATE_IP> ping

# Deberías ver: PONG
```

Si no puedes conectar:
- Verifica el Security Group del Backend permite puerto 6379 desde Worker
- Verifica que Redis está corriendo en Backend: `docker ps | grep redis`

### Paso 6: Configurar montaje NFS

```bash
# Editar el script con la IP del servidor NFS
nano setup-nfs-mount.sh

# Cambiar esta línea:
# NFS_SERVER_IP="REPLACE_WITH_NFS_PRIVATE_IP"
# Por ejemplo:
# NFS_SERVER_IP="172.31.10.10"

# Dar permisos de ejecución
chmod +x setup-nfs-mount.sh

# Ejecutar el script
./setup-nfs-mount.sh
```

**Verificar que NFS está montado:**

```bash
df -h | grep nfs
ls -la /mnt/nfs_uploads
```

**IMPORTANTE:** Deberías ver los mismos directorios que en el Backend.

### Paso 7: Construir y levantar el servicio

```bash
cd ~/anb-worker/deployment/worker-instance

# Construir la imagen
docker-compose build

# Levantar el servicio en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Paso 8: Verificar que el worker está corriendo

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
# [2025-01-15 10:30:01] [INFO] Connected to redis://172.31.10.5:6379/0
# [2025-01-15 10:30:02] [INFO] Ready to accept tasks
```

### Paso 9: Verificar health check

```bash
# Desde la instancia Worker
curl http://localhost:8001/health

# Deberías ver algo como:
# {
#   "status": "healthy",
#   "celery_status": "running",
#   "redis_connection": "ok",
#   "database_connection": "ok",
#   "nfs_mount": "ok"
# }
```

### Paso 10: Verificar desde Flower (en Backend)

Abre en tu navegador:
```
http://<BACKEND_PUBLIC_IP>:5555
```

Deberías ver:
- 4 workers activos
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

2. **Ver el progreso en Flower:**

Abrir: `http://<BACKEND_PUBLIC_IP>:5555`

Deberías ver la tarea `process_video` en estado:
- `PENDING` → `STARTED` → `SUCCESS`

3. **Verificar en el NFS:**

```bash
# En el servidor NFS
ls -lh /mnt/nfs_share/uploads/original/
ls -lh /mnt/nfs_share/uploads/processed/

# Deberías ver el video original y el procesado
```

4. **Verificar logs del Worker:**

```bash
# En la instancia Worker
docker-compose logs -f worker | grep process_video
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

# Monitorear archivos procesados
watch -n 5 'ls -lht /mnt/nfs_uploads/processed/ | head -n 10'
```

### Limpiar archivos temporales

```bash
# Limpiar carpeta temp manualmente
sudo rm -rf /mnt/nfs_uploads/temp/*

# Verificar espacio en NFS
df -h /mnt/nfs_uploads
```

---

## Troubleshooting

### Error: "Cannot connect to Redis"

```bash
# Verificar conectividad
ping <BACKEND_PRIVATE_IP>
telnet <BACKEND_PRIVATE_IP> 6379

# Verificar Security Group del Backend permite puerto 6379 desde Worker
# Verificar que Redis está corriendo en Backend
```

### Error: "Cannot connect to database"

```bash
# Verificar que RDS es alcanzable
telnet <RDS_ENDPOINT> 5432

# Verificar credenciales en .env
cat .env | grep DATABASE_URL
```

### Error: "NFS mount failed"

```bash
# Verificar montaje
df -h | grep nfs

# Intentar remontar
sudo umount /mnt/nfs_uploads
./setup-nfs-mount.sh

# Ver logs del sistema
sudo journalctl -xe | grep mount
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

# Verificar conexión a Redis
docker exec -it anb-worker python -c "
from celery_app import app
app.connection().connect()
print('Redis OK')
"

# Verificar que las colas están configuradas
docker exec -it anb-worker celery -A celery_app inspect active_queues
```

### Tareas quedan en estado PENDING

```bash
# Ver tareas en Flower: http://<BACKEND_PUBLIC_IP>:5555

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
3. Ambas instancias consumirán de la misma cola Redis
4. Load balancing automático

---

## Monitoreo Continuo

### Health Check API

```bash
# Verificar salud cada 30 segundos
watch -n 30 'curl -s http://localhost:8001/health | jq'
```

### Métricas de Prometheus

```bash
# Ver métricas
curl http://localhost:8001/metrics
```

### Alertas (opcional)

Configurar alertas cuando:
- Worker deja de procesar tareas
- Tareas fallan repetidamente
- Espacio en NFS < 10%

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
# Montaje NFS
./setup-nfs-mount.sh

# Verificar conectividad Redis
redis-cli -h <BACKEND_PRIVATE_IP> ping

# Levantar worker
docker-compose up -d

# Ver logs
docker-compose logs -f worker

# Verificar salud
curl http://localhost:8001/health

# Ver tareas activas
docker exec -it anb-worker celery -A celery_app inspect active

# Monitorear archivos procesados
watch 'ls -lht /mnt/nfs_uploads/processed/ | head'

# Reiniciar
docker-compose restart worker

# Detener
docker-compose down
```
