# Modo $0 Absoluto en CloudWatch

> **🎯 Objetivo**: Lograr $0 total en CloudWatch eliminando tanto CloudWatch Logs como métricas custom.

---

## 🚫 ¿Quieres $0 ABSOLUTO en CloudWatch?

Si prefieres **$0 total** y puedes vivir sin métricas de latencia p95 y error rate granular, sigue estos pasos:

### Paso 1: Deshabilitar métricas custom en Backend

**Archivo**: `source/backend/app/main.py`

```python
# OPCIÓN A: Comentar el middleware de CloudWatch completamente
# @app.middleware("http")
# async def cloudwatch_middleware(request: Request, call_next):
#     # ... todo el contenido del middleware
#     pass

# OPCIÓN B: Agregar un flag de entorno para deshabilitar
import os
ENABLE_CLOUDWATCH = os.getenv("ENABLE_CLOUDWATCH", "false").lower() == "true"

@app.middleware("http")
async def cloudwatch_middleware(request: Request, call_next):
    if not ENABLE_CLOUDWATCH:
        return await call_next(request)

    # ... resto del código de métricas
```

**Configurar en .env**:
```bash
ENABLE_CLOUDWATCH=false  # ← Deshabilita métricas custom
```

### Paso 2: Deshabilitar métricas custom en Worker

**Archivo**: `source/worker/main.py`

```python
import os
ENABLE_CLOUDWATCH = os.getenv("ENABLE_CLOUDWATCH", "false").lower() == "true"

@app.on_event("startup")
async def startup_event():
    if ENABLE_CLOUDWATCH:
        asyncio.create_task(publish_heartbeat())
    else:
        logger.info("CloudWatch metrics disabled (ENABLE_CLOUDWATCH=false)")
```

**Archivo**: `source/worker/celery_app.py`

```python
import os
ENABLE_CLOUDWATCH = os.getenv("ENABLE_CLOUDWATCH", "false").lower() == "true"

@task_success.connect
def task_success_handler(sender=None, **kwargs):
    if not ENABLE_CLOUDWATCH:
        return
    # ... resto del código de métricas
```

**Configurar en .env**:
```bash
ENABLE_CLOUDWATCH=false  # ← Deshabilita métricas custom
```

### Paso 3: Verificar que awslogs driver está deshabilitado

**Archivos ya actualizados**:
- ✅ `source/deployment/backend-instance/docker-compose.yml`
- ✅ `source/deployment/worker-instance/docker-compose.yml`

Ambos usan `json-file` driver (logs locales, $0 costo).

### Paso 4: Redeploy

```bash
# Backend
cd source/deployment/backend-instance
docker-compose down
docker-compose build backend
docker-compose up -d

# Worker
cd source/deployment/worker-instance
docker-compose down
docker-compose build worker
docker-compose up -d
```

---

## ✅ Resultado: $0 ABSOLUTO en CloudWatch

### Métricas disponibles (100% FREE):

#### Backend Monitoring:
```bash
# CPU (EC2 - FREE)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-XXXXX \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# Memoria (CWAgent - FREE)
aws cloudwatch get-metric-statistics \
  --namespace CWAgent \
  --metric-name mem_used_percent \
  --dimensions Name=InstanceId,Value=i-XXXXX \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# Network (EC2 - FREE)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name NetworkIn \
  --dimensions Name=InstanceId,Value=i-XXXXX \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

#### Worker Monitoring:
```bash
# Profundidad de cola (SQS - FREE)
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value=video-processing-queue \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# Latencia de procesamiento (SQS - FREE)
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateAgeOfOldestMessage \
  --dimensions Name=QueueName,Value=video-processing-queue \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Maximum

# Mensajes procesados (SQS - FREE)
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name NumberOfMessagesDeleted \
  --dimensions Name=QueueName,Value=video-processing-queue \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

#### S3 Monitoring (FREE - si habilitas Request Metrics):
```bash
# Errores S3 (FREE)
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name 4xxErrors \
  --dimensions Name=BucketName,Value=tu-bucket \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

---

## 📊 Dashboard con Métricas 100% FREE

Crear dashboard usando SOLO métricas gratuitas:

```bash
aws cloudwatch put-dashboard --dashboard-name ANB-Free-Metrics \
  --dashboard-body '{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "Backend CPU (EC2 - FREE)",
        "metrics": [
          ["AWS/EC2", "CPUUtilization", {"stat": "Average", "dimensions": {"InstanceId": "i-XXXXX"}}]
        ],
        "period": 300,
        "region": "us-east-1",
        "yAxis": {"left": {"min": 0, "max": 100}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Backend Memory (CWAgent - FREE)",
        "metrics": [
          ["CWAgent", "mem_used_percent", {"stat": "Average", "dimensions": {"InstanceId": "i-XXXXX"}}]
        ],
        "period": 300,
        "region": "us-east-1",
        "yAxis": {"left": {"min": 0, "max": 100}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Queue Depth (SQS - FREE)",
        "metrics": [
          ["AWS/SQS", "ApproximateNumberOfMessagesVisible", {"dimensions": {"QueueName": "video-processing-queue"}}]
        ],
        "period": 300,
        "region": "us-east-1",
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Queue Latency (SQS - FREE)",
        "metrics": [
          ["AWS/SQS", "ApproximateAgeOfOldestMessage", {"stat": "Maximum", "dimensions": {"QueueName": "video-processing-queue"}}]
        ],
        "period": 300,
        "region": "us-east-1",
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Worker CPU (EC2 - FREE)",
        "metrics": [
          ["AWS/EC2", "CPUUtilization", {"stat": "Average", "dimensions": {"InstanceId": "i-YYYYY"}}]
        ],
        "period": 300,
        "region": "us-east-1",
        "yAxis": {"left": {"min": 0, "max": 100}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "S3 Errors (FREE)",
        "metrics": [
          ["AWS/S3", "4xxErrors", {"stat": "Sum", "dimensions": {"BucketName": "tu-bucket"}}],
          [".", "5xxErrors", {"stat": "Sum"}]
        ],
        "period": 300,
        "region": "us-east-1",
        "yAxis": {"left": {"min": 0}}
      }
    }
  ]
}'
```

**IMPORTANTE**: Reemplaza:
- `i-XXXXX` → Instance ID del Backend
- `i-YYYYY` → Instance ID del Worker
- `video-processing-queue` → Nombre de tu cola SQS
- `tu-bucket` → Nombre de tu bucket S3

---

## 🎯 Pruebas de Carga con Métricas FREE

### KPIs que SÍ puedes medir (100% FREE):

| KPI | Métrica FREE | Query |
|-----|--------------|-------|
| **CPU Peak Backend** | `AWS/EC2: CPUUtilization` | ✅ Disponible |
| **Memoria Backend** | `CWAgent: mem_used_percent` | ✅ Disponible |
| **Cola estable** | `AWS/SQS: ApproximateNumberOfMessagesVisible` | ✅ Disponible |
| **Latencia de procesamiento** | `AWS/SQS: ApproximateAgeOfOldestMessage` | ✅ Disponible |
| **S3 Throttling** | `AWS/S3: 4xxErrors, 5xxErrors` | ✅ Disponible |
| **Worker Throughput (mensajes/min)** | `AWS/SQS: NumberOfMessagesDeleted` | ✅ Disponible |

### KPIs que NO puedes medir sin métricas custom:

| KPI | Requiere | Costo |
|-----|----------|-------|
| **p95 latency Backend** | `ANB/Backend: RequestDuration` | ~$0.02/mes |
| **Error Rate Backend** | `ANB/Backend: ErrorCount, RequestCount` | ~$0.02/mes |
| **Throughput Worker (MB/min)** | `ANB/Worker: VideoFileSize` | ~$0.02/mes |

**Alternativas SIN métricas custom**:
- **p95 latency**: Usar herramientas externas (JMeter, k6, Locust) durante pruebas de carga
- **Error Rate**: Analizar logs locales con `docker logs | grep ERROR`
- **Throughput MB/min**: Calcular manualmente desde tamaño promedio de videos × mensajes procesados (SQS)

---

## 📝 Script de Reporte con Métricas FREE

**Archivo**: `source/cloudwatch/generate_free_metrics_report.sh`

```bash
#!/bin/bash
# Reporte de pruebas de carga usando SOLO métricas FREE

set -e

START_TIME="${1:-$(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%SZ)}"
END_TIME="${2:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
AWS_REGION="${AWS_REGION:-us-east-1}"

BACKEND_INSTANCE="${BACKEND_INSTANCE_ID:-}"
WORKER_INSTANCE="${WORKER_INSTANCE_ID:-}"
QUEUE_NAME="${SQS_QUEUE_NAME:-video-processing-queue}"

echo "========================================"
echo "  FREE METRICS REPORT"
echo "========================================"
echo "Period: $START_TIME to $END_TIME"
echo ""

echo "=== BACKEND METRICS (FREE) ==="
echo ""

# Backend CPU
echo -n "CPU Peak: "
CPU=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value="$BACKEND_INSTANCE" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 1800 \
  --statistics Maximum \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Maximum' \
  --output text 2>/dev/null || echo "N/A")
echo "${CPU}%"

# Backend Memory
echo -n "Memory Peak: "
MEM=$(aws cloudwatch get-metric-statistics \
  --namespace CWAgent \
  --metric-name mem_used_percent \
  --dimensions Name=InstanceId,Value="$BACKEND_INSTANCE" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 1800 \
  --statistics Maximum \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Maximum' \
  --output text 2>/dev/null || echo "N/A")
echo "${MEM}%"
echo ""

echo "=== WORKER METRICS (FREE) ==="
echo ""

# Queue Stability
echo "Queue Stability:"
START_DEPTH=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value="$QUEUE_NAME" \
  --start-time "$START_TIME" \
  --end-time "$(date -u -d "$START_TIME + 1 minute" +%Y-%m-%dT%H:%M:%SZ)" \
  --period 60 \
  --statistics Average \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Average' \
  --output text 2>/dev/null || echo "0")

END_DEPTH=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value="$QUEUE_NAME" \
  --start-time "$(date -u -d "$END_TIME - 1 minute" +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$END_TIME" \
  --period 60 \
  --statistics Average \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Average' \
  --output text 2>/dev/null || echo "0")

echo "  Start: $START_DEPTH"
echo "  End: $END_DEPTH"
echo "  Trend: $(echo "$END_DEPTH - $START_DEPTH" | bc)"
echo ""

# Messages Processed
echo -n "Messages Processed: "
PROCESSED=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name NumberOfMessagesDeleted \
  --dimensions Name=QueueName,Value="$QUEUE_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 1800 \
  --statistics Sum \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Sum' \
  --output text 2>/dev/null || echo "0")
echo "$PROCESSED messages"
echo ""

echo "=== S3 METRICS (FREE) ==="
echo ""

# S3 Errors
echo -n "S3 Errors: "
S3_ERRORS=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name 5xxErrors \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 1800 \
  --statistics Sum \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Sum' \
  --output text 2>/dev/null || echo "0")
echo "$S3_ERRORS errors"
echo ""

echo "========================================"
echo "  Cost: $0 (100% FREE metrics)"
echo "========================================"
```

**Uso**:
```bash
chmod +x source/cloudwatch/generate_free_metrics_report.sh
BACKEND_INSTANCE_ID=i-XXXXX \
WORKER_INSTANCE_ID=i-YYYYY \
SQS_QUEUE_NAME=video-processing-queue \
./source/cloudwatch/generate_free_metrics_report.sh "2025-01-15T10:00:00Z" "2025-01-15T10:30:00Z"
```

---

## 🎉 Resultado Final

### Configuración actual (después de estos cambios):

```
✅ Logs: json-file driver (local) → $0
✅ Métricas: SOLO AWS nativas (EC2, SQS, S3) → $0

COSTO TOTAL: $0/mes en CloudWatch
```

### Trade-offs aceptados:

| Perdiste | Ganaste |
|----------|---------|
| p95 latency granular de API | $0 en CloudWatch (~$1.71/mes ahorrado) |
| Error rate granular por endpoint | Simplificación de arquitectura |
| Throughput MB/min automático | Logs locales (más rápidos de acceder) |
| CloudWatch Logs Insights | Control total de logs |

**Conclusión**: Si tus pruebas de carga se enfocan en estabilidad del sistema (CPU, memoria, cola), métricas FREE son suficientes. Si necesitas KPIs de latencia p95, considera habilitar métricas custom (~$0.09/mes).

---

## 🔄 Volver a habilitar métricas custom

Si en el futuro quieres volver a usar métricas custom (costo ~$0.09/mes):

```bash
# Backend y Worker .env
ENABLE_CLOUDWATCH=true

# Redeploy
docker-compose down
docker-compose build
docker-compose up -d
```
