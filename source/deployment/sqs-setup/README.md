# 🚀 AWS SQS Setup - ANB Rising Stars Showcase

Este directorio contiene toda la configuración necesaria para migrar de Redis a AWS SQS como message broker para el procesamiento de videos.

---

## 📋 Tabla de Contenidos

- [¿Por qué SQS?](#por-qué-sqs)
- [Arquitectura](#arquitectura)
- [Prerequisitos](#prerequisitos)
- [Guía Rápida](#guía-rápida)
- [Guía Detallada](#guía-detallada)
- [Verificación](#verificación)
- [Troubleshooting](#troubleshooting)
- [Rollback](#rollback)

---

## 🎯 ¿Por qué SQS?

### Problema con Redis en Autoscaling

Con Redis en el backend, al hacer autoscaling se crean múltiples instancias de Redis no coordinadas:

```
❌ PROBLEMA:
Backend 1 (Redis 1) ─┐
Backend 2 (Redis 2) ─┼─ ¿Worker consume de cuál? 🤔
Backend 3 (Redis 3) ─┘
```

### Solución: AWS SQS

```
✅ SOLUCIÓN:
Backend 1 ─┐
Backend 2 ─┼─→ AWS SQS (managed) ─→ Worker 1
Backend 3 ─┘                      ├─→ Worker 2
                                  └─→ Worker 3
```

### Beneficios

| Aspecto | Redis (actual) | AWS SQS |
|---------|---------------|---------|
| **Autoscaling Backend** | ❌ Problemático | ✅ Nativo |
| **Autoscaling Worker** | ⚠️ Complejo | ✅ Fácil |
| **Disponibilidad** | ❌ Single point | ✅ 99.9% SLA |
| **Mantenimiento** | ❌ Manual | ✅ Cero |
| **Costo mensual** | ~$0 (en EC2) | ~$0.50 |
| **Persistencia** | ⚠️ Solo RAM | ✅ Garantizada |
| **DLQ nativo** | ❌ No | ✅ Sí |

---

## 🏗️ Arquitectura

### Arquitectura Actual (Redis)

```
Internet
   ↓
Backend EC2 (Nginx + FastAPI + Redis) → RDS PostgreSQL
   ↓                    ↓
NFS Server  ←────── Worker EC2 (Celery)
```

### Nueva Arquitectura (SQS)

```
Internet
   ↓
Backend EC2 (Nginx + FastAPI) ─┐
                                ├─→ AWS SQS ─→ Worker EC2 (Celery)
                                │              Worker EC2 (Celery)
                                └─→ RDS PostgreSQL
                                         ↓
                                    NFS Server
```

### Componentes SQS

```
anb-video-processing-queue (Cola Principal)
  ├─ Visibility Timeout: 3600s (1 hora)
  ├─ Message Retention: 4 días
  ├─ Receive Wait Time: 20s (long polling)
  └─ Redrive Policy: 3 reintentos → DLQ

anb-video-processing-dlq (Dead Letter Queue)
  ├─ Visibility Timeout: 3600s
  └─ Message Retention: 14 días
```

---

## ✅ Prerequisitos

### 1. AWS CLI

```bash
# Verificar instalación
aws --version

# Si no está instalado:
# macOS: brew install awscli
# Ubuntu: sudo apt install awscli
# Windows: descargar desde https://aws.amazon.com/cli/
```

### 2. Credenciales AWS

```bash
# Configurar credenciales
aws configure

# Ingresar:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: us-east-1
# - Default output: json

# Verificar
aws sts get-caller-identity
```

### 3. Permisos AWS

Tu usuario AWS necesita permisos para:
- ✅ SQS: `CreateQueue`, `DeleteQueue`, `GetQueueAttributes`
- ✅ IAM: `CreatePolicy`, `CreateRole`, `AttachRolePolicy`
- ✅ EC2: `AssociateIamInstanceProfile`

---

## 🚀 Guía Rápida

Si ya conoces el proceso:

```bash
# 1. Ir al directorio
cd deployment/sqs-setup

# 2. Crear colas SQS
chmod +x setup-sqs.sh
./setup-sqs.sh us-east-1

# 3. Configurar permisos IAM
chmod +x setup-iam.sh
./setup-iam.sh

# 4. Adjuntar Instance Profile a instancias EC2
aws ec2 associate-iam-instance-profile \
  --instance-id i-BACKEND_INSTANCE_ID \
  --iam-instance-profile Name=ANB-EC2-SQS-InstanceProfile

aws ec2 associate-iam-instance-profile \
  --instance-id i-WORKER_INSTANCE_ID \
  --iam-instance-profile Name=ANB-EC2-SQS-InstanceProfile

# 5. Actualizar .env del backend y worker (ver sqs-config.env)

# 6. Redesplegar servicios
```

---

## 📖 Guía Detallada

### Paso 1: Crear Colas SQS (5 min)

```bash
cd deployment/sqs-setup

# Dar permisos de ejecución
chmod +x setup-sqs.sh

# Ejecutar script (región por defecto: us-east-1)
./setup-sqs.sh

# O especificar región:
./setup-sqs.sh us-west-2
```

**¿Qué hace este script?**
- ✅ Crea cola principal `anb-video-processing-queue`
- ✅ Crea Dead Letter Queue `anb-video-processing-dlq`
- ✅ Configura redrive policy (3 reintentos)
- ✅ Guarda configuración en `sqs-config.env`

**Output esperado:**
```
==================================================
✅ Colas SQS creadas exitosamente
==================================================

📋 RESUMEN:

  Región:           us-east-1
  Account ID:       123456789012

  Cola Principal:   anb-video-processing-queue
  URL:              https://sqs.us-east-1.amazonaws.com/123456789012/anb-video-processing-queue

  Dead Letter Queue: anb-video-processing-dlq
  URL:              https://sqs.us-east-1.amazonaws.com/123456789012/anb-video-processing-dlq

📄 Archivo de configuración: sqs-config.env
```

**Verificar en AWS Console:**
```
AWS Console > SQS > Queues
- anb-video-processing-queue (Available)
- anb-video-processing-dlq (Available)
```

---

### Paso 2: Configurar Permisos IAM (5 min)

```bash
# Dar permisos de ejecución
chmod +x setup-iam.sh

# Ejecutar script
./setup-iam.sh
```

**¿Qué hace este script?**
- ✅ Crea política IAM `ANB-SQS-Access-Policy` con permisos para SQS
- ✅ Crea role IAM `ANB-EC2-SQS-Role` para instancias EC2
- ✅ Crea instance profile `ANB-EC2-SQS-InstanceProfile`
- ✅ Adjunta política al role
- ✅ Actualiza `sqs-config.env` con ARNs

**Output esperado:**
```
==================================================
✅ Configuración IAM completada
==================================================

📋 RESUMEN:

  Política IAM:       ANB-SQS-Access-Policy
  Policy ARN:         arn:aws:iam::123456789012:policy/ANB-SQS-Access-Policy

  Role IAM:           ANB-EC2-SQS-Role
  Role ARN:           arn:aws:iam::123456789012:role/ANB-EC2-SQS-Role

  Instance Profile:   ANB-EC2-SQS-InstanceProfile
```

**Verificar en AWS Console:**
```
AWS Console > IAM > Policies
- ANB-SQS-Access-Policy (creada)

AWS Console > IAM > Roles
- ANB-EC2-SQS-Role (creado)
```

---

### Paso 3: Adjuntar Instance Profile a Instancias EC2 (5 min)

#### Opción A: Instancias Existentes

```bash
# Obtener IDs de las instancias
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=anb-backend" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text

aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=anb-worker" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text

# Adjuntar Instance Profile al Backend
aws ec2 associate-iam-instance-profile \
  --instance-id i-XXXXXXXXX \
  --iam-instance-profile Name=ANB-EC2-SQS-InstanceProfile

# Adjuntar Instance Profile al Worker
aws ec2 associate-iam-instance-profile \
  --instance-id i-YYYYYYYYY \
  --iam-instance-profile Name=ANB-EC2-SQS-InstanceProfile

# Verificar
aws ec2 describe-instances \
  --instance-ids i-XXXXXXXXX \
  --query 'Reservations[0].Instances[0].IamInstanceProfile'
```

#### Opción B: Nuevas Instancias

Al crear nuevas instancias EC2, incluir el Instance Profile:

```bash
aws ec2 run-instances \
  --image-id ami-XXXXXXXXX \
  --instance-type t2.medium \
  --iam-instance-profile Name=ANB-EC2-SQS-InstanceProfile \
  ...
```

O en la AWS Console:
```
EC2 > Launch Instance > Advanced Details > IAM instance profile
→ Seleccionar: ANB-EC2-SQS-InstanceProfile
```

---

### Paso 4: Actualizar Código de la Aplicación (30 min)

#### 4.1 Actualizar requirements.txt

**Backend: `source/backend/requirements.txt`**
```diff
 celery==5.3.4
 redis==5.0.1
+kombu[sqs]==5.3.4
+boto3==1.34.25
```

**Worker: `source/worker/requirements.txt`**
```diff
 celery==5.3.4
 redis==5.0.1
+kombu[sqs]==5.3.4
+boto3==1.34.25
```

#### 4.2 Actualizar settings.py

**Archivo: `source/backend/app/config/settings.py`**

```python
# Agregar después de REDIS_URL (línea 23)

# AWS SQS (para migración de Redis)
USE_SQS: bool = os.getenv("USE_SQS", "false").lower() == "true"
SQS_QUEUE_URL: str = os.getenv("SQS_QUEUE_URL", "")
SQS_DLQ_URL: str = os.getenv("SQS_DLQ_URL", "")
```

#### 4.3 Actualizar celery_client.py

**Archivo: `source/backend/app/infrastructure/external_services/celery_client.py`**

Modificar la configuración de Celery para soportar SQS:

```python
# Después de los imports, agregar:
from app.config.settings import settings

# Modificar configuración de celery_app
if settings.USE_SQS:
    # Configuración para AWS SQS
    celery_app.conf.update(
        broker_url='sqs://',
        broker_transport_options={
            'region': settings.AWS_REGION,
            'predefined_queues': {
                'video_processing': {
                    'url': settings.SQS_QUEUE_URL,
                },
                'dlq': {
                    'url': settings.SQS_DLQ_URL,
                }
            },
            'polling_interval': 20,  # Long polling
            'visibility_timeout': 3600,  # 1 hora
        },
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        task_ignore_result=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
    )
else:
    # Configuración para Redis (existente)
    celery_app.conf.update(
        broker_url=settings.REDIS_URL,
        task_serializer='json',
        task_ignore_result=True,
    )
```

#### 4.4 Actualizar worker/celery_app.py

**Archivo: `source/worker/celery_app.py`**

Aplicar la misma lógica condicional:

```python
# Agregar después de imports
from config import config

# Modificar configuración (alrededor de línea 25)
if config.USE_SQS:
    # Configuración SQS
    app.conf.update(
        broker_url='sqs://',
        broker_transport_options={
            'region': config.AWS_REGION,
            'predefined_queues': {
                'video_processing': {
                    'url': config.SQS_QUEUE_URL,
                },
                'dlq': {
                    'url': config.SQS_DLQ_URL,
                }
            },
            'polling_interval': 20,
            'visibility_timeout': 3600,
        },
        task_serializer='json',
        accept_content=['json'],
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=50,
    )
else:
    # Configuración Redis (existente)
    app.conf.update(
        broker_url=config.REDIS_URL,
        # ... resto de configuración existente
    )
```

#### 4.5 Actualizar worker/config.py

**Archivo: `source/worker/config.py`**

```python
# Agregar nuevas variables (después de REDIS_URL)
USE_SQS: bool = os.getenv('USE_SQS', 'false').lower() == 'true'
AWS_REGION: str = os.getenv('AWS_REGION', 'us-east-1')
SQS_QUEUE_URL: str = os.getenv('SQS_QUEUE_URL', '')
SQS_DLQ_URL: str = os.getenv('SQS_DLQ_URL', '')
```

---

### Paso 5: Actualizar Configuración de Deployment (10 min)

#### 5.1 Backend Instance

**Archivo: `deployment/backend-instance/.env`**

Agregar al final del archivo (copiar valores de `sqs-config.env`):

```bash
# ============================================
# AWS SQS Configuration
# ============================================
USE_SQS=true
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/anb-video-processing-queue
SQS_DLQ_URL=https://sqs.us-east-1.amazonaws.com/123456789012/anb-video-processing-dlq
```

**Archivo: `deployment/backend-instance/docker-compose.yml`**

Comentar o eliminar el servicio Redis:

```yaml
# ===== REDIS BROKER ===== (YA NO NECESARIO CON SQS)
# redis:
#   image: redis:7-alpine
#   container_name: anb-redis
#   ...
```

También remover la dependencia de Redis del backend:

```yaml
backend:
  # ...
  depends_on:
    # redis:                    # REMOVER ESTA LÍNEA
    #   condition: service_healthy  # REMOVER ESTA LÍNEA
```

#### 5.2 Worker Instance

**Archivo: `deployment/worker-instance/.env`**

Agregar (copiar valores de `sqs-config.env`):

```bash
# ============================================
# AWS SQS Configuration
# ============================================
USE_SQS=true
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/anb-video-processing-queue
SQS_DLQ_URL=https://sqs.us-east-1.amazonaws.com/123456789012/anb-video-processing-dlq
```

---

### Paso 6: Redesplegar Servicios (15 min)

#### 6.1 Backend

```bash
# Conectar a instancia Backend
ssh -i "your-key.pem" ubuntu@<BACKEND_PUBLIC_IP>

cd ~/anb-backend/deployment/backend-instance

# Editar .env y agregar variables SQS
nano .env

# Rebuild y redesplegar (sin Redis)
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar que NO hay Redis
docker ps
# Deberías ver solo: anb-nginx, anb-backend (sin anb-redis)
```

#### 6.2 Worker

```bash
# Conectar a instancia Worker
ssh -i "your-key.pem" ubuntu@<WORKER_PUBLIC_IP>

cd ~/anb-worker/deployment/worker-instance

# Editar .env y agregar variables SQS
nano .env

# Rebuild y redesplegar
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Ver logs
docker-compose logs -f worker

# Deberías ver líneas como:
# [INFO] Connected to SQS queue: anb-video-processing-queue
```

---

## ✅ Verificación

### 1. Verificar Colas en AWS Console

```
AWS Console > SQS > Queues
→ anb-video-processing-queue
  - Messages Available: 0
  - Messages in Flight: 0
```

### 2. Verificar Permisos desde EC2

```bash
# Conectar a Backend o Worker
ssh -i "your-key.pem" ubuntu@<EC2_IP>

# Verificar credenciales (debe usar IAM Role)
aws sts get-caller-identity

# Listar colas (debe funcionar)
aws sqs list-queues

# Enviar mensaje de prueba
aws sqs send-message \
  --queue-url "https://sqs.us-east-1.amazonaws.com/.../anb-video-processing-queue" \
  --message-body "Test message"

# Recibir mensaje
aws sqs receive-message \
  --queue-url "https://sqs.us-east-1.amazonaws.com/.../anb-video-processing-queue"
```

### 3. Test End-to-End

```bash
# Desde tu máquina local

# 1. Login
curl -X POST http://<BACKEND_PUBLIC_IP>/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@test.com&password=Test123456"

# Guardar token

# 2. Subir video
curl -X POST http://<BACKEND_PUBLIC_IP>/api/videos/upload \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@test_video.mp4"

# 3. Monitorear logs del worker
# En instancia Worker:
docker-compose logs -f worker | grep process_video

# 4. Verificar en AWS Console
AWS Console > SQS > anb-video-processing-queue > Send and receive messages
→ Ver mensajes en la cola (o Messages in Flight si está procesando)

# 5. Verificar que video se procesó
curl -X GET http://<BACKEND_PUBLIC_IP>/api/videos \
  -H "Authorization: Bearer <TOKEN>"

# Status debe ser: "processed"
```

---

## 🐛 Troubleshooting

### Error: "Access Denied to SQS"

**Síntoma:**
```
boto.exception.SQSError: SQSError: 403 Forbidden
```

**Solución:**
```bash
# Verificar que Instance Profile está adjunto
aws ec2 describe-instances \
  --instance-ids i-XXXXXXXXX \
  --query 'Reservations[0].Instances[0].IamInstanceProfile'

# Si no hay Instance Profile, adjuntar:
aws ec2 associate-iam-instance-profile \
  --instance-id i-XXXXXXXXX \
  --iam-instance-profile Name=ANB-EC2-SQS-InstanceProfile

# Reiniciar servicios
docker-compose restart
```

---

### Error: "Queue does not exist"

**Síntoma:**
```
AWS.SimpleQueueService.NonExistentQueue
```

**Solución:**
```bash
# Verificar URL en .env
cat .env | grep SQS_QUEUE_URL

# Verificar que cola existe
aws sqs list-queues

# Si no existe, crear de nuevo
./setup-sqs.sh
```

---

### Worker no consume mensajes

**Síntoma:**
```
Messages Available: 5
Messages in Flight: 0
Worker logs: No activity
```

**Solución:**
```bash
# Ver logs del worker
docker-compose logs -f worker

# Verificar configuración
docker exec -it anb-worker python -c "
from config import config
print('USE_SQS:', config.USE_SQS)
print('SQS_QUEUE_URL:', config.SQS_QUEUE_URL)
"

# Reiniciar worker
docker-compose restart worker

# Verificar conectividad a SQS desde worker
docker exec -it anb-worker aws sqs list-queues
```

---

### Mensajes van a DLQ

**Síntoma:**
```
anb-video-processing-dlq - Messages Available: 3
```

**Solución:**
```bash
# Ver mensajes en DLQ
aws sqs receive-message \
  --queue-url "https://sqs.us-east-1.amazonaws.com/.../anb-video-processing-dlq" \
  --max-number-of-messages 10

# Analizar error (ver body del mensaje)
# Corregir issue
# Mover mensajes de vuelta a cola principal (redrive)

# AWS Console > SQS > anb-video-processing-dlq > Start DLQ redrive
```

---

## 🔄 Rollback a Redis

Si necesitas volver a Redis:

### Opción 1: Feature Flag

```bash
# En .env del backend y worker
USE_SQS=false  # Cambiar a false

# Levantar Redis de nuevo en backend
# Descomentar servicio redis en docker-compose.yml
docker-compose up -d

# Reiniciar servicios
docker-compose restart
```

### Opción 2: Limpiar SQS completamente

```bash
cd deployment/sqs-setup

# Eliminar colas y recursos IAM
chmod +x cleanup-sqs.sh
./cleanup-sqs.sh --confirm

# Revertir cambios en código (git)
git checkout main -- source/backend/requirements.txt
git checkout main -- source/worker/requirements.txt
# ... etc

# Redesplegar con Redis
```

---

## 📊 Comparativa de Costos

### Redis en EC2 (Actual)

```
EC2 Backend (t2.medium): $0.0464/hora × 730h = $33.87/mes
  ├─ Nginx
  ├─ FastAPI
  └─ Redis ← Usando recursos de EC2

TOTAL: $0/mes adicional (incluido en EC2)
```

### AWS SQS (Nuevo)

```
Requests: 10,000 videos/mes × 10 requests/video = 100,000 requests/mes
  ├─ SendMessage: 10,000
  ├─ ReceiveMessage: 30,000 (long polling)
  ├─ DeleteMessage: 10,000
  └─ Otros: 50,000

Primeros 1M requests/mes: GRATIS

TOTAL: $0/mes (dentro del free tier)
```

**Nota:** Incluso con 100,000 videos/mes (1M requests), el costo sería ~$0.40/mes.

---

## 📚 Recursos Adicionales

- [AWS SQS Documentation](https://docs.aws.amazon.com/sqs/)
- [Celery with SQS](https://docs.celeryproject.org/en/stable/userguide/configuration.html#broker-settings)
- [Kombu SQS Transport](https://kombu.readthedocs.io/en/stable/reference/kombu.transport.SQS.html)
- [IAM Roles for EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html)

---

## 🎯 Checklist de Migración

- [ ] AWS CLI instalado y configurado
- [ ] Ejecutar `./setup-sqs.sh`
- [ ] Ejecutar `./setup-iam.sh`
- [ ] Adjuntar Instance Profile a EC2 backend
- [ ] Adjuntar Instance Profile a EC2 worker
- [ ] Actualizar `backend/requirements.txt`
- [ ] Actualizar `worker/requirements.txt`
- [ ] Actualizar `backend/app/config/settings.py`
- [ ] Actualizar `backend/.../celery_client.py`
- [ ] Actualizar `worker/config.py`
- [ ] Actualizar `worker/celery_app.py`
- [ ] Actualizar `backend-instance/.env`
- [ ] Modificar `backend-instance/docker-compose.yml` (quitar Redis)
- [ ] Actualizar `worker-instance/.env`
- [ ] Redesplegar backend (sin Redis)
- [ ] Redesplegar worker
- [ ] Test end-to-end
- [ ] Monitorear métricas en AWS Console

---

## 🚀 ¡Listo!

Has migrado exitosamente de Redis a AWS SQS. Tu arquitectura ahora es:

✅ Completamente serverless (message broker)
✅ Auto-escalable (backend y workers)
✅ Altamente disponible (99.9% SLA)
✅ Sin mantenimiento (managed service)
✅ Económica (~$0/mes con free tier)

**¡Felicitaciones! 🎉**

---

**Última actualización:** Noviembre 2025
**Versión:** 1.0
