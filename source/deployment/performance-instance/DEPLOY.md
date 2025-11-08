# Guía de Despliegue - Instancia de Performance Testing (AWS SQS + S3)

## 🆕 Actualización: Migración a AWS SQS y S3

Esta guía ha sido actualizada para usar AWS SQS y S3 en lugar de Redis con SSH tunnel y almacenamiento local/NFS.

## Resumen
Esta instancia EC2 contiene:
- ✅ Producer (Python + Celery Client) - Inyecta tareas en AWS SQS y sube videos a S3
- ✅ JMeter - Pruebas de carga HTTP contra la API
- ✅ Prometheus - Recolección de métricas vía HTTP
- ✅ Grafana - Visualización de métricas (Puerto 3000)

**Modo de operación:** Esta instancia usa AWS SQS como broker de mensajes y S3 para almacenar videos de prueba. No requiere túnel SSH ni acceso directo al backend.

---

## Requisitos Previos

### 1. Instancia EC2 configurada
- ✅ Ubuntu Server 22.04 LTS
- ✅ Tipo: t2.medium o superior (mínimo 4GB RAM para JMeter)
- ✅ Docker y Docker Compose instalados
- ✅ Security Group configurado (ver abajo)

### 2. Recursos AWS configurados
- ✅ Colas SQS creadas (Main Queue y DLQ)
- ✅ Bucket S3 creado (mismo que usa el worker)
- ✅ Credenciales AWS configuradas (Access Key, Secret Key, Session Token)
- ✅ Worker configurado para leer de SQS y procesar videos de S3

### 3. Servicios backend accesibles
- ✅ Backend desplegado y funcionando
- ✅ Worker(s) desplegado(s) y escuchando en SQS
- ✅ Puerto 8000 (backend métricas) y 8001 (worker métricas) accesibles vía HTTP

---

## Security Group - Performance Testing Instance

### Inbound Rules

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | Your IP | Administración SSH |
| Custom TCP | TCP | 3000 | Your IP | Grafana - Visualización de métricas |
| Custom TCP | TCP | 9090 | Your IP | Prometheus (opcional, para debug) |

### Outbound Rules
- All traffic (default)

**IMPORTANTE:** Esta instancia necesita poder conectarse a:
- AWS SQS (puerto 443 HTTPS para enviar mensajes)
- AWS S3 (puerto 443 HTTPS para subir/descargar archivos)
- Backend API (puerto 80 HTTP para pruebas JMeter)
- Backend métricas (puerto 8000 HTTP para Prometheus)
- Worker métricas (puerto 8001 HTTP para Prometheus)

---

## ⚠️ IMPORTANTE: Configuración Previa al Despliegue

**Si ya tienes la instancia configurada**, solo necesitas:

```bash
# 1. Crear recursos AWS (colas SQS)
cd ~/MISW-4204-desarrollo-de-software-en-la-nube/source/deployment/sqs-setup
./setup-sqs.sh us-east-1

# 2. Editar .env con configuración AWS
cd ~/performance-instance
nano .env
# Configura: USE_SQS=true, USE_S3=true, SQS_QUEUE_URL, S3_BUCKET_NAME, credenciales AWS

# 3. Configurar Prometheus con las IPs
./setup-ssh-tunnel.sh  # Ahora solo configura prometheus.yml, no crea túnel SSH si USE_SQS=true

# 4. Levantar servicios
docker-compose up -d

# 5. Verificar
docker ps
docker exec producer python -c "import boto3; print('✅ AWS configurado correctamente')"
curl http://localhost:3000  # Grafana
```

**Archivos que DEBES editar antes de desplegar:**

| Archivo | Qué configurar | Valor |
|---------|----------------|-------|
| **`.env`** | `USE_SQS` | `true` (usar AWS SQS) |
| **`.env`** | `USE_S3` | `true` (usar AWS S3) |
| **`.env`** | `SQS_QUEUE_URL` | URL de la cola SQS principal (del script setup-sqs.sh) |
| **`.env`** | `SQS_DLQ_URL` | URL de la cola DLQ (del script setup-sqs.sh) |
| **`.env`** | `S3_BUCKET_NAME` | Nombre del bucket S3 (mismo que usa el worker) |
| **`.env`** | `AWS_ACCESS_KEY_ID` | Access Key de AWS Academy |
| **`.env`** | `AWS_SECRET_ACCESS_KEY` | Secret Key de AWS Academy |
| **`.env`** | `AWS_SESSION_TOKEN` | Session Token de AWS Academy |
| **`.env`** | `API_BASE_URL` | URL de la API del backend (ej: `http://3.XXX.XXX.XXX`) |
| **`.env`** | `PROMETHEUS_BACKEND_TARGET` | IP y puerto del backend para métricas (ej: `3.XXX.XXX.XXX:8000`) |
| **`.env`** | `PROMETHEUS_WORKER_TARGET` | IP y puerto del worker para métricas (ej: `3.YYY.YYY.YYY:8001`) |

**Nota:** El script `setup-ssh-tunnel.sh` configurará automáticamente `prometheus.yml` usando los valores del `.env`. Cuando `USE_SQS=true`, no se crea túnel SSH.

### 🔄 ¿Necesitas recrear contenedores después de cambiar configuración?

**SÍ, debes recrear** si cambias cualquiera de estos valores después del primer despliegue:

```bash
# Detener servicios
docker-compose down

# Editar configuración
nano .env

# Recrear túnel SSH
pkill -f 'ssh.*6379'
./setup-ssh-tunnel.sh

# Reconstruir y levantar con nueva configuración
docker-compose up -d --build
```

**NO necesitas recrear** si solo cambias:
- Credenciales de Grafana (`GF_SECURITY_ADMIN_USER`, `GF_SECURITY_ADMIN_PASSWORD`)
- Intervalo de renovación JWT (`RENEWAL_INTERVAL`)

---

## Arquitectura del Performance Testing (AWS SQS + S3)

```
┌─────────────────────────────────────────────────────────────┐
│ TU CUENTA AWS                                               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ EC2: anb-performance-testing                        │  │
│  │                                                     │  │
│  │  • Producer (envía a SQS, sube a S3)               │  │
│  │  • JMeter (HTTP Load Testing)                      │  │
│  │  • Prometheus (Metrics Collection vía HTTP)        │  │
│  │  • Grafana (Metrics Visualization)                 │  │
│  └─────────────────────────────────────────────────────┘  │
│            │                   │                            │
│            │ HTTPS             │ HTTPS                      │
│            ▼                   ▼                            │
│  ┌──────────────────┐  ┌─────────────────┐                │
│  │  AWS SQS         │  │  AWS S3         │                │
│  │  • Main Queue    │  │  • Bucket       │                │
│  │  • DLQ           │  │    original/    │                │
│  └──────────────────┘  └─────────────────┘                │
│            │                   │                            │
└────────────┼───────────────────┼────────────────────────────┘
             │ Poll              │ Download/Upload
             │ Messages          │ Videos
             ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│ TU INFRAESTRUCTURA DE BACKEND/WORKER                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ EC2: anb-backend                                    │  │
│  │                                                     │  │
│  │  • API Backend (Puerto 80) ◄─── JMeter (HTTP)      │  │
│  │  • Métricas (Puerto 8000) ◄─── Prometheus (HTTP)   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ EC2: anb-worker(s) - Auto Scaling Group             │  │
│  │                                                     │  │
│  │  • Lee mensajes de SQS                             │  │
│  │  • Descarga videos de S3                           │  │
│  │  • Procesa videos                                  │  │
│  │  • Sube resultados a S3                            │  │
│  │  • Métricas (Puerto 8001) ◄─── Prometheus (HTTP)   │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Flujo de las Pruebas (AWS SQS + S3)

1. **Producer** (tu instancia) → Sube videos a **S3** (carpeta `original/`)
2. **Producer** (tu instancia) → Envía mensajes a **SQS** con referencias a los videos
3. **Worker(s)** (tu infraestructura) → Leen mensajes de **SQS**
4. **Worker(s)** (tu infraestructura) → Descargan videos de **S3**, procesan y suben resultados
5. **Prometheus** (tu instancia) → Recolecta métricas del backend y workers vía HTTP
6. **Grafana** (tu instancia) → Visualiza las métricas en dashboards

---

## Paso 1: Crear Security Group (5 min)

**En AWS Console > EC2 > Security Groups > Create Security Group:**

```
Name: anb-performance-sg
Description: Security group for Performance Testing instance

Inbound Rules:
- SSH (22) from Your IP
- Custom TCP (3000) from Your IP [Grafana]
- Custom TCP (9090) from Your IP [Prometheus - opcional]

Outbound Rules:
- All traffic to 0.0.0.0/0
```

---

## Paso 2: Crear Instancia EC2 (10 min)

**En AWS Console > EC2 > Launch Instance:**

```
Name: anb-performance-testing
AMI: Ubuntu Server 22.04 LTS
Instance type: t2.medium (recomendado para JMeter)
Key pair: <tu-key>
Security group: anb-performance-sg
Storage: 20 GB (gp3)
```

**Anotar IPs:**
```
PERFORMANCE_PUBLIC_IP: _____________________________________________
PERFORMANCE_PRIVATE_IP: _____________________________________________
```

---

## Paso 3: Configurar AWS SQS y S3 (15 min)

### 3.1 Crear colas SQS

**Opción A: Usar el script automatizado (Recomendado)**

```bash
# Conectarte a tu instancia de performance
ssh -i "your-key.pem" ubuntu@<PERFORMANCE_PUBLIC_IP>

# Clonar el repositorio (si aún no lo has hecho)
cd ~
git clone https://github.com/TU_USUARIO/MISW-4204-desarrollo-de-software-en-la-nube.git

# Navegar al directorio de setup de SQS
cd MISW-4204-desarrollo-de-software-en-la-nube/source/deployment/sqs-setup

# Configurar credenciales de AWS (desde AWS Academy)
# Ve a AWS Details > AWS CLI > Show y copia las credenciales
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

# Ejecutar script de creación de colas
chmod +x setup-sqs.sh
./setup-sqs.sh us-east-1
```

**El script creará:**
- Cola principal: `anb-video-processing-queue`
- Cola DLQ: `anb-video-processing-dlq`

**Anota las URLs que genera el script:**
```
SQS_QUEUE_URL: https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/anb-video-processing-queue
SQS_DLQ_URL: https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/anb-video-processing-dlq
```

### 3.2 Verificar bucket S3

El bucket S3 debe ser creado previamente (el mismo que usa el worker).

```bash
# Verificar que el bucket existe
aws s3 ls s3://your-bucket-name

# Si no existe, créalo
aws s3 mb s3://your-bucket-name --region us-east-1

# Verificar carpeta original/ (se creará automáticamente si no existe)
aws s3 ls s3://your-bucket-name/original/
```

**Anota el nombre del bucket:**
```
S3_BUCKET_NAME: your-bucket-name
```

---

## Paso 4: Instalar Docker y Dependencias (10 min)

**Conectarse a tu instancia de performance:**

```bash
ssh -i "your-key.pem" ubuntu@<PERFORMANCE_PUBLIC_IP>
```

**Instalar Docker y herramientas:**

```bash
# Actualizar paquetes
sudo apt update

# Instalar Docker y Docker Compose
sudo apt install -y docker.io docker-compose

# Agregar usuario al grupo docker
sudo usermod -aG docker ubuntu

# Instalar herramientas adicionales
sudo apt install -y git curl wget

# Cerrar sesión y volver a entrar para aplicar permisos
exit
ssh -i "your-key.pem" ubuntu@<PERFORMANCE_PUBLIC_IP>

# Verificar instalación
docker --version
docker-compose --version
```

---

## Paso 5: Copiar Archivos del Proyecto (15 min)

### 5.1 Clonar el repositorio o copiar archivos

**Opción 1: Clonar desde Git (Recomendado)**

```bash
# Conectado a tu instancia de performance
cd ~
git clone https://github.com/TU_USUARIO/MISW-4204-desarrollo-de-software-en-la-nube.git
cd MISW-4204-desarrollo-de-software-en-la-nube/source/deployment/performance-instance
```

**Opción 2: Copiar desde tu máquina local**

```bash
# Desde tu máquina local
scp -i "your-key.pem" -r ./source/deployment/performance-instance ubuntu@<PERFORMANCE_PUBLIC_IP>:~/performance-instance
scp -i "your-key.pem" -r ./source/performance-testing ubuntu@<PERFORMANCE_PUBLIC_IP>:~/performance-testing

# Conectarte a la instancia
ssh -i "your-key.pem" ubuntu@<PERFORMANCE_PUBLIC_IP>
cd ~/performance-instance
```

---

## Paso 6: Configurar Variables de Entorno (10 min)

### 6.1 Crear archivo .env

```bash
# Desde tu instancia de performance
cd ~/performance-instance
cp .env.example .env
nano .env
```

**Configuración del .env para AWS SQS + S3:**

```bash
# ==============================================================================
# MODO DE OPERACIÓN (AWS SQS + S3)
# ==============================================================================

USE_SQS=true
USE_S3=true

# ==============================================================================
# AWS SQS CONFIGURATION
# ==============================================================================

AWS_REGION=us-east-1

# URLs obtenidas del script setup-sqs.sh (Paso 3.1)
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/anb-video-processing-queue
SQS_DLQ_URL=https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/anb-video-processing-dlq

# ==============================================================================
# AWS S3 CONFIGURATION
# ==============================================================================

# Nombre del bucket (mismo que usa el worker)
S3_BUCKET_NAME=your-bucket-name

# ==============================================================================
# AWS CREDENTIALS (desde AWS Academy)
# ==============================================================================

# Ve a: AWS Details > AWS CLI > Show
AWS_ACCESS_KEY_ID=ASIA...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...

# ==============================================================================
# API CONFIGURATION (para JMeter y setup JWT)
# ==============================================================================

# URL de la API del backend
API_BASE_URL=http://3.XXX.XXX.XXX

# Usuario de prueba para JMeter
TEST_USER_EMAIL=performance_test@example.com
TEST_USER_PASSWORD=PerformanceTest123!

# ==============================================================================
# PROMETHEUS CONFIGURATION
# ==============================================================================

# IPs públicas del backend y worker para scraping de métricas
PROMETHEUS_BACKEND_TARGET=3.XXX.XXX.XXX:8000
PROMETHEUS_WORKER_TARGET=3.YYY.YYY.YYY:8001

# ==============================================================================
# GRAFANA CONFIGURATION
# ==============================================================================

GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=admin
```

**Guardar:** `Ctrl + O`, `Enter`, `Ctrl + X`

### 6.2 Validar configuración

```bash
# Verificar que el archivo .env está correcto
cat .env

# Verificar que USE_SQS y USE_S3 están en true
grep "USE_SQS\|USE_S3" .env

# Verificar que las URLs de SQS están configuradas
grep "SQS_QUEUE_URL\|SQS_DLQ_URL" .env
```

---

## Paso 7: Configurar Prometheus (5 min)

Prometheus necesita saber las IPs del backend y worker para recolectar métricas.

### 7.1 Editar prometheus.yml

```bash
cd ~/performance-instance
nano prometheus.yml
```

**Busca estas líneas y reemplaza con las IPs reales:**

```yaml
# Antes (línea 13):
      - targets: ['BACKEND_PUBLIC_IP:8000']

# Después (ejemplo):
      - targets: ['3.XXX.XXX.XXX:8000']

# Antes (línea 20):
      - targets: ['WORKER_PUBLIC_IP:8001']

# Después (ejemplo):
      - targets: ['3.YYY.YYY.YYY:8001']
```

**Archivo completo debería verse así:**

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Scrape de métricas del backend (API)
  - job_name: 'backend'
    static_configs:
      - targets: ['3.XXX.XXX.XXX:8000']  # ← Reemplaza con IP real del backend
        labels:
          instance: 'backend-api'
          environment: 'production'

  # Scrape de métricas del worker
  - job_name: 'worker'
    static_configs:
      - targets: ['3.YYY.YYY.YYY:8001']  # ← Reemplaza con IP real del worker
        labels:
          instance: 'celery-worker'
          environment: 'production'
```

**Guardar:** `Ctrl + O`, `Enter`, `Ctrl + X`

### 7.2 Verificar configuración

```bash
# Ver el archivo configurado
cat prometheus.yml

# Asegurarte de que no queden placeholders
grep -i "PUBLIC_IP" prometheus.yml
# Este comando NO debe devolver nada (si devuelve algo, aún hay placeholders)
```

**⚠️ IMPORTANTE:** Si el worker está en la misma instancia que el backend, usa la misma IP para ambos:

```yaml
- targets: ['3.XXX.XXX.XXX:8000']  # Backend
- targets: ['3.XXX.XXX.XXX:8001']  # Worker (misma IP, diferente puerto)
```

---

## Paso 8: Configurar Prometheus (sin túnel SSH) (10 min)

Ya no necesitamos túnel SSH porque usamos AWS SQS. El script `setup-ssh-tunnel.sh` ahora solo configura `prometheus.yml`.

### 8.1 Actualizar script de configuración

El script `setup-ssh-tunnel.sh` ya existe en el repositorio y ahora detecta automáticamente si `USE_SQS=true` para omitir la creación del túnel SSH.

```bash
cd ~/performance-instance
chmod +x setup-ssh-tunnel.sh
```

### 8.2 Ejecutar el script de configuración

```bash
./setup-ssh-tunnel.sh
```

**Con USE_SQS=true, el script:**
1. ✅ Configura `prometheus.yml` con las IPs del `.env`
2. ✅ **NO** crea túnel SSH (porque usas SQS, no Redis)
3. ✅ Valida que las variables de entorno estén configuradas

**Deberías ver:**

```
==========================================
Configuración completada
==========================================
✅ prometheus.yml configurado con IPs
✅ Modo SQS activado (no se requiere túnel SSH)
```

### 8.3 Verificar configuración de Prometheus

```bash
# Ver el archivo configurado
cat prometheus.yml

# Asegurarte de que las IPs fueron reemplazadas correctamente
grep -E "3\." prometheus.yml

# Debería mostrar las IPs reales del backend y worker
```

---

## Paso 9: Desplegar Performance Testing (15 min)

### 9.1 Levantar servicios con Docker Compose

```bash
cd ~/performance-instance

# Levantar servicios en modo detached
docker-compose up -d

# Ver logs de los servicios
docker-compose logs -f
```

**Servicios que se levantarán:**

1. **setup-jwt**: Configura el token JWT inicial (se ejecuta una vez)
2. **renew-jwt**: Renueva el token cada 30 minutos
3. **prometheus**: Recolecta métricas (puerto 9090)
4. **grafana**: Visualiza métricas (puerto 3000)
5. **jmeter**: Ejecutor de pruebas HTTP
6. **producer**: Cliente para inyectar tareas en Redis

### 9.2 Verificar que los servicios están corriendo

```bash
docker ps
```

**Deberías ver:**

```
CONTAINER ID   IMAGE                     STATUS
xxxxx          grafana/grafana:latest    Up 1 minute   0.0.0.0:3000->3000/tcp
xxxxx          prom/prometheus:latest    Up 1 minute   0.0.0.0:9090->9090/tcp
xxxxx          justb4/jmeter:latest      Up 1 minute
xxxxx          producer                  Up 1 minute
xxxxx          renew-jwt                 Up 1 minute
```

### 9.3 Verificar logs iniciales

```bash
# Ver logs del setup JWT
docker logs setup-jwt

# Deberías ver:
# [INFO] Usuario de prueba creado/verificado exitosamente
# [INFO] JWT token obtenido exitosamente

# Ver logs del producer (verificar conexión a Redis)
docker logs producer
```

---

## Paso 10: Verificación End-to-End con AWS SQS y S3 (20 min)

### 10.1 Verificar acceso a Grafana

**Desde tu navegador local:**

```
http://<PERFORMANCE_PUBLIC_IP>:3000
```

- **Usuario:** `admin`
- **Password:** `admin`

**Navegar a:**
- Dashboard del Worker: [http://localhost:3000/d/worker-perf/worker-performance-video-processing](http://localhost:3000/d/worker-perf/worker-performance-video-processing)
- Dashboard del Backend: [http://localhost:3000/d/backend-api-perf/backend-api-performance](http://localhost:3000/d/backend-api-perf/backend-api-performance)

### 10.2 Verificar conexión a AWS SQS

```bash
# Desde tu instancia de performance
docker exec producer python -c "
import boto3
import os
sqs = boto3.client('sqs', region_name=os.getenv('AWS_REGION', 'us-east-1'))
print('✅ Conexión a AWS SQS exitosa')
print('Colas disponibles:', sqs.list_queues())
"

# Verificar estado de la cola
docker exec producer python -c "
import boto3
import os
sqs = boto3.client('sqs', region_name=os.getenv('AWS_REGION', 'us-east-1'))
response = sqs.get_queue_attributes(
    QueueUrl=os.getenv('SQS_QUEUE_URL'),
    AttributeNames=['ApproximateNumberOfMessages']
)
print('Mensajes en cola:', response['Attributes']['ApproximateNumberOfMessages'])
"
```

### 10.3 Verificar acceso a AWS S3

```bash
# Verificar conexión a S3
docker exec producer python -c "
import boto3
s3 = boto3.client('s3')
print('✅ Conexión a AWS S3 exitosa')
print('Buckets:', [b['Name'] for b in s3.list_buckets()['Buckets']])
"

# Verificar acceso al bucket configurado
docker exec producer python -c "
import boto3
import os
s3 = boto3.client('s3')
bucket = os.getenv('S3_BUCKET_NAME')
try:
    s3.head_bucket(Bucket=bucket)
    print(f'✅ Bucket {bucket} accesible')
except Exception as e:
    print(f'❌ Error: {e}')
"
```

### 10.4 Verificar acceso a la API del backend

```bash
# Verificar health check
curl http://<BACKEND_PUBLIC_IP>/health

# Deberías ver:
# {"status":"healthy"}
```

### 10.5 Ejecutar prueba de sanidad con JMeter

```bash
# Ejecutar smoke test
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"

# Ver resultados
cat ~/performance-testing/web-api-tests/scenarios/scenarios/smoke_results.jtl
```

### 10.6 Ejecutar prueba básica con el Producer (AWS SQS + S3)

```bash
# Encolar 5 tareas de prueba (sube videos a S3 y envía mensajes a SQS)
docker exec producer python producer.py --num-videos 5 --video-file ./assets/dummy_file_50mb.mp4 --no-wait --debug

# Deberías ver:
# [INFO] Verificando conexión a AWS SQS...
# [INFO] ✅ Conexión a AWS SQS exitosa
# [INFO] ✅ Bucket S3 'your-bucket-name' existe y es accesible
# [INFO] ✅ 5 archivos subidos a S3 y tareas preparadas
# [INFO] ✅ 5 tareas encoladas exitosamente en SQS

# Verificar archivos en S3
aws s3 ls s3://<S3_BUCKET_NAME>/original/

# Verificar mensajes en SQS
aws sqs get-queue-attributes \
  --queue-url <SQS_QUEUE_URL> \
  --attribute-names ApproximateNumberOfMessages

# Monitorear en Grafana que las tareas se procesan
```

---

## Paso 11: Ejecutar Escenarios de Prueba

### 11.1 Pruebas de API con JMeter

**Smoke Test (Validación básica):**

```bash
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"
```

**Ramp-up Test (Encontrar capacidad máxima):**

```bash
# Prueba con 100 usuarios
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_100_users_results.jtl -Jusers=100"

# Prueba con 200 usuarios
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_200_users_results.jtl -Jusers=200"

# Prueba con 300 usuarios
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_300_users_results.jtl -Jusers=300"
```

**Sustained Test (Prueba sostenida al 80% de capacidad):**

```bash
# Si la capacidad máxima fue 146 usuarios, prueba con 116 (80%)
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/sustained_test.jmx -l /scripts/sustained_116_users_results.jtl -Jusers=116"
```

### 11.2 Pruebas de Worker con Producer

**Prueba básica (20 videos):**

```bash
docker exec producer python producer.py --num-videos 20 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Prueba de saturación (50, 100, 200 videos):**

```bash
# 50 videos
docker exec producer python producer.py --num-videos 50 --video-file ./assets/dummy_file_50mb.mp4 --no-wait

# Esperar a que se procesen (monitorear en Grafana)

# 100 videos
docker exec producer python producer.py --num-videos 100 --video-file ./assets/dummy_file_50mb.mp4 --no-wait

# 200 videos
docker exec producer python producer.py --num-videos 200 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Prueba con videos de 100MB:**

```bash
docker exec producer python producer.py --num-videos 10 --video-file ./assets/dummy_file_100mb.mp4 --no-wait
```

---

## Monitoreo y Troubleshooting

### Ver logs en tiempo real

```bash
# Logs del producer
docker logs -f producer

# Logs de Grafana
docker logs -f grafana

# Logs de Prometheus
docker logs -f prometheus

# Logs de JMeter
docker logs -f jmeter

# Logs de renovación de JWT
docker logs -f renew-jwt
```

### Verificar túnel SSH

```bash
# Ver proceso del túnel SSH
ps aux | grep 'ssh.*6379'

# Verificar puerto 6379 local
netstat -tuln | grep 6379

# Probar conexión a Redis
docker exec producer redis-cli -h localhost -p 6379 ping

# Ver longitud de la cola
docker exec producer redis-cli -h localhost -p 6379 LLEN video_processing
```

### Reiniciar túnel SSH

```bash
# Cerrar túnel SSH existente
pkill -f 'ssh.*6379'

# Volver a crear el túnel
cd ~/performance-instance
./setup-ssh-tunnel.sh
```

### Reiniciar servicios

```bash
cd ~/performance-instance

# Reiniciar todos los servicios
docker-compose restart

# Reiniciar un servicio específico
docker-compose restart producer
docker-compose restart grafana
```

### Ver métricas de Prometheus

**Desde tu navegador:**

```
http://<PERFORMANCE_PUBLIC_IP>:9090
```

**Queries útiles:**

```promql
# Tamaño de la cola de Redis
celery_queue_length{queue="video_processing"}

# Tareas completadas
celery_tasks_completed_total

# Requests HTTP al backend
http_requests_total
```

---

## Troubleshooting Común (AWS SQS + S3)

### Problema 1: El producer no puede conectarse a AWS SQS

**Síntoma:**

```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Solución:**

```bash
# Verificar que las credenciales AWS están configuradas en .env
docker exec producer printenv | grep AWS

# Si las credenciales están vacías o expiradas, actualizarlas
cd ~/performance-instance
nano .env
# Actualiza AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN

# Reiniciar el producer
docker-compose restart producer

# Verificar conexión
docker exec producer python -c "import boto3; print(boto3.client('sqs').list_queues())"
```

### Problema 2: Credenciales de AWS Academy expiraron

**Síntoma:**

```
An error occurred (ExpiredToken) when calling the ... operation: The security token included in the request is expired
```

**Solución:**

```bash
# Las credenciales de AWS Academy expiran cada 4 horas
# Obtener nuevas credenciales:
# 1. Ve a AWS Academy > AWS Details > AWS CLI > Show
# 2. Copia las nuevas credenciales
# 3. Actualiza el .env

cd ~/performance-instance
nano .env
# Pega las nuevas credenciales AWS

# Reiniciar el producer
docker-compose restart producer

# Verificar que las nuevas credenciales funcionan
docker exec producer python -c "import boto3; print('✅ Credenciales válidas')"
```

### Problema 2: JMeter no puede conectarse a la API

**Síntoma:**

```
Non HTTP response code: java.net.ConnectException
```

**Solución:**

```bash
# Verificar que la API está accesible
curl http://<BACKEND_PUBLIC_IP>/health

# Verificar que el .env tiene la IP correcta
cat .env | grep API_BASE_URL

# Verificar Security Group del backend permite HTTP (80) desde tu IP
```

### Problema 3: Grafana no muestra métricas

**Síntoma:**

```
No data
```

**Solución:**

```bash
# Verificar que Prometheus puede hacer scraping del backend
curl http://<BACKEND_PUBLIC_IP>:8000/metrics

# Verificar configuración de Prometheus
docker exec prometheus cat /etc/prometheus/prometheus.yml

# Ver targets en Prometheus
http://<PERFORMANCE_PUBLIC_IP>:9090/targets
```

### Problema 4: No se pueden subir archivos a S3

**Síntoma:**

```
botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling the PutObject operation: Access Denied
```

**Solución:**

```bash
# Verificar que el bucket existe y tienes permisos
aws s3 ls s3://<S3_BUCKET_NAME>

# Verificar que las credenciales tienen permisos de escritura
# En AWS Academy, las credenciales deberían tener acceso completo a S3

# Si el bucket no existe, créalo
aws s3 mb s3://<S3_BUCKET_NAME> --region us-east-1

# Verificar que el bucket está configurado en .env
grep S3_BUCKET_NAME ~/performance-instance/.env
```

### Problema 5: Las tareas no se procesan (mensajes en SQS pero workers no las toman)

**Síntoma:**

```
Mensajes en SQS pero no se procesan
```

**Solución:**

```bash
# Verificar que los workers están escuchando en SQS
# Conectarse a la instancia del worker y verificar logs
ssh -i "worker-key.pem" ubuntu@<WORKER_IP>
docker logs -f celery-worker

# Verificar que el worker tiene las mismas URLs de SQS configuradas
docker exec celery-worker printenv | grep SQS_QUEUE_URL

# Verificar que el worker tiene credenciales AWS válidas
docker exec celery-worker python -c "import boto3; print(boto3.client('sqs').list_queues())"
```

---

## Checklist Final (AWS SQS + S3)

- [ ] Instancia EC2 `anb-performance-testing` creada
- [ ] Security Group `anb-performance-sg` configurado
- [ ] Docker y Docker Compose instalados
- [ ] Colas SQS creadas (Main Queue y DLQ)
- [ ] Bucket S3 creado y accesible
- [ ] Credenciales AWS configuradas en `.env` (Access Key, Secret Key, Session Token)
- [ ] Archivo `.env` configurado con URLs de SQS y nombre de bucket S3
- [ ] `prometheus.yml` configurado con IPs del backend y worker
- [ ] Servicios de Docker Compose corriendo (`docker ps`)
- [ ] Producer puede conectarse a AWS SQS (`docker exec producer python -c "import boto3; print(boto3.client('sqs').list_queues())"`)
- [ ] Producer puede acceder a S3 (`docker exec producer python -c "import boto3; s3=boto3.client('s3'); print(s3.list_buckets())"`)
- [ ] Grafana accesible en puerto 3000
- [ ] JMeter puede ejecutar smoke test exitosamente
- [ ] Producer puede encolar tareas en SQS y subir archivos a S3
- [ ] Métricas visibles en Grafana

---

## Comandos de Referencia Rápida (AWS SQS + S3)

```bash
# Conexión SSH a la instancia de performance
ssh -i "your-key.pem" ubuntu@<PERFORMANCE_PUBLIC_IP>

# Verificar configuración AWS
docker exec producer printenv | grep AWS
docker exec producer printenv | grep SQS
docker exec producer printenv | grep S3

# Verificar conexión a SQS
docker exec producer python -c "import boto3; print(boto3.client('sqs').list_queues())"

# Verificar conexión a S3
docker exec producer python -c "import boto3; print(boto3.client('s3').list_buckets())"

# Configurar Prometheus
cd ~/performance-instance && ./setup-ssh-tunnel.sh

# Levantar servicios
cd ~/performance-instance && docker-compose up -d

# Ver logs de todos los servicios
docker-compose logs -f

# Ejecutar prueba básica con producer (SQS + S3)
docker exec producer python producer.py --num-videos 10 --no-wait --debug

# Ejecutar smoke test con JMeter
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"

# Ver mensajes en SQS
aws sqs get-queue-attributes \
  --queue-url <SQS_QUEUE_URL> \
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible

# Ver archivos en S3
aws s3 ls s3://<S3_BUCKET_NAME>/original/

# Acceder a Grafana
http://<PERFORMANCE_PUBLIC_IP>:3000
Usuario: admin / Password: admin

# Renovar credenciales AWS (cada 4 horas en AWS Academy)
# 1. Obtén nuevas credenciales de AWS Academy
# 2. Edita .env con las nuevas credenciales
cd ~/performance-instance
nano .env
# 3. Reinicia el producer
docker-compose restart producer
```

---

**Tiempo estimado total: 2 - 2.5 horas**

¡Éxito con las pruebas de rendimiento! 🚀
