# Performance Testing Instance - Deployment (AWS SQS + S3)

Esta carpeta contiene los archivos necesarios para desplegar una instancia de **Performance Testing** en AWS EC2 que ejecuta pruebas de carga contra tu infraestructura de procesamiento de videos usando **AWS SQS** y **S3**.

## 🆕 Actualización: Migración a AWS SQS y S3

Esta configuración ahora usa:
- **AWS SQS** como broker de mensajes (en lugar de Redis con SSH tunnel)
- **AWS S3** para almacenamiento de videos (en lugar de volúmenes locales/NFS)

### ¿Por qué migrar a SQS y S3?

✅ **Escalabilidad**: SQS y S3 escalan automáticamente sin configuración adicional
✅ **Confiabilidad**: Servicios administrados por AWS con alta disponibilidad
✅ **Simplicidad**: No requiere túneles SSH ni sincronización de archivos
✅ **Costo-efectivo**: Pago por uso, sin infraestructura permanente
✅ **AWS Academy compatible**: Funciona perfectamente con credenciales temporales

## 📁 Archivos en esta carpeta

- **[DEPLOY.md](./DEPLOY.md)** - Guía completa paso a paso para el deployment
- **docker-compose.yml** - Configuración de Docker Compose (con soporte SQS/S3)
- **prometheus.yml** - Configuración de Prometheus para scraping de métricas
- **setup-ssh-tunnel.sh** - Script de configuración (ahora configura Prometheus)
- **.env.example** - Plantilla de variables de entorno (actualizada para SQS/S3)

## 🚀 Inicio Rápido

### 1. Lee la guía completa de deployment

➡️ **[DEPLOY.md](./DEPLOY.md)**

Esta guía contiene TODOS los pasos necesarios, incluyendo:

- Creación de la instancia EC2
- Configuración de Security Groups
- Instalación de Docker
- Configuración de AWS SQS y S3
- Deployment de servicios (Prometheus, Grafana, JMeter, Producer)
- Ejecución de pruebas de carga
- Troubleshooting

### 2. Requisitos previos

Antes de comenzar, asegúrate de tener:

- [ ] Una cuenta de AWS Academy o AWS con permisos para:
  - Crear instancias EC2
  - Crear colas SQS
  - Crear buckets S3
- [ ] Credenciales de AWS (Access Key, Secret Key, Session Token)
- [ ] IP pública del backend (para JMeter y métricas de Prometheus)
- [ ] Worker configurado para usar SQS y S3

### 3. Configuración AWS necesaria

Necesitarás configurar:

```bash
# AWS SQS
SQS_QUEUE_URL: https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/anb-video-processing-queue
SQS_DLQ_URL: https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/anb-video-processing-dlq

# AWS S3
S3_BUCKET_NAME: your-bucket-name

# AWS Credentials (desde AWS Academy)
AWS_ACCESS_KEY_ID: ASIA...
AWS_SECRET_ACCESS_KEY: ...
AWS_SESSION_TOKEN: ...

# Backend/Worker IPs (para Prometheus)
PROMETHEUS_BACKEND_TARGET: 3.XXX.XXX.XXX:8000
PROMETHEUS_WORKER_TARGET: 3.YYY.YYY.YYY:8001
```

## 🎯 ¿Qué hace esta instancia?

La instancia de Performance Testing ejecuta:

1. **Producer** (Python + Celery Client)
   - Inyecta tareas en AWS SQS
   - Sube videos de prueba a S3
   - Simula carga de procesamiento de videos
   - Soporta monitoreo de progreso con CloudWatch

2. **JMeter**
   - Ejecuta pruebas de carga HTTP contra la API del backend
   - Soporta smoke tests, ramp-up tests y sustained tests
   - Genera reportes de rendimiento

3. **Prometheus**
   - Recolecta métricas del backend y worker remotos vía HTTP
   - Almacena datos de rendimiento
   - Expone métricas en puerto 9090

4. **Grafana**
   - Visualiza métricas en dashboards interactivos
   - Accesible en puerto 3000
   - Dashboards pre-configurados para API y Worker

## 📊 Arquitectura (AWS SQS + S3)

```
┌─────────────────────────────────────────────────────────┐
│ TU CUENTA AWS                                           │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ EC2: Performance Testing                          │ │
│  │                                                   │ │
│  │  • Producer (envía mensajes a SQS)               │ │
│  │  • JMeter (pruebas HTTP)                         │ │
│  │  • Prometheus (recolecta métricas)               │ │
│  │  • Grafana (visualización)                       │ │
│  └───────────────────────────────────────────────────┘ │
│            │                   │                        │
│            │                   │                        │
│            ▼                   ▼                        │
│  ┌──────────────────┐  ┌─────────────────┐            │
│  │  AWS SQS         │  │  AWS S3         │            │
│  │  • Main Queue    │  │  • Videos       │            │
│  │  • DLQ           │  │    (original/)  │            │
│  └──────────────────┘  └─────────────────┘            │
│            │                   │                        │
│            │                   │                        │
└────────────┼───────────────────┼────────────────────────┘
             │                   │
             ▼                   ▼
┌────────────────────────────────────────────────────────┐
│ TU INFRAESTRUCTURA DE BACKEND/WORKER                   │
│                                                        │
│  ┌──────────────────────────────┐                     │
│  │ EC2: Backend                 │                     │
│  │  • API (HTTP) ◄──── JMeter   │                     │
│  │  • Métricas :8000            │                     │
│  └──────────────────────────────┘                     │
│                                                        │
│  ┌──────────────────────────────┐                     │
│  │ EC2: Worker(s)               │                     │
│  │  • Lee mensajes de SQS       │                     │
│  │  • Procesa videos de S3      │                     │
│  │  • Guarda resultados en S3   │                     │
│  │  • Métricas :8001            │                     │
│  └──────────────────────────────┘                     │
└────────────────────────────────────────────────────────┘
```

## 🔧 Configuración Rápida (AWS SQS + S3)

### 1. Crear recursos AWS necesarios

```bash
# Crear colas SQS (desde tu máquina local o EC2)
cd source/deployment/sqs-setup
./setup-sqs.sh us-east-1

# Anota las URLs de las colas que genera el script
# SQS_QUEUE_URL: https://sqs.us-east-1.amazonaws.com/...
# SQS_DLQ_URL: https://sqs.us-east-1.amazonaws.com/...
```

### 2. Clonar el repositorio en la instancia EC2

```bash
# Desde la instancia de performance
git clone https://github.com/TU_USUARIO/MISW-4204-desarrollo-de-software-en-la-nube.git
cd MISW-4204-desarrollo-de-software-en-la-nube/source/deployment/performance-instance
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
nano .env
```

Completa los valores principales:

```bash
# Modo de operación (usa SQS y S3)
USE_SQS=true
USE_S3=true

# AWS SQS (URLs obtenidas del script setup-sqs.sh)
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/anb-video-processing-queue
SQS_DLQ_URL=https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/anb-video-processing-dlq

# AWS S3 (mismo bucket que usa el worker)
S3_BUCKET_NAME=your-bucket-name

# Credenciales AWS (desde AWS Academy > AWS Details > AWS CLI > Show)
AWS_ACCESS_KEY_ID=ASIA...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...

# API del backend (para JMeter)
API_BASE_URL=http://3.XXX.XXX.XXX

# Prometheus targets
PROMETHEUS_BACKEND_TARGET=3.XXX.XXX.XXX:8000
PROMETHEUS_WORKER_TARGET=3.YYY.YYY.YYY:8001
```

### 4. Configurar Prometheus

```bash
# El script setup-ssh-tunnel.sh ahora configura prometheus.yml automáticamente
chmod +x setup-ssh-tunnel.sh
./setup-ssh-tunnel.sh
```

**Nota**: Aunque el script se llama `setup-ssh-tunnel.sh`, ahora también configura `prometheus.yml` con las IPs del `.env`. El túnel SSH solo se crea si `USE_SQS=false`.

### 5. Levantar servicios

```bash
docker-compose up -d
```

### 6. Verificar

```bash
# Ver servicios
docker ps

# Verificar conexión a SQS
docker exec producer python -c "import boto3; print(boto3.client('sqs', region_name='us-east-1').list_queues())"

# Verificar acceso a S3
docker exec producer python -c "import boto3; print(boto3.client('s3').list_buckets())"

# Acceder a Grafana
http://<PERFORMANCE_IP>:3000
Usuario: admin / Password: admin
```

## 📝 Ejecución de Pruebas

### Pruebas de API con JMeter

```bash
# Smoke test
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"

# Ramp-up test (100 usuarios)
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_100_users_results.jtl -Jusers=100"

# Sustained test (116 usuarios)
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/sustained_test.jmx -l /scripts/sustained_116_users_results.jtl -Jusers=116"
```

### Pruebas de Worker con Producer (AWS SQS + S3)

```bash
# Prueba básica (20 videos) - Los videos se suben a S3 y tareas a SQS
docker exec producer python producer.py --num-videos 20 --no-wait

# Prueba de saturación (100 videos)
docker exec producer python producer.py --num-videos 100 --no-wait

# Prueba con videos grandes (100MB)
docker exec producer python producer.py --num-videos 10 --video-file ./assets/dummy_file_100mb.mp4 --no-wait

# Prueba con modo debug (ver detalles de subida a S3 y SQS)
docker exec producer python producer.py --num-videos 5 --no-wait --debug
```

### Monitorear progreso de pruebas

```bash
# Ver mensajes en la cola SQS
aws sqs get-queue-attributes \
  --queue-url <SQS_QUEUE_URL> \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible

# Ver archivos en S3
aws s3 ls s3://<S3_BUCKET_NAME>/original/

# Ver logs del producer
docker logs -f producer

# Ver métricas en Grafana
http://<PERFORMANCE_IP>:3000
```

## 🐛 Troubleshooting

Ver la sección completa de troubleshooting en [DEPLOY.md](./DEPLOY.md).

## 📚 Recursos Adicionales

- [GET_STARTED.md](../GET_STARTED.md) - Guía de inicio rápido del proyecto
- [../../performance-testing/README.md](../../performance-testing/README.md) - Documentación completa de performance testing
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Arquitectura del sistema

---

**¿Necesitas ayuda?** Consulta [DEPLOY.md](./DEPLOY.md) para la guía completa paso a paso.
