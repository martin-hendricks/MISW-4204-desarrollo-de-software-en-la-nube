# Guía de Despliegue - Instancia Backend

## Resumen
Esta instancia EC2 contiene:
- ✅ Nginx (API Gateway) - Puerto 80
- ✅ Backend API (FastAPI) - Puerto 8000
- ✅ Integración con AWS SQS (Message Broker)
- ✅ Integración con AWS S3 (Almacenamiento de archivos)

---

## Requisitos Previos

### 1. Instancia EC2 configurada
- ✅ Ubuntu Server 22.04 LTS
- ✅ Tipo: t2.medium o superior
- ✅ Docker y Docker Compose instalados
- ✅ Security Group configurado (ver abajo)

### 2. Servicios externos creados
- ✅ RDS PostgreSQL creado y accesible
- ✅ AWS SQS colas creadas (main queue y DLQ)
- ✅ AWS S3 bucket creado
- ⏳ Worker (se desplegará después)

### 3. Información que necesitas tener a mano
- Endpoint de RDS PostgreSQL
- Usuario y contraseña de RDS
- Nombre de la base de datos en RDS
- SQS Queue URL y DLQ URL
- S3 Bucket Name
- AWS credentials (Access Key ID, Secret Access Key)

---

## Security Group - Backend Instance

### Inbound Rules

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | Your IP | Administración SSH |
| HTTP | TCP | 80 | 0.0.0.0/0 | Nginx - Acceso público |
| Custom TCP | TCP | 8000 | Your IP | Backend API (debug) |

### Outbound Rules
- All traffic (default)

---

## ⚠️ IMPORTANTE: Configuración Previa al Despliegue

**Antes de ejecutar `docker-compose up`**, debes configurar el archivo `.env` con los valores correctos:

### 📝 Archivo que DEBES editar:

| Archivo | Qué configurar |
|---------|----------------|
| **`.env`** | `DATABASE_URL` (RDS endpoint) |
| **`.env`** | `BASE_PATH` (URL pública del Backend - IP PÚBLICA de esta instancia) |
| **`.env`** | `SQS_QUEUE_URL` y `SQS_DLQ_URL` |
| **`.env`** | `S3_BUCKET_NAME` y credenciales AWS |

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
- Variables de configuración que no afectan conectividad (como `CORS_ORIGINS`)

---

## Pasos de Despliegue

### Paso 1: Conectarse a la instancia

```bash
ssh -i "your-key.pem" ubuntu@<BACKEND_PUBLIC_IP>
```

### Paso 2: Clonar/Copiar los archivos del proyecto

```bash
# Crear directorio de trabajo
mkdir -p ~/anb-backend
cd ~/anb-backend

# Opción A: Clonar repositorio (si está en GitHub)
git clone <your-repo-url> .
cd source/deployment/backend-instance

# Opción B: Copiar archivos manualmente usando SCP desde tu máquina local
# Desde tu máquina local:
# scp -i "your-key.pem" -r ./source/deployment/backend-instance ubuntu@<BACKEND_PUBLIC_IP>:~/anb-backend/
# scp -i "your-key.pem" -r ./source/backend ubuntu@<BACKEND_PUBLIC_IP>:~/anb-backend/
```

### Paso 3: Configurar variables de entorno

```bash
cd ~/anb-backend/deployment/backend-instance

# Copiar archivo de ejemplo
cp .env.example .env

# Editar con tus valores reales
nano .env
```

**Variables que DEBES cambiar:**

```bash
# RDS Database
DATABASE_URL=postgresql://admin:YourPassword@anb-db.xxx.us-east-1.rds.amazonaws.com:5432/anbdb

# AWS SQS
USE_SQS=true
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/anb-video-processing
SQS_DLQ_URL=https://sqs.us-east-1.amazonaws.com/123456789/anb-video-processing-dlq

# AWS S3
FILE_STORAGE_TYPE=s3
S3_BUCKET_NAME=anb-videos-bucket
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# JWT Secret (generar uno aleatorio)
SECRET_KEY=tu-clave-secreta-super-segura-minimo-32-caracteres

# Base Path (IP pública de esta instancia)
BASE_PATH=http://<BACKEND_PUBLIC_IP>/api/videos
```

### Paso 4: Configurar Almacenamiento S3

**Pre-requisito:** Tener creado el bucket S3 y las credenciales configuradas en `.env`

```bash
# Dar permisos de ejecución
chmod +x setup-s3.sh

# Ejecutar el script
./setup-s3.sh
```

El script:
- ✅ Valida las credenciales AWS
- ✅ Instala AWS CLI
- ✅ Configura las credenciales (incluyendo session_token si existe)
- ✅ Verifica/crea el bucket S3
- ✅ Crea estructura de carpetas (`original/`, `processed/`)

**Verificar acceso a S3:**

```bash
aws s3 ls s3://anb-videos-bucket-2025-team-2/
```

Deberías ver:

```
                           PRE original/
                           PRE processed/
```

---

### Paso 5: Inicializar Base de Datos (IMPORTANTE - Solo primera vez)

**⚠️ EJECUTAR ANTES de levantar docker-compose**

Este proyecto NO usa Alembic. Debes ejecutar el script `init.sql` manualmente:

```bash
cd ~/anb-backend/deployment/backend-instance

# Dar permisos de ejecución al script
chmod +x init-database.sh

# Ejecutar el script de inicialización
./init-database.sh
```

**¿Qué hace este script?**
- Verifica que postgresql-client esté instalado
- Conecta a tu RDS PostgreSQL
- Ejecuta el archivo `init.sql` que crea las tablas:
  - `players` (jugadores)
  - `videos` (videos)
  - `votes` (votos)

**Si ya ejecutaste este script antes:**
- Puedes saltar este paso
- Las tablas ya existen en RDS

**Alternativa manual (si prefieres hacerlo tú mismo):**

```bash
# Instalar cliente PostgreSQL
sudo apt install -y postgresql-client

# Ejecutar init.sql directamente
PGPASSWORD='TU_PASSWORD' psql \
  -h anb-database.ctxmjxakbtby.us-east-1.rds.amazonaws.com \
  -U admin \
  -d anbdb \
  -p 5432 \
  -f ~/anb-backend/source/database/init.sql
```

### Paso 6: Construir y levantar los servicios

```bash
cd ~/anb-backend/deployment/backend-instance

# Construir las imágenes
docker-compose build

# Levantar los servicios en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Paso 7: Verificar que los servicios están corriendo

```bash
# Ver estado de contenedores
docker-compose ps

# Deberías ver:
# NAME                IMAGE                    STATUS
# anb-nginx           nginx:alpine             Up (healthy)
# anb-backend         backend-instance-backend Up (healthy)
```

### Paso 8: Verificar endpoints

```bash
# Health check de Nginx
curl http://localhost/health
# Debería retornar: {"status":"healthy","service":"nginx"}

# Health check de Backend
curl http://localhost:8000/health
# Debería retornar información de salud del backend
```

### Paso 9: Acceso desde tu máquina local

```bash
# Reemplaza <BACKEND_PUBLIC_IP> con la IP pública de tu instancia

# Health check
curl http://<BACKEND_PUBLIC_IP>/health

# Swagger Docs
# Abrir en navegador: http://<BACKEND_PUBLIC_IP>/docs
```

---

## Comandos Útiles

### Ver logs

```bash
# Todos los servicios
docker-compose logs -f

# Solo backend
docker-compose logs -f backend

# Solo nginx
docker-compose logs -f nginx
```

### Reiniciar servicios

```bash
# Todos los servicios
docker-compose restart

# Solo backend
docker-compose restart backend
```

### Detener servicios

```bash
# Detener
docker-compose stop

# Detener y eliminar contenedores
docker-compose down

# Detener, eliminar contenedores Y volúmenes
docker-compose down -v
```

### Rebuild después de cambios en código

```bash
# Rebuild y restart
docker-compose up -d --build
```

### Monitorear recursos

```bash
# Uso de CPU y memoria de contenedores
docker stats

# Espacio en disco
df -h

# Espacio usado por Docker
docker system df
```

---

## Troubleshooting

### Error: "Cannot connect to database"

```bash
# Verificar que RDS es alcanzable
telnet <RDS_ENDPOINT> 5432

# Verificar Security Group de RDS permite conexión desde esta instancia
# Verificar credenciales en .env
```

### Error: "Cannot connect to S3"

```bash
# Verificar credenciales AWS
aws s3 ls s3://<YOUR_BUCKET_NAME>

# Verificar variables de entorno
docker exec -it anb-backend env | grep AWS

# Ver logs del backend
docker-compose logs backend
```

### Error: "Cannot connect to SQS"

```bash
# Verificar que las colas existen
aws sqs list-queues

# Verificar URL de la cola
aws sqs get-queue-attributes --queue-url <YOUR_QUEUE_URL>

# Ver logs del backend
docker-compose logs backend
```

### Backend no responde

```bash
# Ver logs del backend
docker-compose logs backend

# Verificar variables de entorno
docker exec -it anb-backend env | grep DATABASE_URL

# Reiniciar backend
docker-compose restart backend
```

### Nginx 502 Bad Gateway

```bash
# Verificar que backend está corriendo
docker-compose ps backend

# Ver logs de nginx
docker-compose logs nginx

# Verificar configuración de nginx
docker exec -it anb-nginx nginx -t
```

---

## Monitoreo Continuo

### Logs en tiempo real
```bash
# Mantener terminal abierta monitoreando logs
docker-compose logs -f --tail=100
```

### Health checks automáticos
Los contenedores tienen health checks configurados. Verifica con:

```bash
docker-compose ps
```

---

## Backup y Rollback

### Rollback a versión anterior

```bash
# Si tienes versión anterior en git
git checkout <previous-commit>
docker-compose up -d --build
```

---

## Siguientes Pasos

Una vez que el Backend esté funcionando correctamente:

1. ✅ Backend desplegado y funcionando
2. ⏭️ Desplegar instancia Worker
3. ⏭️ Probar flujo completo de upload y procesamiento
4. ⏭️ Configurar monitoreo y alertas
5. ⏭️ Configurar backups automáticos

---

## Comandos Rápidos de Referencia

```bash
# 1. Configurar archivos (ANTES de desplegar)
nano .env                    # DATABASE_URL, SECRET_KEY, BASE_PATH, SQS_QUEUE_URL, S3_BUCKET_NAME

# 2. Configurar S3
chmod +x setup-s3.sh
./setup-s3.sh

# 3. Inicializar base de datos (SOLO PRIMERA VEZ)
chmod +x init-database.sh
./init-database.sh

# 4. Levantar servicios
docker-compose up -d

# 5. Ver logs
docker-compose logs -f

# 6. Verificar salud
docker-compose ps
curl http://localhost/health

# Reiniciar servicios
docker-compose restart

# Detener servicios
docker-compose down
```
