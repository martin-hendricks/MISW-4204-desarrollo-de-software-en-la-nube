# Guía Maestra de Despliegue en AWS EC2

## ANB Rising Stars Showcase - Arquitectura Distribuida

---

## 📋 Índice

1. [Resumen de la Arquitectura](#resumen-de-la-arquitectura)
2. [Requisitos Previos](#requisitos-previos)
3. [Orden de Despliegue](#orden-de-despliegue)
4. [Archivos de Configuración](#archivos-de-configuración)
5. [Verificación Final](#verificación-final)
6. [Troubleshooting](#troubleshooting)

---

## Resumen de la Arquitectura

### Arquitectura Final

```
┌─────────────────────────────────────────────────────────────┐
│                         INTERNET                            │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP:80
                         ↓
        ┌────────────────────────────────────────┐
        │  EC2 Backend Instance                  │
        │  ┌──────────┐ ┌─────────┐ ┌─────────┐ │
        │  │  Nginx   │ │ Backend │ │  Redis  │ │
        │  │  (80)    │ │ (8000)  │ │ (6379)  │ │
        │  └──────────┘ └─────────┘ └─────────┘ │
        │       Flower (5555)                    │
        └─────┬──────────────────────┬───────────┘
              │                      │
              │ NFS:2049             │ Redis:6379
              ↓                      ↓
   ┌──────────────────┐    ┌──────────────────┐
   │  EC2 NFS Server  │    │  EC2 Worker      │
   │  File Storage    │◄───│  Video Processor │
   │  (2049)          │    │  (Celery+FFmpeg) │
   └──────────────────┘    └────────┬─────────┘
                                    │
                    ┌───────────────┴─────────────┐
                    │                             │
                    ↓                             ↓
          ┌──────────────────┐          ┌──────────────────┐
          │  RDS PostgreSQL  │          │  EC2 NFS Server  │
          │  Database        │          │  (2049)          │
          │  (5432)          │          └──────────────────┘
          └──────────────────┘
```

### Componentes

| Instancia | Servicios | Puertos | Tipo EC2 Recomendado |
|-----------|-----------|---------|----------------------|
| **Backend** | Nginx, FastAPI, Redis, Flower | 80, 8000, 6379, 5555 | t2.medium |
| **Worker** | Celery, FFmpeg, Health API | 8001 | t2.large |
| **NFS Server** | NFS Server | 2049, 111 | t2.small + 50GB EBS |
| **RDS** | PostgreSQL | 5432 | db.t3.micro |

---

## Requisitos Previos

### 1. Cuenta AWS Academy
- ✅ Acceso a AWS Academy Learner Lab
- ✅ Créditos disponibles ($100 inicial)
- ✅ Región: us-east-1 (recomendado)

### 2. Herramientas Locales
- ✅ Git instalado
- ✅ Cliente SSH configurado
- ✅ AWS CLI (opcional, pero recomendado)
- ✅ Tu par de llaves (.pem) descargado

### 3. Assets de Video
- ✅ `anb_logo.png` - Logo ANB (200x200px, PNG con transparencia)
- ✅ `intro.mp4` - Video intro (máx 2.5s, 1280x720)
- ✅ `outro.mp4` - Video outro (máx 2.5s, 1280x720)

---

## Orden de Despliegue

### Fase 1: Preparación (30 minutos)

#### 1.1 Crear Security Groups

```bash
# Ver guía completa en: SECURITY_GROUPS.md

# Orden de creación:
1. anb-backend-sg
2. anb-worker-sg
3. anb-nfs-sg
4. anb-rds-sg
```

📄 **Guía detallada:** [SECURITY_GROUPS.md](./SECURITY_GROUPS.md)

#### 1.2 Crear RDS PostgreSQL

**Pasos en AWS Console:**

1. RDS > Create Database
2. Engine: PostgreSQL 15.x
3. Templates: Free tier (o Dev/Test)
4. Settings:
   - DB instance identifier: `anb-database`
   - Master username: `postgres`
   - Master password: `<ANOTA_ESTA_PASSWORD>`
5. Instance configuration:
   - db.t3.micro (Free tier)
6. Storage:
   - 20 GB gp2
   - Desmarcar "Enable storage autoscaling"
7. Connectivity:
   - VPC: Default VPC
   - Public access: No (más seguro)
   - VPC security group: `anb-rds-sg`
8. Database name: `anbdb`
9. Create database

**Anotar:**
```
RDS_ENDPOINT: anb-database.xxxxx.us-east-1.rds.amazonaws.com
RDS_PORT: 5432
RDS_DATABASE: anbdb
RDS_USERNAME: postgres
RDS_PASSWORD: <tu_password>
```

---

### Fase 2: Servidor NFS (45 minutos)

#### 2.1 Crear Instancia EC2

**Especificaciones:**
- Name: `anb-nfs-server`
- AMI: Ubuntu Server 22.04 LTS
- Instance type: t2.small
- Key pair: Tu key pair
- Security group: `anb-nfs-sg`
- Storage:
  - Root: 8 GB gp3
  - **Agregar volumen adicional:** 50 GB gp3 (para videos)

#### 2.2 Configurar NFS Server

```bash
# Conectarse a la instancia
ssh -i "your-key.pem" ubuntu@<NFS_PUBLIC_IP>

# Seguir la guía completa
```

📄 **Guía detallada:** [NFS_SERVER_SETUP.md](./NFS_SERVER_SETUP.md)

**Anotar la IP privada:**
```bash
# Dentro de la instancia NFS
hostname -I
# Ejemplo: 172.31.10.10
```

```
NFS_PRIVATE_IP: 172.31.10.10
NFS_EXPORT_PATH: /mnt/nfs_share/uploads
```

---

### Fase 3: Backend Instance (60 minutos)

#### 3.1 Crear Instancia EC2

**Especificaciones:**
- Name: `anb-backend`
- AMI: Ubuntu Server 22.04 LTS
- Instance type: t2.medium
- Key pair: Tu key pair
- Security group: `anb-backend-sg`
- Storage: 20 GB gp3

#### 3.2 Instalar Docker y Docker Compose

```bash
# Conectarse
ssh -i "your-key.pem" ubuntu@<BACKEND_PUBLIC_IP>

# Instalar Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
# Cerrar sesión y volver a entrar para aplicar permisos
exit
ssh -i "your-key.pem" ubuntu@<BACKEND_PUBLIC_IP>

# Verificar
docker --version
docker-compose --version
```

#### 3.3 Copiar Archivos del Proyecto

**Opción A: Desde Git (recomendado)**
```bash
cd ~
git clone <YOUR_REPO_URL> anb-backend
cd anb-backend/source/deployment/backend-instance
```

**Opción B: Usando SCP desde tu máquina local**
```bash
# Desde tu máquina local
scp -i "your-key.pem" -r ./source/deployment/backend-instance ubuntu@<BACKEND_PUBLIC_IP>:~/
scp -i "your-key.pem" -r ./source/backend ubuntu@<BACKEND_PUBLIC_IP>:~/
scp -i "your-key.pem" -r ./source/api-gateway ubuntu@<BACKEND_PUBLIC_IP>:~/
```

#### 3.4 Configurar Variables de Entorno

```bash
cd ~/anb-backend/source/deployment/backend-instance

# Copiar y editar .env
cp .env.example .env
nano .env
```

**Completar con tus valores:**
```bash
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@anb-database.xxxxx.us-east-1.rds.amazonaws.com:5432/anbdb
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<genera-una-clave-secreta-larga>
BASE_PATH=http://<BACKEND_PUBLIC_IP>/api/videos
```

#### 3.5 Montar NFS y Desplegar

```bash
# Configurar NFS
nano setup-nfs-mount.sh
# Cambiar: NFS_SERVER_IP="172.31.10.10" (usa tu IP privada del NFS)

chmod +x setup-nfs-mount.sh
./setup-nfs-mount.sh

# Verificar montaje
df -h | grep nfs

# Levantar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f
```

📄 **Guía detallada:** [backend-instance/DEPLOY.md](./backend-instance/DEPLOY.md)

#### 3.6 Ejecutar Migraciones de Base de Datos

```bash
# Entrar al contenedor
docker exec -it anb-backend bash

# Ejecutar migraciones
alembic upgrade head

# Salir
exit
```

**Anotar la IP pública del Backend:**
```
BACKEND_PUBLIC_IP: 54.123.45.67
BACKEND_PRIVATE_IP: 172.31.10.5
```

---

### Fase 4: Worker Instance (45 minutos)

#### 4.1 Crear Instancia EC2

**Especificaciones:**
- Name: `anb-worker`
- AMI: Ubuntu Server 22.04 LTS
- Instance type: t2.large (recomendado para procesamiento de video)
- Key pair: Tu key pair
- Security group: `anb-worker-sg`
- Storage: 20 GB gp3

#### 4.2 Instalar Docker y Docker Compose

```bash
# Conectarse
ssh -i "your-key.pem" ubuntu@<WORKER_PUBLIC_IP>

# Instalar Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
exit
ssh -i "your-key.pem" ubuntu@<WORKER_PUBLIC_IP>
```

#### 4.3 Copiar Archivos del Proyecto

```bash
# Opción A: Git
cd ~
git clone <YOUR_REPO_URL> anb-worker
cd anb-worker/source/deployment/worker-instance

# Opción B: SCP desde tu máquina local
# scp -i "your-key.pem" -r ./source/deployment/worker-instance ubuntu@<WORKER_PUBLIC_IP>:~/
# scp -i "your-key.pem" -r ./source/worker ubuntu@<WORKER_PUBLIC_IP>:~/
```

#### 4.4 Copiar Assets de Video

```bash
# Crear carpeta assets
mkdir -p ~/anb-worker/source/deployment/worker-instance/assets

# Desde tu máquina local, copiar assets:
scp -i "your-key.pem" anb_logo.png ubuntu@<WORKER_PUBLIC_IP>:~/anb-worker/source/deployment/worker-instance/assets/
scp -i "your-key.pem" intro.mp4 ubuntu@<WORKER_PUBLIC_IP>:~/anb-worker/source/deployment/worker-instance/assets/
scp -i "your-key.pem" outro.mp4 ubuntu@<WORKER_PUBLIC_IP>:~/anb-worker/source/deployment/worker-instance/assets/

# Verificar
ls -lh ~/anb-worker/source/deployment/worker-instance/assets/
```

#### 4.5 Configurar Variables de Entorno

```bash
cd ~/anb-worker/source/deployment/worker-instance

cp .env.example .env
nano .env
```

**Completar con tus valores:**
```bash
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@anb-database.xxxxx.us-east-1.rds.amazonaws.com:5432/anbdb
REDIS_URL=redis://172.31.10.5:6379/0  # IP PRIVADA del Backend
BASE_PATH=http://54.123.45.67/api/videos  # IP PÚBLICA del Backend
```

#### 4.6 Verificar Conectividad con Redis

```bash
# Instalar redis-tools
sudo apt install -y redis-tools

# Probar conexión (usa IP privada del Backend)
redis-cli -h 172.31.10.5 ping
# Debe retornar: PONG
```

#### 4.7 Montar NFS y Desplegar

```bash
# Configurar NFS
nano setup-nfs-mount.sh
# Cambiar: NFS_SERVER_IP="172.31.10.10" (tu IP privada del NFS)

chmod +x setup-nfs-mount.sh
./setup-nfs-mount.sh

# Verificar montaje
df -h | grep nfs
ls -la /mnt/nfs_uploads  # Deberías ver los mismos archivos que en Backend

# Levantar worker
docker-compose up -d

# Ver logs
docker-compose logs -f
```

📄 **Guía detallada:** [worker-instance/DEPLOY.md](./worker-instance/DEPLOY.md)

---

## Verificación Final

### 1. Health Checks

```bash
# Backend
curl http://<BACKEND_PUBLIC_IP>/health

# Backend API
curl http://<BACKEND_PUBLIC_IP>/docs
# Debería abrir Swagger UI en el navegador

# Worker Health
curl http://<WORKER_PUBLIC_IP>:8001/health
```

### 2. Flower Monitoring

Abrir en navegador:
```
http://<BACKEND_PUBLIC_IP>:5555
```

Deberías ver:
- 4 workers activos
- Queues: `video_processing` y `dlq`

### 3. Test End-to-End

#### 3.1 Crear un usuario (desde tu máquina local)

```bash
curl -X POST http://<BACKEND_PUBLIC_IP>/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123456",
    "full_name": "Test User",
    "birth_date": "2000-01-01",
    "country": "USA",
    "gender": "M"
  }'
```

#### 3.2 Login

```bash
curl -X POST http://<BACKEND_PUBLIC_IP>/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=Test123456"

# Guardar el access_token que retorna
```

#### 3.3 Subir un video

```bash
curl -X POST http://<BACKEND_PUBLIC_IP>/api/videos/upload \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "file=@test_video.mp4"

# Debería retornar:
# {
#   "id": "...",
#   "status": "processing",
#   "url": "..."
# }
```

#### 3.4 Monitorear procesamiento

**En Flower:**
```
http://<BACKEND_PUBLIC_IP>:5555/tasks
```

**En logs del Worker:**
```bash
# Desde la instancia Worker
docker-compose logs -f worker | grep process_video
```

**Verificar archivos en NFS:**
```bash
# Desde el servidor NFS
ls -lh /mnt/nfs_share/uploads/original/
ls -lh /mnt/nfs_share/uploads/processed/
```

#### 3.5 Obtener el video procesado

```bash
# Listar videos
curl -X GET http://<BACKEND_PUBLIC_IP>/api/videos \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# El video debería tener status: "processed"
```

---

## Archivos de Configuración

### Estructura del Directorio `deployment/`

```
deployment/
├── README.md                          # Este archivo
├── SECURITY_GROUPS.md                 # Configuración de Security Groups
├── NFS_SERVER_SETUP.md                # Guía servidor NFS
├── backend-instance/
│   ├── DEPLOY.md                      # Guía despliegue Backend
│   ├── docker-compose.yml             # Compose para Backend
│   ├── nginx.conf                     # Configuración Nginx
│   ├── .env.example                   # Variables de entorno
│   └── setup-nfs-mount.sh             # Script montaje NFS
└── worker-instance/
    ├── DEPLOY.md                      # Guía despliegue Worker
    ├── docker-compose.yml             # Compose para Worker
    ├── .env.example                   # Variables de entorno
    ├── setup-nfs-mount.sh             # Script montaje NFS
    └── assets/                        # Logo, intro, outro
        ├── anb_logo.png
        ├── intro.mp4
        └── outro.mp4
```

---

## Troubleshooting

### Problema: Backend no se conecta a RDS

**Síntomas:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solución:**
1. Verificar que el Security Group `anb-rds-sg` permite conexiones desde `anb-backend-sg`
2. Verificar el endpoint de RDS en `.env`
3. Verificar usuario/password
4. Probar desde la instancia:
   ```bash
   sudo apt install postgresql-client
   psql -h <RDS_ENDPOINT> -U postgres -d anbdb
   ```

### Problema: Worker no se conecta a Redis

**Síntomas:**
```
[ERROR] Cannot connect to redis://...
```

**Solución:**
1. Verificar Security Group `anb-backend-sg` permite puerto 6379 desde `anb-worker-sg`
2. Usar la IP PRIVADA del Backend en `REDIS_URL`, no la pública
3. Verificar que Redis está corriendo:
   ```bash
   # En Backend
   docker ps | grep redis
   ```
4. Probar conectividad:
   ```bash
   # En Worker
   telnet <BACKEND_PRIVATE_IP> 6379
   redis-cli -h <BACKEND_PRIVATE_IP> ping
   ```

### Problema: NFS mount failed

**Síntomas:**
```
mount.nfs: Connection timed out
```

**Solución:**
1. Verificar que el servidor NFS está corriendo
2. Verificar Security Group `anb-nfs-sg` permite puerto 2049 desde las instancias
3. Verificar que usas la IP PRIVADA del NFS, no la pública
4. En el servidor NFS, verificar exports:
   ```bash
   sudo exportfs -v
   showmount -e localhost
   ```

### Problema: Videos no se procesan

**Verificar:**
1. Worker está corriendo: `docker-compose ps`
2. Worker ve las tareas: Ver logs o Flower
3. NFS está montado en Worker: `df -h | grep nfs`
4. Assets existen: `docker exec -it anb-worker ls -la /app/assets`
5. FFmpeg funciona: `docker exec -it anb-worker ffmpeg -version`

---

## Costos Estimados (AWS Academy)

| Servicio | Tipo | Costo/hora | Costo/mes (24/7) |
|----------|------|------------|------------------|
| Backend EC2 | t2.medium | $0.0464 | ~$33.80 |
| Worker EC2 | t2.large | $0.0928 | ~$67.60 |
| NFS EC2 | t2.small | $0.023 | ~$16.70 |
| RDS | db.t3.micro | $0.016 | ~$11.70 |
| **TOTAL** | | **$0.1782/hora** | **~$129.80/mes** |

**Nota:** AWS Academy provee $100 en créditos. Para optimizar:
- Detén instancias cuando no las uses
- Usa snapshots y recrea instancias cuando necesites
- No dejes corriendo 24/7 en ambiente de prueba

---

## Mantenimiento y Operación

### Detener servicios (ahorrar costos)

```bash
# En cada instancia
docker-compose down

# En AWS Console, detener instancias EC2
# IMPORTANTE: No terminar, solo stop
```

### Reiniciar servicios

```bash
# Iniciar instancias EC2 desde AWS Console
# Nota: Las IPs públicas cambiarán, pero las privadas se mantienen

# En cada instancia
docker-compose up -d
```

### Ver logs agregados

```bash
# Backend
ssh -i key.pem ubuntu@<BACKEND_IP>
cd ~/anb-backend/source/deployment/backend-instance
docker-compose logs -f --tail=100

# Worker
ssh -i key.pem ubuntu@<WORKER_IP>
cd ~/anb-worker/source/deployment/worker-instance
docker-compose logs -f --tail=100
```

### Actualizar código

```bash
# En cada instancia
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Próximos Pasos

1. ✅ Infraestructura desplegada
2. ⏭️ Configurar dominio personalizado (Route 53)
3. ⏭️ Configurar HTTPS con Let's Encrypt
4. ⏭️ Implementar CI/CD con GitHub Actions
5. ⏭️ Configurar backups automáticos
6. ⏭️ Implementar monitoreo con CloudWatch
7. ⏭️ Escalar horizontalmente (Auto Scaling Groups)

---

## Soporte

Para preguntas o problemas:
1. Revisa los logs: `docker-compose logs -f`
2. Verifica health checks: `/health` endpoints
3. Consulta Flower: `http://<BACKEND_IP>:5555`
4. Revisa las guías individuales en cada carpeta

---

**¡Listo para producción!** 🚀
