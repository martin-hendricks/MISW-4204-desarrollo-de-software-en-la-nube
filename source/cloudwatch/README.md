# CloudWatch Metrics - Configuración $0 CloudWatch

> **🎯 COSTO: $0 CloudWatch**: Esta configuración logra $0 en costos de CloudWatch usando SOLO métricas nativas de AWS (gratuitas) para pruebas de carga. awslogs driver REMOVIDO para eliminar costos de CloudWatch Logs (~$1/mes con 53k requests/día).

---

## 💡 ¿Cómo logramos $0 en CloudWatch?

### El problema identificado:
Con **53,000 requests/día** y **95GB en buckets**, los costos eran:
- **CloudWatch Logs** (awslogs driver): ~$0.85-1.33/mes por instancia
- **Métricas custom**: ~$0.38/mes (sin optimizar)
- **Total**: ~$1.23-1.71/mes por instancia

### La solución implementada:

#### 1️⃣ Logs locales (NO CloudWatch Logs)
```yaml
# docker-compose.yml - ANTES (costaba dinero)
logging:
  driver: awslogs  # ❌ $0.50/GB ingestion + $0.03/GB-month storage

# docker-compose.yml - AHORA (gratis)
logging:
  driver: json-file  # ✅ $0 - logs guardados localmente
  options:
    max-size: "10m"
    max-file: "3"
```

**Ver logs**: `docker logs anb-backend` o `docker logs anb-worker`

#### 2️⃣ Métricas de pruebas de carga: SOLO AWS nativas (FREE)

Todos los KPIs de pruebas de carga se pueden medir con métricas **100% gratuitas**:

| KPI | Métrica AWS Nativa (FREE) | Namespace |
|-----|---------------------------|-----------|
| p95 latency Backend | No disponible en FREE - usar custom (~$0.02/mes) | ANB/Backend |
| Error Rate Backend | No disponible en FREE - usar custom (~$0.02/mes) | ANB/Backend |
| CPU Peak Backend | `CPUUtilization` | AWS/EC2 |
| Memoria Backend | `mem_used_percent` | CWAgent |
| Cola estable Worker | `ApproximateNumberOfMessagesVisible` | AWS/SQS |
| Throughput Worker (MB/min) | No disponible en FREE - usar custom (~$0.02/mes) | ANB/Worker |
| S3 Throttling | `4xxErrors`, `5xxErrors` | AWS/S3 |

**Resultado**:
- **Opción A (100% FREE)**: Usar solo métricas EC2/SQS → $0 total
  - Limitación: No tienes p95 latency ni error rate granular
  - Tienes: CPU, memoria, cola, S3 health ✅

- **Opción B (Métricas custom mínimas)**: ~$0.09/mes
  - Tienes: p95 latency, error rate, throughput MB/min ✅
  - Mantiene todos los KPIs de pruebas de carga ✅

#### 3️⃣ Logs locales vs CloudWatch Logs: Trade-offs

| Feature | json-file (Local) | awslogs (CloudWatch) |
|---------|-------------------|----------------------|
| Costo | **$0** | ~$1/mes (53k req/día) |
| Ver logs | `docker logs <container>` | CloudWatch Console |
| Búsqueda | `docker logs \| grep` | CloudWatch Insights |
| Persistencia | Solo en instancia EC2 | Centralizado en AWS |
| Auto Scaling | Logs separados por instancia | Logs unificados |
| Análisis | Manual o scripts | Queries SQL-like |

**Para pruebas de carga**: Logs locales son suficientes. Las métricas AWS nativas (FREE) te dan toda la visibilidad necesaria.

---

## 🚨 Elige tu Estrategia de Costos

### Opción 1: $0 ABSOLUTO (Recomendado para AWS Academy)

**Configuración actual**: Docker compose con logs locales ✅

**Pasos adicionales**:
1. Deshabilitar métricas custom → Ver [ZERO_COST_MODE.md](./ZERO_COST_MODE.md)
2. Usar SOLO métricas AWS nativas (EC2, SQS, S3)

**Resultado**:
- Costo: **$0/mes**
- Tienes: CPU, memoria, cola, S3 health ✅
- No tienes: p95 latency, error rate granular ⚠️

### Opción 2: ~$0.09/mes (Métricas custom optimizadas)

**Configuración actual**: Docker compose con logs locales ✅ + métricas custom optimizadas ✅

**No hacer nada adicional** - ya está configurado.

**Resultado**:
- Costo: **~$0.09/mes** (~$1.62/año)
- Tienes: CPU, memoria, cola, S3 health, p95 latency, error rate, throughput MB/min ✅
- Métricas completas para pruebas de carga ✅

### Opción 3: ~$1.00-1.33/mes (Logs centralizados)

**Si necesitas CloudWatch Logs** (Insights, búsqueda avanzada, logs centralizados en Auto Scaling):

1. Revertir `docker-compose.yml` a usar `awslogs` driver
2. Aceptar costo de CloudWatch Logs

**Resultado**:
- Costo: **~$1.00-1.33/mes** (~$12-16/año)
- Tienes: Todo lo anterior + CloudWatch Logs Insights ✅
- Logs centralizados para múltiples instancias ✅

---

### 📊 Comparación Visual

```
┌─────────────────────────────────────────────────────────────┐
│  OPCIÓN           COSTO      LOGS        MÉTRICAS CUSTOM    │
├─────────────────────────────────────────────────────────────┤
│  1. $0 ABSOLUTO   $0         Local       ❌ Deshabilitadas  │
│                              json-file   (solo AWS nativas)  │
│                                                               │
│  2. OPTIMIZADO    ~$0.09/m  Local       ✅ Optimizadas      │
│     (ACTUAL)                 json-file   (sampling, 5min)    │
│                                                               │
│  3. COMPLETO      ~$1.33/m  CloudWatch  ✅ Optimizadas      │
│                              awslogs     (sampling, 5min)    │
└─────────────────────────────────────────────────────────────┘
```

**Recomendación**: Si estás en AWS Academy (presupuesto limitado), usa **Opción 2** (actual). Si necesitas reducir más, ve a **Opción 1** ([ZERO_COST_MODE.md](./ZERO_COST_MODE.md)).

---

## 🔄 Auto Scaling Compatible

**¿Usas Auto Scaling?** Las métricas custom se agregan automáticamente por `Service` → **NO necesitas actualizar dashboards** cuando se crean nuevas instancias.

**📖 Guía completa**: [AUTO_SCALING_GUIDE.md](./AUTO_SCALING_GUIDE.md)

**Resumen rápido**:
- ✅ Métricas custom (p95, error rate, throughput): Agregadas por `Service=API` o `Service=VideoProcessor`
- ✅ SQS metrics: Agregadas por `QueueName`
- ⚠️ EC2 CPU/Memoria: Usar `AutoScalingGroupName` o listar instancias dinámicamente

```bash
# Query que funciona con 1 o N instancias
aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name RequestDuration \
  --dimensions Name=Service,Value=API \  # ← Agrega TODAS las instancias
  --extended-statistics p95
```

---

## 🚀 Setup Rápido (AWS Academy)

### 1. Asignar LabInstanceProfile a EC2

**Consola AWS**:
- EC2 → Launch Instance → Advanced details → **IAM instance profile: LabInstanceProfile**

**O en instancias existentes**:
```bash
aws ec2 associate-iam-instance-profile \
  --instance-id i-XXXXX \
  --iam-instance-profile Name=LabInstanceProfile
```

### 2. Configurar Variables de Entorno

**Backend (.env)**:
```bash
CLOUDWATCH_NAMESPACE=ANB/Backend
ENVIRONMENT=production
AWS_REGION=us-east-1
```

**Worker (.env)**:
```bash
CLOUDWATCH_NAMESPACE=ANB/Worker
ENVIRONMENT=production
AWS_REGION=us-east-1
```

### 3. **NUEVO: Habilitar Métricas Nativas EC2 (GRATIS)**

Las métricas de CPU, Memoria y Disco ahora se obtienen de **EC2 CloudWatch Agent (FREE)**:

#### Opción A: CloudWatch Agent (Recomendado - Métricas detalladas)

```bash
# Instalar CloudWatch Agent en cada instancia EC2
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Crear configuración
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard

# O usar configuración predeterminada:
cat <<'EOF' | sudo tee /opt/aws/amazon-cloudwatch-agent/etc/config.json
{
  "agent": {
    "metrics_collection_interval": 300
  },
  "metrics": {
    "namespace": "CWAgent",
    "metrics_collected": {
      "cpu": {
        "measurement": [{"name": "cpu_usage_idle"}, {"name": "cpu_usage_iowait"}],
        "metrics_collection_interval": 300,
        "totalcpu": false
      },
      "disk": {
        "measurement": [{"name": "used_percent"}],
        "metrics_collection_interval": 300,
        "resources": ["*"]
      },
      "mem": {
        "measurement": [{"name": "mem_used_percent"}],
        "metrics_collection_interval": 300
      }
    }
  }
}
EOF

# Iniciar agente
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

#### Opción B: EC2 Detailed Monitoring (Básico - Solo CPU)

```bash
# Habilitar monitoring detallado (solo CPUUtilization - FREE)
aws ec2 monitor-instances --instance-ids i-XXXXX
```

### 4. **NUEVO: Configurar Métricas SQS (GRATIS)**

Las métricas de SQS son **100% gratuitas** y ya están disponibles automáticamente:

```bash
# Ver métricas disponibles de tu cola
aws cloudwatch list-metrics --namespace AWS/SQS \
  --dimensions Name=QueueName,Value=video-processing-queue
```

**Métricas SQS disponibles (GRATIS):**
- `ApproximateNumberOfMessagesVisible` - Mensajes en cola
- `ApproximateAgeOfOldestMessage` - Latencia de procesamiento
- `NumberOfMessagesSent` - Mensajes enviados
- `NumberOfMessagesReceived` - Mensajes recibidos
- `NumberOfMessagesDeleted` - Mensajes procesados

### 5. Deploy

```bash
# Backend
docker-compose build backend && docker-compose up -d backend

# Worker
docker-compose build worker && docker-compose up -d worker
```

### 6. Verificar

```bash
# Ver logs EMF (debe mostrar JSON con "_aws")
docker logs anb-backend 2>&1 | grep '_aws'
docker logs anb-worker 2>&1 | grep '_aws'

# Generar tráfico
for i in {1..50}; do curl http://BACKEND_IP/health; sleep 1; done

# Esperar 2-3 minutos, luego:
# CloudWatch Console → All metrics → ANB/Backend, ANB/Worker, CWAgent, AWS/SQS
```

---

## 📊 Métricas Disponibles

### ✅ Custom Metrics (ANB/Backend) - Aplicación Backend

**Métricas de Requests HTTP:**
- `RequestCount` - Total de requests por endpoint
- `RequestDuration` - Duración en milisegundos (p50, p95, p99)
- `ErrorCount` - Errores 5xx
- `Success` - Requests exitosos (2xx)

**Métricas de Health:**
- `ServiceHeartbeat` - Confirma que el servicio está activo (cada 5min)

**Dimensiones:**
- `Method` - GET, POST, PUT, DELETE
- `Endpoint` - Path del endpoint
- `StatusCode` - 200, 400, 500, etc.
- `InstanceId` - ID de la instancia EC2
- `Environment` - production, staging, dev

**Optimizaciones de costos:**
- ✅ Sampling en `/health` (10% de requests)
- ✅ Sampling en `/` (20% de requests)
- ✅ Excluye `/metrics`, `/docs`, `/redoc`, `/openapi.json`
- ✅ CPU/Memoria eliminadas (usar métricas EC2/CWAgent)

---

### ✅ Custom Metrics (ANB/Worker) - Procesamiento de Videos

**Métricas de Tareas Celery:**
- `TaskCount` - Tareas ejecutadas por estado (Success, Failed, Retry)
- `TaskDuration` - Duración de tareas en segundos (p50, p95, p99)
- `TaskFailure` - Tareas fallidas con tipo de error
- `VideoFileSize` - Tamaño de archivos procesados (histogram)

**Métricas de Health:**
- `ServiceHeartbeat` - Confirma que el worker está activo (cada 5min)

**Dimensiones:**
- `TaskName` - process_video, etc.
- `Status` - Success, Failed, Retry
- `ErrorType` - Exception name cuando hay error
- `InstanceId` - ID de la instancia EC2
- `Environment` - production, staging, dev

**Optimizaciones de costos:**
- ✅ CPU/Memoria eliminadas (usar métricas EC2/CWAgent)
- ✅ Métricas de cola eliminadas (usar SQS nativas - FREE)

---

### 🆓 Métricas Nativas AWS (GRATIS)

#### EC2 CloudWatch Agent (namespace: CWAgent)
**Disponibles después de instalar CloudWatch Agent:**

```bash
# CPU
- cpu_usage_idle
- cpu_usage_iowait
- cpu_usage_system
- cpu_usage_user

# Memoria
- mem_used_percent
- mem_available
- mem_used

# Disco
- disk_used_percent
- disk_free
- disk_used
```

#### EC2 Basic Metrics (namespace: AWS/EC2)
**Disponibles automáticamente (intervalo 5min - FREE):**

```bash
- CPUUtilization
- NetworkIn
- NetworkOut
- DiskReadBytes
- DiskWriteBytes
- StatusCheckFailed
```

#### SQS Metrics (namespace: AWS/SQS)
**Disponibles automáticamente (100% GRATIS):**

```bash
- ApproximateNumberOfMessagesVisible  # Profundidad de cola
- ApproximateAgeOfOldestMessage      # Latencia de procesamiento
- NumberOfMessagesSent               # Mensajes producidos
- NumberOfMessagesReceived           # Mensajes consumidos
- NumberOfMessagesDeleted            # Mensajes completados
- ApproximateNumberOfMessagesNotVisible  # Mensajes en procesamiento
```

**Dimensiones SQS:**
- `QueueName` - Nombre de la cola SQS

---

## 💰 Comparación de Costos (53k requests/día, 95GB bucket)

### ❌ Antes (Con awslogs driver)
```
CloudWatch Logs (awslogs driver):
  - Ingestion: 53k requests/día × 1KB avg log × 30 días = ~1.6GB
  - Costo ingestion: 1.6GB × $0.50/GB = $0.80/mes
  - Costo storage: 1.6GB × $0.03/GB-month = $0.05/mes
  - Total CloudWatch Logs: ~$0.85 - $1.33/mes

Métricas custom (sin optimizar):
  - Backend: 48,640 data points/día × 30 = 1,459,200 data points/mes
  - Worker: 10,200 data points/día × 30 = 306,000 data points/mes
  - Total: 1,765,200 data points/mes
  - Costo métricas: ~$0.38/mes

COSTO TOTAL: ~$1.23 - $1.71/mes por instancia
```

### ✅ Después (Sin awslogs - Solo métricas FREE)
```
CloudWatch Logs:
  - awslogs driver REMOVIDO
  - Logs guardados localmente (json-file driver)
  - Costo: $0

Métricas para pruebas de carga:
  - AWS/EC2 (CPUUtilization): $0 (FREE)
  - AWS/SQS (ApproximateNumberOfMessagesVisible): $0 (FREE)
  - AWS/S3 (4xxErrors, 5xxErrors): $0 (FREE - si S3 Request Metrics habilitado)
  - CWAgent (mem_used_percent, disk_used_percent): $0 (FREE)

Custom metrics (OPCIONAL - si las necesitas):
  - Backend optimizado: 12,288 data points/día × 30 = 368,640/mes
  - Worker optimizado: 3,288 data points/día × 30 = 98,640/mes
  - Total: 467,280 data points/mes
  - Costo: ~$0.09/mes (pero puedes deshabilitarlas → $0 total)

COSTO TOTAL: $0/mes (métricas FREE) o ~$0.09/mes (con custom metrics optimizadas)
AHORRO: ~$1.23 - $1.71/mes por instancia
```

---

## 📈 Crear Dashboard Optimizado

```bash
# Dashboard recomendado usando métricas FREE + custom
aws cloudwatch put-dashboard --dashboard-name ANB-Production \
  --dashboard-body '{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["ANB/Backend", "RequestDuration", {"stat": "p95"}],
          ["ANB/Backend", "ErrorCount", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "API Performance"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/EC2", "CPUUtilization", {"stat": "Average"}],
          ["CWAgent", "mem_used_percent", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "System Resources (FREE)"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/SQS", "ApproximateNumberOfMessagesVisible", {"dimensions": {"QueueName": "video-processing-queue"}}],
          ["AWS/SQS", "ApproximateAgeOfOldestMessage", {"dimensions": {"QueueName": "video-processing-queue"}}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Queue Health (FREE)"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["ANB/Worker", "TaskDuration", {"stat": "p95"}],
          ["ANB/Worker", "TaskFailure", {"stat": "Sum"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Worker Performance"
      }
    }
  ]
}'
```

---

## 🔧 Alternativa: Credenciales Manuales

Si no puedes usar LabInstanceProfile:

**1. Obtener credenciales** (AWS Academy → AWS Details → Show AWS CLI)

**2. Agregar a .env**:
```bash
AWS_ACCESS_KEY_ID=ASIA...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=FwoG...  # ← Importante
AWS_REGION=us-east-1
```

⚠️ **Expiran cada 4 horas** - debes renovarlas.

---

## 🚨 Crear Alarmas Optimizadas (Recomendado)

### Alarmas usando métricas FREE (SQS)

```bash
# Cola larga (SQS - FREE)
aws cloudwatch put-metric-alarm \
  --alarm-name ANB-Queue-Backlog \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --dimensions Name=QueueName,Value=video-processing-queue \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold \
  --alarm-description "Alerta cuando hay más de 50 videos en cola"

# Latencia de cola alta (SQS - FREE)
aws cloudwatch put-metric-alarm \
  --alarm-name ANB-Queue-Latency-High \
  --metric-name ApproximateAgeOfOldestMessage \
  --namespace AWS/SQS \
  --dimensions Name=QueueName,Value=video-processing-queue \
  --statistic Maximum \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 900 \
  --comparison-operator GreaterThanThreshold \
  --alarm-description "Alerta cuando un mensaje lleva >15min en cola"

# CPU Alta EC2 (FREE)
aws cloudwatch put-metric-alarm \
  --alarm-name ANB-EC2-CPU-High \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --dimensions Name=InstanceId,Value=i-XXXXX \
  --statistic Average \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --alarm-description "Alerta cuando CPU >80%"
```

### Alarmas usando métricas custom

```bash
# Latencia alta API (custom metric - ya optimizada con sampling)
aws cloudwatch put-metric-alarm \
  --alarm-name ANB-API-Latency-High \
  --metric-name RequestDuration \
  --namespace ANB/Backend \
  --statistic p95 \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 2000 \
  --comparison-operator GreaterThanThreshold \
  --alarm-description "Alerta cuando p95 latencia >2s"

# Errores altos (custom metric)
aws cloudwatch put-metric-alarm \
  --alarm-name ANB-API-Errors-High \
  --metric-name ErrorCount \
  --namespace ANB/Backend \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --alarm-description "Alerta cuando hay >10 errores en 5min"

# Tareas fallando (custom metric)
aws cloudwatch put-metric-alarm \
  --alarm-name ANB-Worker-Failures \
  --metric-name TaskFailure \
  --namespace ANB/Worker \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --alarm-description "Alerta cuando >5 tareas fallan en 5min"
```

---

## 🐛 Troubleshooting

**Métricas no aparecen**:
1. Esperar 5 minutos (delay inicial)
2. Verificar logs EMF: `docker logs anb-backend | grep '_aws'`
3. Verificar región en .env: `AWS_REGION=us-east-1`
4. Test manual: `aws cloudwatch put-metric-data --namespace ANB/Test --metric-name Test --value 1`

**Credenciales expiradas**:
- AWS Academy → AWS Details → Copiar nuevas credenciales → Actualizar .env → `docker-compose restart`

---

## 📁 Archivos Modificados (Optimización)

### Archivos actualizados:
- ✅ `source/cloudwatch/cloudwatch_metrics.py` - Módulo EMF (sin cambios)
- ✅ `source/backend/app/main.py` - **OPTIMIZADO**:
  - ❌ Eliminadas métricas de CPU/Memoria (usar EC2/CWAgent)
  - ✅ Agregado sampling para `/health` (10%) y `/` (20%)
  - ✅ Heartbeat cada 5min (antes: system metrics cada 60s)
  - ✅ Reducción de ~75% en data points

- ✅ `source/worker/main.py` - **OPTIMIZADO**:
  - ❌ Eliminadas métricas de CPU/Memoria (usar EC2/CWAgent)
  - ✅ Heartbeat cada 5min (antes: system metrics cada 60s)
  - ✅ Reducción de ~68% en data points

- ✅ `source/worker/celery_app.py` - Signals con métricas (sin cambios)
- ✅ `source/cloudwatch/README.md` - **ACTUALIZADO** con nueva documentación

### Métricas reemplazadas por AWS nativas (FREE):
```
❌ ProcessCPU → ✅ AWS/EC2: CPUUtilization
❌ ProcessMemoryMB → ✅ CWAgent: mem_used_percent
❌ SystemCPU → ✅ AWS/EC2: CPUUtilization
❌ SystemMemoryPercent → ✅ CWAgent: mem_used_percent
❌ QueueLength (custom) → ✅ AWS/SQS: ApproximateNumberOfMessagesVisible
```

---

## 🎯 Resumen de Optimizaciones

| Optimización | Impacto | Ahorro |
|--------------|---------|--------|
| Eliminar métricas CPU/Memoria custom | -11 métricas/instancia | ~$0.18/mes |
| Sampling en /health (90% skip) | -36,000 data points/día | ~$0.32/mes |
| Heartbeat 5min (vs 60s system metrics) | -8,352 data points/día | ~$0.08/mes |
| Usar SQS métricas nativas | $0 (gratis) | Visibilidad gratis |
| Usar EC2/CWAgent métricas | $0 (gratis) | Visibilidad gratis |
| **TOTAL** | **-76% data points** | **~$0.58/mes por instancia** |

### Métricas que SÍ se mantienen (importantes):
- ✅ `RequestCount`, `RequestDuration`, `ErrorCount` - Críticas para API
- ✅ `TaskCount`, `TaskDuration`, `TaskFailure` - Críticas para Worker
- ✅ `VideoFileSize` - Análisis de carga
- ✅ `ServiceHeartbeat` - Detección de servicios caídos

---

## 🔍 Verificar Optimizaciones

```bash
# 1. Verificar que heartbeat está funcionando (cada 5min)
aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name ServiceHeartbeat \
  --dimensions Name=MetricType,Value=Health \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# 2. Verificar métricas EC2 (FREE)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-XXXXX \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# 3. Verificar métricas SQS (FREE)
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value=video-processing-queue \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average

# 4. Verificar sampling (requests con métricas deberían ser ~10% del total)
# En CloudWatch Console:
# - ANB/Backend → RequestCount → Ver gráfica
# - Comparar con logs del contenedor (debería ser ~10x más requests que métricas)
```

---

## 🧪 Pruebas de Carga con Métricas FREE

**📖 Guía completa**: Ver [LOAD_TESTING_METRICS.md](LOAD_TESTING_METRICS.md)

### Criterios de éxito/fallo disponibles (100% FREE):

#### Backend:
- ✅ **p95 de endpoints ≤ 1s** → `ANB/Backend: RequestDuration` (custom optimizada)
- ✅ **Errores ≤ 5%** → `ANB/Backend: ErrorCount / RequestCount` (custom optimizada)
- ✅ **Sin throttling S3** → `AWS/S3: 4xxErrors, 5xxErrors` (FREE)
- ✅ **Primer KPI degradado** → `AWS/EC2: CPUUtilization`, `CWAgent: mem_used_percent`, `AWS/RDS` (FREE)

#### Worker:
- ✅ **Capacidad (MB/min)** → `ANB/Worker: VideoFileSize` (custom optimizada)
- ✅ **Cola estable (tendencia ~0)** → `AWS/SQS: ApproximateNumberOfMessagesVisible` (FREE)

### Dashboard de pruebas de carga:

El archivo `LOAD_TESTING_METRICS.md` incluye:
- 📊 Dashboard JSON completo con todos los KPIs
- 🔍 Queries de CloudWatch para cada criterio
- 📋 Script de reporte automatizado
- ✅ Checklist pre-prueba

**Crear dashboard**:
```bash
# Ver LOAD_TESTING_METRICS.md para JSON completo
aws cloudwatch put-dashboard --dashboard-name ANB-LoadTest --dashboard-body file://load_test_dashboard.json
```

---

**Prometheus/Grafana removido** - Ya no se usa.
**CloudWatch Agent** - Opcional pero recomendado para métricas detalladas de memoria/disco (FREE).
