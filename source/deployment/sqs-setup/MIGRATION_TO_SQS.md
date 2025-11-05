# 🚀 Guía de Migración: Redis → AWS SQS

Esta guía te ayudará a migrar tu arquitectura de Redis (en backend) a AWS SQS como message broker para el sistema de colas de ANB Rising Stars.

---

## 📋 Índice

- [¿Por qué migrar?](#por-qué-migrar)
- [Antes de empezar](#antes-de-empezar)
- [Pasos de migración](#pasos-de-migración)
- [Verificación](#verificación)
- [Rollback](#rollback)

---

## 🎯 ¿Por qué migrar?

### Problema Actual

Con Redis en el backend, al escalar horizontalmente el backend se crean múltiples instancias de Redis descoordinadas:

```
❌ PROBLEMA:
Backend 1 (Redis 1) ─┐
Backend 2 (Redis 2) ─┼─ Worker no sabe de cuál consumir
Backend 3 (Redis 3) ─┘
```

### Solución: AWS SQS

```
✅ SOLUCIÓN:
Backend 1 ─┐
Backend 2 ─┼─→ AWS SQS (managed) ─→ Worker 1, Worker 2, Worker 3
Backend 3 ─┘
```

**Beneficios:**
- ✅ Autoscaling nativo (backends y workers)
- ✅ Alta disponibilidad (99.9% SLA)
- ✅ Sin mantenimiento (managed service)
- ✅ Persistencia garantizada
- ✅ DLQ integrado
- ✅ Económico (~$0.50/mes)

---

## ✅ Antes de empezar

### Prerequisitos

- [ ] AWS CLI instalado (`aws --version`)
- [ ] Credenciales AWS configuradas (`aws sts get-caller-identity`)
- [ ] Permisos para crear recursos SQS e IAM
- [ ] Backup de configuración actual
- [ ] Ventana de mantenimiento programada

### Impacto

- ⏱️ **Tiempo estimado:** 1-2 horas
- 🚨 **Downtime:** ~15 minutos durante el redespliegue
- 🔄 **Reversibilidad:** Sí (rollback disponible)

---

## 🛠️ Pasos de Migración

### Paso 1: Configurar AWS SQS (15 min)

#### 1.1 Crear colas SQS

```bash
cd deployment/sqs-setup

# Dar permisos de ejecución
chmod +x setup-sqs.sh

# Crear colas en AWS
./setup-sqs.sh us-east-1
```

**Output esperado:**
```
✅ Colas SQS creadas exitosamente
  Cola Principal:   anb-video-processing-queue
  Dead Letter Queue: anb-video-processing-dlq
📄 Archivo de configuración: sqs-config.env
```

#### 1.2 Configurar permisos IAM

```bash
chmod +x setup-iam.sh
./setup-iam.sh
```

**Output esperado:**
```
✅ Configuración IAM completada
  Política IAM:       ANB-SQS-Access-Policy
  Role IAM:           ANB-EC2-SQS-Role
  Instance Profile:   ANB-EC2-SQS-InstanceProfile
```

#### 1.3 Adjuntar Instance Profile a instancias EC2

```bash
# Obtener IDs de instancias
AWS_REGION=us-east-1

# Backend
BACKEND_INSTANCE_ID=$(aws ec2 describe-instances \
  --region $AWS_REGION \
  --filters "Name=tag:Name,Values=anb-backend" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

# Worker
WORKER_INSTANCE_ID=$(aws ec2 describe-instances \
  --region $AWS_REGION \
  --filters "Name=tag:Name,Values=anb-worker" \
  --query 'Reservations[0].Instances[0].InstanceId' \
  --output text)

# Adjuntar Instance Profile
aws ec2 associate-iam-instance-profile \
  --region $AWS_REGION \
  --instance-id $BACKEND_INSTANCE_ID \
  --iam-instance-profile Name=ANB-EC2-SQS-InstanceProfile

aws ec2 associate-iam-instance-profile \
  --region $AWS_REGION \
  --instance-id $WORKER_INSTANCE_ID \
  --iam-instance-profile Name=ANB-EC2-SQS-InstanceProfile
```

**Verificar:**
```bash
aws ec2 describe-instances \
  --instance-ids $BACKEND_INSTANCE_ID \
  --query 'Reservations[0].Instances[0].IamInstanceProfile'

# Debe retornar:
# {
#     "Arn": "arn:aws:iam::123456789012:instance-profile/ANB-EC2-SQS-InstanceProfile",
#     "Id": "AIPAXXX..."
# }
```

---

### Paso 2: Actualizar Backend (30 min)

#### 2.1 Conectar a instancia Backend

```bash
ssh -i "your-key.pem" ubuntu@<BACKEND_PUBLIC_IP>
cd ~/anb-backend/source/deployment/backend-instance
```

#### 2.2 Actualizar código del backend

```bash
# Pull último código (con cambios de SQS)
cd ~/anb-backend
git pull origin main  # o la rama correspondiente

# O si copiaste manualmente, asegúrate de tener:
# - source/backend/requirements.txt actualizado (kombu[sqs], boto3)
# - source/backend/app/config/settings.py con variables SQS
# - source/backend/.../celery_client.py con lógica SQS
```

#### 2.3 Actualizar variables de entorno

```bash
cd ~/anb-backend/source/deployment/backend-instance

# Editar .env
nano .env
```

**Agregar al final del archivo (copiar de `sqs-config.env`):**

```bash
# ===== AWS SQS Configuration =====
USE_SQS=true
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/anb-video-processing-queue
SQS_DLQ_URL=https://sqs.us-east-1.amazonaws.com/123456789012/anb-video-processing-dlq
```

**Guardar:** `Ctrl+O`, `Enter`, `Ctrl+X`

#### 2.4 Usar docker-compose para SQS

```bash
# Opción A: Usar el docker-compose específico para SQS
cp docker-compose.yml docker-compose.redis.yml.backup
cp docker-compose.sqs.yml docker-compose.yml

# Opción B: Comentar Redis en docker-compose.yml existente
# (El servicio redis ya no será necesario)
```

#### 2.5 Redesplegar Backend

```bash
# Detener servicios actuales
docker-compose down

# Reconstruir con nuevas dependencias
docker-compose build --no-cache

# Levantar servicios (sin Redis)
docker-compose up -d

# Ver logs
docker-compose logs -f
```

**Verificar logs - deberías ver:**
```
🚀 Configurando Celery con AWS SQS como broker
✅ Backend iniciado correctamente
```

**Verificar que NO hay Redis:**
```bash
docker ps

# Deberías ver:
# anb-nginx
# anb-backend
# (NO anb-redis)
```

#### 2.6 Verificar permisos SQS desde Backend

```bash
# Entrar al contenedor del backend
docker exec -it anb-backend bash

# Verificar credenciales (debe usar IAM Role)
aws sts get-caller-identity

# Listar colas (debe funcionar)
aws sqs list-queues

# Salir
exit
```

---

### Paso 3: Actualizar Worker (30 min)

#### 3.1 Conectar a instancia Worker

```bash
ssh -i "your-key.pem" ubuntu@<WORKER_PUBLIC_IP>
cd ~/anb-worker/source/deployment/worker-instance
```

#### 3.2 Actualizar código del worker

```bash
# Pull último código
cd ~/anb-worker
git pull origin main

# O verificar que tienes:
# - source/worker/requirements.txt actualizado (kombu[sqs], boto3)
# - source/worker/config.py con variables SQS
# - source/worker/celery_app.py con lógica SQS
```

#### 3.3 Actualizar variables de entorno

```bash
cd ~/anb-worker/source/deployment/worker-instance

# Editar .env
nano .env
```

**Agregar (MISMAS URLs que en Backend):**

```bash
# ===== AWS SQS Configuration =====
USE_SQS=true
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/anb-video-processing-queue
SQS_DLQ_URL=https://sqs.us-east-1.amazonaws.com/123456789012/anb-video-processing-dlq
```

**Guardar:** `Ctrl+O`, `Enter`, `Ctrl+X`

#### 3.4 Redesplegar Worker

```bash
# Detener worker actual
docker-compose down

# Reconstruir con nuevas dependencias
docker-compose build --no-cache

# Levantar worker
docker-compose up -d

# Ver logs
docker-compose logs -f worker
```

**Verificar logs - deberías ver:**
```
🚀 Configurando Worker con AWS SQS como broker
📍 Broker: AWS SQS
✅ Worker ANB Rising Stars iniciado correctamente
[INFO] Connected to AWS SQS
[INFO] Consuming from queue: video_processing
```

#### 3.5 Verificar permisos SQS desde Worker

```bash
# Entrar al contenedor del worker
docker exec -it anb-worker bash

# Verificar credenciales
aws sts get-caller-identity

# Listar colas
aws sqs list-queues

# Salir
exit
```

---

## ✅ Verificación

### 1. Verificar Colas en AWS Console

```
AWS Console > SQS > Queues
→ anb-video-processing-queue (Messages Available: 0)
→ anb-video-processing-dlq (Messages Available: 0)
```

### 2. Test End-to-End

#### 2.1 Login y obtener token

```bash
# Desde tu máquina local
curl -X POST http://<BACKEND_PUBLIC_IP>/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@test.com&password=Test123456"

# Guardar el access_token
TOKEN="eyJ..."
```

#### 2.2 Subir video de prueba

```bash
curl -X POST http://<BACKEND_PUBLIC_IP>/api/videos/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_video.mp4"

# Guardar el video_id del response
```

#### 2.3 Monitorear procesamiento

**En AWS Console:**
```
AWS Console > SQS > anb-video-processing-queue
→ Send and receive messages
→ Poll for messages

# Deberías ver el mensaje (o Messages in Flight: 1 si ya está procesando)
```

**En Worker logs:**
```bash
ssh -i "your-key.pem" ubuntu@<WORKER_PUBLIC_IP>
docker-compose logs -f worker | grep process_video

# Deberías ver:
# [INFO] Received task: process_video[video_id]
# [INFO] Processing video...
# [INFO] Task completed successfully
```

#### 2.4 Verificar video procesado

```bash
curl -X GET http://<BACKEND_PUBLIC_IP>/api/videos \
  -H "Authorization: Bearer $TOKEN"

# Verificar que status sea "processed"
```

### 3. Monitoreo Continuo (Primer día)

```bash
# Ver mensajes en la cola cada minuto
watch -n 60 'aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/.../anb-video-processing-queue \
  --attribute-names ApproximateNumberOfMessages,ApproximateNumberOfMessagesNotVisible'

# Verificar que no haya mensajes en DLQ
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/.../anb-video-processing-dlq \
  --attribute-names ApproximateNumberOfMessages

# Debe retornar: "ApproximateNumberOfMessages": "0"
```

---

## 🔄 Rollback (Si algo sale mal)

### Rollback Rápido con Feature Flag

Si los servicios están corriendo pero hay problemas:

#### Backend:

```bash
ssh -i "your-key.pem" ubuntu@<BACKEND_PUBLIC_IP>
cd ~/anb-backend/source/deployment/backend-instance

# Cambiar USE_SQS a false
nano .env
# USE_SQS=false

# Levantar Redis nuevamente
nano docker-compose.yml
# Descomentar servicio redis

docker-compose up -d redis
docker-compose restart backend

# Verificar logs
docker-compose logs -f backend
```

#### Worker:

```bash
ssh -i "your-key.pem" ubuntu@<WORKER_PUBLIC_IP>
cd ~/anb-worker/source/deployment/worker-instance

# Cambiar USE_SQS a false
nano .env
# USE_SQS=false
# REDIS_URL=redis://BACKEND_PRIVATE_IP:6379/0

docker-compose restart worker

# Verificar logs
docker-compose logs -f worker
```

### Rollback Completo (Eliminar SQS)

Si decides abandonar la migración completamente:

```bash
cd deployment/sqs-setup

# Eliminar recursos de AWS
chmod +x cleanup-sqs.sh
./cleanup-sqs.sh --confirm

# Revertir cambios en código
git checkout main -- source/backend/requirements.txt
git checkout main -- source/worker/requirements.txt
git checkout main -- source/backend/app/config/settings.py
git checkout main -- source/worker/config.py
# ... etc

# Redesplegar con Redis
# Seguir instrucciones originales de deployment
```

---

## 📊 Checklist de Migración

### Pre-migración
- [ ] Backup de .env del backend
- [ ] Backup de .env del worker
- [ ] Backup de docker-compose.yml
- [ ] Ventana de mantenimiento programada
- [ ] Usuarios notificados

### Migración
- [ ] AWS SQS creado (`./setup-sqs.sh`)
- [ ] IAM configurado (`./setup-iam.sh`)
- [ ] Instance Profile adjunto a Backend EC2
- [ ] Instance Profile adjunto a Worker EC2
- [ ] Backend actualizado y redesplegado
- [ ] Worker actualizado y redesplegado
- [ ] Redis removido del backend

### Post-migración
- [ ] Test end-to-end exitoso
- [ ] Logs sin errores (24h)
- [ ] Métricas SQS normales
- [ ] Sin mensajes en DLQ
- [ ] Documentación actualizada
- [ ] Equipo notificado

---

## 🐛 Troubleshooting

### Error: "Access Denied to SQS"

**Causa:** Instance Profile no adjunto o permisos incorrectos

**Solución:**
```bash
# Verificar Instance Profile
aws ec2 describe-instances \
  --instance-ids i-XXXXXXXXX \
  --query 'Reservations[0].Instances[0].IamInstanceProfile'

# Si no hay, adjuntar
aws ec2 associate-iam-instance-profile \
  --instance-id i-XXXXXXXXX \
  --iam-instance-profile Name=ANB-EC2-SQS-InstanceProfile

# Reiniciar contenedores
docker-compose restart
```

---

### Error: "Queue does not exist"

**Causa:** SQS_QUEUE_URL incorrecto en .env

**Solución:**
```bash
# Verificar URL
cat .env | grep SQS_QUEUE_URL

# Obtener URL correcta
aws sqs list-queues | grep anb-video-processing-queue

# Actualizar .env con URL correcta
nano .env
docker-compose restart
```

---

### Worker no consume mensajes

**Causa:** Worker no puede conectar a SQS o configuración incorrecta

**Solución:**
```bash
# Ver logs detallados
docker-compose logs -f worker

# Verificar configuración
docker exec -it anb-worker python -c "
from config import config
print('USE_SQS:', config.USE_SQS)
print('SQS_QUEUE_URL:', config.SQS_QUEUE_URL)
"

# Verificar conectividad
docker exec -it anb-worker aws sqs list-queues

# Reiniciar worker
docker-compose restart worker
```

---

### Mensajes van a DLQ

**Causa:** Errores en el procesamiento o timeouts

**Solución:**
```bash
# Ver mensajes en DLQ
aws sqs receive-message \
  --queue-url https://sqs.us-east-1.amazonaws.com/.../anb-video-processing-dlq \
  --max-number-of-messages 10

# Analizar error en el body del mensaje
# Corregir issue en el código
# Mover mensajes de vuelta (redrive)

# AWS Console > SQS > anb-video-processing-dlq > Start DLQ redrive
```

---

## 📚 Recursos Adicionales

- [README de sqs-setup/](./sqs-setup/README.md) - Documentación detallada de SQS
- [AWS SQS Documentation](https://docs.aws.amazon.com/sqs/)
- [Celery with SQS](https://docs.celeryproject.org/en/stable/userguide/configuration.html#broker-settings)

---

## 🎉 ¡Migración Completada!

Una vez que todo esté funcionando:

1. Monitorea durante 48 horas
2. Elimina los backups de Redis si todo está bien
3. Actualiza la documentación del equipo
4. Celebra 🎊 - Ahora tienes una arquitectura cloud-native y auto-escalable!

---

**Última actualización:** Noviembre 2025
**Versión:** 1.0
