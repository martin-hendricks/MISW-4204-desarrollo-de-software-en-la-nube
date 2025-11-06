# AWS SQS Setup - ANB Rising Stars

Guía para configurar AWS SQS como message broker para el procesamiento de videos.

> **Nota:** El código ya está migrado a SQS. Esta guía te ayuda a crear y configurar las colas en AWS.

---

## Índice

- [¿Por qué SQS?](#por-qué-sqs)
- [Configuración en AWS Console](#configuración-en-aws-console)
- [Configuración con Scripts](#configuración-con-scripts)
- [Variables de Entorno](#variables-de-entorno)
- [Verificación](#verificación)
- [Troubleshooting](#troubleshooting)

---

## ¿Por qué SQS?

### Problema con Redis

Con Redis en el backend, al escalar horizontalmente se crean múltiples instancias de Redis descoordinadas:

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
Backend 2 ─┼─→ AWS SQS (managed) ─→ Worker 1
Backend 3 ─┘                      ├─→ Worker 2
                                  └─→ Worker 3
```

**Beneficios:**
- ✅ Autoscaling nativo (backends y workers)
- ✅ Balanceo automático de carga entre workers
- ✅ Alta disponibilidad (99.9% SLA)
- ✅ Sin mantenimiento (managed service)
- ✅ Dead Letter Queue integrado
- ✅ Económico (~$0/mes en free tier)

---

## Configuración en AWS Console

### Paso 1: Crear Dead Letter Queue (DLQ)

1. Ve a **AWS Console > Amazon SQS**
2. Click en **"Create queue"**
3. Configuración:
   ```
   Type: Standard
   Name: anb-video-processing-dlq

   Configuration:
     Visibility timeout: 3600 segundos (1 hora)
     Message retention period: 1209600 segundos (14 días)
     Receive message wait time: 0 segundos

   Access Policy: Básico
     Send messages: Solo el propietario de la cola
     Receive messages: Solo el propietario de la cola

   Dead-letter queue: Deshabilitada
   ```
4. Click **"Create queue"**
5. **Guarda la URL** de la DLQ (la necesitarás):
   ```
   https://sqs.us-east-1.amazonaws.com/TU_ACCOUNT_ID/anb-video-processing-dlq
   ```

---

### Paso 2: Crear Cola Principal

1. Click en **"Create queue"**
2. Configuración:
   ```
   Type: Standard
   Name: anb-video-processing-queue

   Configuration:
     Visibility timeout: 3600 segundos (1 hora)
     Message retention period: 345600 segundos (4 días)
     Receive message wait time: 20 segundos ⚠️ IMPORTANTE (long polling)

   Access Policy: Básico
     Send messages: Solo el propietario de la cola
     Receive messages: Solo el propietario de la cola

   Dead-letter queue: ✅ Habilitada
     Choose queue: anb-video-processing-dlq
     Maximum receives: 3
   ```
3. Click **"Create queue"**
4. **Guarda la URL** de la cola principal:
   ```
   https://sqs.us-east-1.amazonaws.com/TU_ACCOUNT_ID/anb-video-processing-queue
   ```

---

### Paso 3: Configurar Permisos IAM

#### Opción A: AWS Academy (Usar LabRole existente)

En AWS Academy no puedes crear roles nuevos. Usa el `LabRole` existente:

1. Ve a **EC2 > Instances**
2. Selecciona tu instancia Backend
3. **Actions > Security > Modify IAM role**
4. Selecciona **LabRole**
5. Click **Update IAM role**
6. Repite para la instancia Worker

#### Opción B: AWS Cuenta Normal (Crear IAM Role)

Si tienes una cuenta AWS normal (no Academy):

```bash
cd deployment/sqs-setup
chmod +x setup-iam.sh
./setup-iam.sh
```

Luego adjunta el Instance Profile a tus instancias:

```bash
aws ec2 associate-iam-instance-profile \
  --instance-id i-BACKEND_ID \
  --iam-instance-profile Name=ANB-EC2-SQS-InstanceProfile

aws ec2 associate-iam-instance-profile \
  --instance-id i-WORKER_ID \
  --iam-instance-profile Name=ANB-EC2-SQS-InstanceProfile
```

---

## Configuración con Scripts

Si prefieres usar scripts (requiere AWS CLI configurado):

```bash
cd deployment/sqs-setup

# 1. Crear colas
chmod +x setup-sqs.sh
./setup-sqs.sh us-east-1

# 2. Configurar IAM (solo si no usas AWS Academy)
chmod +x setup-iam.sh
./setup-iam.sh
```

---

## Variables de Entorno

Una vez creadas las colas, configura las variables de entorno:

### Backend: `deployment/backend-instance/.env`

Agregar estas líneas al final del archivo:

```bash
# ============================================
# AWS SQS Configuration
# ============================================
USE_SQS=true
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/TU_ACCOUNT_ID/anb-video-processing-queue
SQS_DLQ_URL=https://sqs.us-east-1.amazonaws.com/TU_ACCOUNT_ID/anb-video-processing-dlq

# Solo para AWS Academy (credenciales temporales):
AWS_ACCESS_KEY_ID=ASIAXXX...
AWS_SECRET_ACCESS_KEY=xxx...
AWS_SESSION_TOKEN=xxx...
```

### Worker: `deployment/worker-instance/.env`

Agregar las **MISMAS** líneas:

```bash
# ============================================
# AWS SQS Configuration
# ============================================
USE_SQS=true
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/TU_ACCOUNT_ID/anb-video-processing-queue
SQS_DLQ_URL=https://sqs.us-east-1.amazonaws.com/TU_ACCOUNT_ID/anb-video-processing-dlq

# Solo para AWS Academy (credenciales temporales):
AWS_ACCESS_KEY_ID=ASIAXXX...
AWS_SECRET_ACCESS_KEY=xxx...
AWS_SESSION_TOKEN=xxx...
```

### Notas sobre credenciales:

**AWS Academy:**
- Las credenciales (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`) son necesarias
- Se renuevan cada ~4 horas. Debes actualizarlas periódicamente desde "AWS Details"

**AWS Cuenta Normal:**
- NO necesitas credenciales en `.env` si usas IAM Role/Instance Profile
- El IAM Role se encarga automáticamente de las credenciales

---

## Redesplegar Servicios

Una vez agregadas las variables al `.env`, debes **reconstruir y redesplegar** los contenedores:

### Backend

```bash
# Conectar a instancia Backend
ssh -i "your-key.pem" ubuntu@BACKEND_IP

# Ir al directorio de deployment
cd ~/anb-backend/deployment/backend-instance

# Detener servicios actuales (si están corriendo)
docker-compose down

# Reconstruir imágenes con nuevas dependencias (kombu[sqs], boto3)
docker-compose -f docker-compose.sqs.yml build --no-cache

# Levantar servicios con SQS (sin Redis)
docker-compose -f docker-compose.sqs.yml up -d

# Verificar logs
docker-compose -f docker-compose.sqs.yml logs -f backend

# Deberías ver:
# 🚀 Configurando Celery con AWS SQS como broker
```

### Worker

```bash
# Conectar a instancia Worker
ssh -i "your-key.pem" ubuntu@WORKER_IP

# Ir al directorio de deployment
cd ~/anb-worker/deployment/worker-instance

# Detener worker actual
docker-compose down

# Reconstruir imagen con nuevas dependencias
docker-compose build --no-cache

# Levantar worker
docker-compose up -d

# Verificar logs
docker-compose logs -f worker

# Deberías ver:
# 🚀 Configurando Worker con AWS SQS como broker
# 📍 Broker: AWS SQS
# ✅ Worker ANB Rising Stars iniciado correctamente
```

### ¿Por qué usar `docker-compose.sqs.yml`?

- **`docker-compose.yml`**: Incluye Redis (para desarrollo local)
- **`docker-compose.sqs.yml`**: Sin Redis, solo SQS (para producción)

El archivo SQS es más limpio y no levanta servicios innecesarios.

### ¿Por qué `build --no-cache`?

- Las nuevas dependencias (`kombu[sqs]`, `boto3`) deben instalarse
- El flag `--no-cache` garantiza que se instalen las versiones correctas
- Sin rebuild, los contenedores seguirán usando las dependencias antiguas

### Alternativa: Solo reiniciar si ya habías construido antes

Si ya habías construido las imágenes con las dependencias correctas:

```bash
# Solo reiniciar para cargar nuevas variables .env
docker-compose -f docker-compose.sqs.yml restart
```

---

## Verificación

### 1. Verificar colas en AWS Console

```
AWS Console > SQS > Queues

✅ anb-video-processing-queue (Available)
✅ anb-video-processing-dlq (Available)
```

### 2. Verificar permisos desde EC2

Conéctate a tu instancia Backend o Worker:

```bash
# Verificar identidad AWS
aws sts get-caller-identity

# Listar colas (debe funcionar sin errores)
aws sqs list-queues

# Enviar mensaje de prueba
aws sqs send-message \
  --queue-url "https://sqs.us-east-1.amazonaws.com/TU_ACCOUNT_ID/anb-video-processing-queue" \
  --message-body "Test message"

# Recibir mensaje
aws sqs receive-message \
  --queue-url "https://sqs.us-east-1.amazonaws.com/TU_ACCOUNT_ID/anb-video-processing-queue"
```

### 3. Test End-to-End

```bash
# 1. Login
curl -X POST http://BACKEND_IP/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@test.com&password=Test123456"

# Guardar token
TOKEN="..."

# 2. Subir video
curl -X POST http://BACKEND_IP/api/videos/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_video.mp4"

# 3. Monitorear en AWS Console
# AWS Console > SQS > anb-video-processing-queue
# Verás "Messages in Flight: 1" mientras se procesa

# 4. Verificar video procesado
curl -X GET http://BACKEND_IP/api/videos \
  -H "Authorization: Bearer $TOKEN"
```

---

## Troubleshooting

### Error: "Access Denied to SQS"

**Síntoma:**
```
boto.exception.SQSError: SQSError: 403 Forbidden
```

**Solución para AWS Academy:**
```bash
# 1. Verifica que las credenciales estén en .env
cat .env | grep AWS_ACCESS_KEY_ID

# 2. Renueva credenciales desde AWS Academy > AWS Details
# 3. Actualiza .env con nuevas credenciales
# 4. Reinicia servicios
docker-compose restart
```

**Solución para AWS Normal:**
```bash
# Verificar IAM Role adjunto
aws ec2 describe-instances \
  --instance-ids i-XXXXX \
  --query 'Reservations[0].Instances[0].IamInstanceProfile'

# Si no hay, adjuntar
aws ec2 associate-iam-instance-profile \
  --instance-id i-XXXXX \
  --iam-instance-profile Name=ANB-EC2-SQS-InstanceProfile
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

# Listar colas disponibles
aws sqs list-queues

# Actualizar .env con URL correcta
nano .env
docker-compose restart
```

---

### Worker no consume mensajes

**Síntoma:**
```
AWS Console > Messages Available: 5
Worker logs: No activity
```

**Solución:**
```bash
# 1. Ver logs del worker
docker-compose logs -f worker

# 2. Verificar configuración
docker exec -it anb-worker python -c "
from config import config
print('USE_SQS:', config.USE_SQS)
print('SQS_QUEUE_URL:', config.SQS_QUEUE_URL)
"

# 3. Verificar conectividad
docker exec -it anb-worker aws sqs list-queues

# 4. Reiniciar worker
docker-compose restart worker
```

---

### Mensajes van a DLQ

**Síntoma:**
```
AWS Console > anb-video-processing-dlq > Messages Available: 3
```

**Solución:**
```bash
# Ver mensajes en DLQ para identificar el error
aws sqs receive-message \
  --queue-url "https://sqs.us-east-1.amazonaws.com/TU_ACCOUNT_ID/anb-video-processing-dlq" \
  --max-number-of-messages 10

# Analizar el error en el body del mensaje
# Corregir el issue
# Mover mensajes de vuelta a cola principal:
# AWS Console > SQS > anb-video-processing-dlq > Start DLQ redrive
```

---

## Balanceo de Carga entre Workers

SQS balancea automáticamente los mensajes entre múltiples workers:

```
Cola SQS (10 mensajes)
         ↓
    ┌────┴────┬────────┐
    ↓         ↓        ↓
Worker 1  Worker 2  Worker 3
Msg 1,4   Msg 2,5   Msg 3,6
```

**Para escalar workers:**
1. Lanza más instancias EC2 worker con la misma configuración
2. Todos los workers consumen de la misma cola
3. SQS garantiza que cada mensaje se procesa solo una vez

**Configuración recomendada en workers:**
- `worker_prefetch_multiplier=1` (ya configurado en el código)
- Solo 1 mensaje por worker a la vez
- Distribuye la carga equitativamente

---

## Recursos Adicionales

- [AWS SQS Documentation](https://docs.aws.amazon.com/sqs/)
- [Celery with SQS](https://docs.celeryproject.org/en/stable/userguide/configuration.html#broker-settings)
- [AWS Academy Learner Lab Guide](https://awsacademy.instructure.com/)

---

## Checklist de Setup

### Fase 1: Crear Colas en AWS
- [ ] Cola DLQ creada: `anb-video-processing-dlq`
- [ ] Cola principal creada: `anb-video-processing-queue`
- [ ] DLQ vinculada a cola principal (max receives: 3)
- [ ] Long polling configurado (Receive wait time: 20s)

### Fase 2: Configurar Permisos
- [ ] IAM Role configurado (o usando LabRole en AWS Academy)
- [ ] IAM Role/LabRole adjunto a instancia Backend
- [ ] IAM Role/LabRole adjunto a instancia Worker
- [ ] (Si AWS Academy) Credenciales temporales obtenidas

### Fase 3: Configurar Variables de Entorno
- [ ] Variables en `backend-instance/.env` actualizadas
  - [ ] `USE_SQS=true`
  - [ ] `SQS_QUEUE_URL` con URL correcta
  - [ ] `SQS_DLQ_URL` con URL correcta
  - [ ] (Si AWS Academy) Credenciales AWS agregadas
- [ ] Variables en `worker-instance/.env` actualizadas (mismos valores)

### Fase 4: Redesplegar Servicios
- [ ] Backend: `docker-compose -f docker-compose.sqs.yml build --no-cache && docker-compose -f docker-compose.sqs.yml up -d`
- [ ] Worker: `docker-compose build --no-cache && docker-compose up -d`
- [ ] Logs del backend muestran: "Configurando Celery con AWS SQS"
- [ ] Logs del worker muestran: "Configurando Worker con AWS SQS"
- [ ] Verificar que Redis NO está corriendo en el backend

### Fase 5: Verificación
- [ ] Test end-to-end exitoso (subir video y verificar procesamiento)
- [ ] Mensajes aparecen en cola SQS al subir videos
- [ ] Worker consume y procesa mensajes correctamente
- [ ] No hay mensajes en DLQ
- [ ] Monitoreo de colas en AWS Console funcionando

---

**Última actualización:** Noviembre 2025
**Versión:** 2.0
