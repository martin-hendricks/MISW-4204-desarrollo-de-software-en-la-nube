# Guía de Auto Scaling con CloudWatch Metrics

> **🔄 Métricas compatibles con Auto Scaling**: No necesitas actualizar dashboards cada vez que se crean nuevas instancias.

---

## 🎯 Problema Resuelto

**Antes**: Si usabas `InstanceId` en tus queries/dashboards, cada vez que Auto Scaling creaba una nueva instancia, tenías que actualizar el ID manualmente.

**Ahora**: Las métricas custom usan dimensión `Service` que automáticamente agrega datos de TODAS las instancias del servicio.

---

## ✅ Dimensiones Automáticas en Métricas Custom

Todas las métricas custom incluyen estas dimensiones automáticamente:

```python
# En cloudwatch_metrics.py
all_dimensions = {
    "Service": self.service_name,      # ← Usa ESTA para Auto Scaling
    "InstanceId": instance_id,         # ← Cambia con cada instancia
    "AvailabilityZone": az,
    "InstanceType": type,
    "Environment": environment
}
```

### Valores de `Service`:

| Aplicación | Valor de Service | Namespace |
|------------|------------------|-----------|
| Backend | `API` | ANB/Backend |
| Worker | `VideoProcessor` | ANB/Worker |

---

## 📊 Queries Compatible con Auto Scaling

### ❌ ANTES (requería actualizar InstanceId):

```bash
aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name RequestDuration \
  --dimensions Name=InstanceId,Value=i-XXXXX \  # ❌ Cambia con Auto Scaling
  --statistics Average
```

### ✅ AHORA (compatible con Auto Scaling):

```bash
aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name RequestDuration \
  --dimensions Name=Service,Value=API \  # ✅ Agrega TODAS las instancias
  --statistics Average \
  --extended-statistics p95
```

---

## 🚀 Uso con Scripts de Reporte

### Script: `generate_load_test_report.sh`

**Variables de entorno**:

```bash
# REQUERIDO (pero con valores por defecto)
export BACKEND_SERVICE="API"                    # Agrega todas las instancias Backend
export WORKER_SERVICE="VideoProcessor"          # Agrega todas las instancias Worker
export SQS_QUEUE_NAME="video-processing-queue"  # Cola SQS

# OPCIONAL (solo para métricas EC2 CPU/Memoria de instancia específica)
export BACKEND_INSTANCE_ID="i-XXXXX"  # Solo si necesitas CPU de instancia específica
export WORKER_INSTANCE_ID="i-YYYYY"   # Solo si necesitas CPU de instancia específica
```

**Ejecución**:

```bash
# Con valores por defecto (compatible con Auto Scaling)
./source/cloudwatch/generate_load_test_report.sh "2025-01-15T10:00:00Z" "2025-01-15T10:30:00Z"

# O especificando servicios personalizados
BACKEND_SERVICE=MyAPI \
WORKER_SERVICE=MyWorker \
./source/cloudwatch/generate_load_test_report.sh "2025-01-15T10:00:00Z" "2025-01-15T10:30:00Z"
```

---

## 📈 Dashboard Compatible con Auto Scaling

### Dashboard JSON (agrega todas las instancias automáticamente):

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "title": "API Latency (All Instances)",
        "metrics": [
          ["ANB/Backend", "RequestDuration", {
            "stat": "p95",
            "dimensions": {"Service": "API"}
          }]
        ],
        "period": 300,
        "region": "us-east-1",
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "API Error Rate (All Instances)",
        "metrics": [
          ["ANB/Backend", "ErrorCount", {
            "stat": "Sum",
            "dimensions": {"Service": "API"},
            "label": "Errors"
          }],
          [".", "RequestCount", {
            "stat": "Sum",
            "dimensions": {"Service": "API"},
            "label": "Requests"
          }]
        ],
        "period": 300,
        "region": "us-east-1"
      }
    },
    {
      "type": "metric",
      "properties": {
        "title": "Worker Throughput (All Instances)",
        "metrics": [
          ["ANB/Worker", "VideoFileSize", {
            "stat": "Sum",
            "dimensions": {"Service": "VideoProcessor"}
          }]
        ],
        "period": 300,
        "region": "us-east-1"
      }
    }
  ]
}
```

**Crear dashboard**:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name ANB-Production-AutoScaling \
  --dashboard-body file://dashboard.json
```

---

## 🔍 Ver Métricas por Instancia Individual (Opcional)

Si necesitas ver métricas de una instancia específica:

```bash
# Listar todas las instancias que están enviando métricas
aws cloudwatch list-metrics \
  --namespace ANB/Backend \
  --metric-name RequestDuration

# Output incluirá todas las combinaciones de dimensiones:
# - Service=API, InstanceId=i-XXX
# - Service=API, InstanceId=i-YYY
# - Service=API, InstanceId=i-ZZZ

# Ver métrica de instancia específica
aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name RequestDuration \
  --dimensions Name=Service,Value=API Name=InstanceId,Value=i-XXXXX \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 300 \
  --statistics Average
```

---

## ⚠️ Métricas EC2 Nativas (Requieren InstanceId)

**Limitación**: Las métricas de AWS/EC2 (CPUUtilization, NetworkIn, etc.) requieren `InstanceId` específico o usar Auto Scaling Group metrics.

### Opción 1: Usar Auto Scaling Group (Recomendado)

```bash
# CPU promedio de TODAS las instancias en el Auto Scaling Group
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=AutoScalingGroupName,Value=anb-backend-asg \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 300 \
  --statistics Average
```

### Opción 2: Listar instancias dinámicamente

```bash
# Script para obtener CPU de todas las instancias activas en Auto Scaling
ASG_NAME="anb-backend-asg"

# Obtener IDs de instancias activas
INSTANCE_IDS=$(aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names "$ASG_NAME" \
  --query 'AutoScalingGroups[0].Instances[?LifecycleState==`InService`].InstanceId' \
  --output text)

# Iterar sobre cada instancia
for INSTANCE_ID in $INSTANCE_IDS; do
    echo "CPU for $INSTANCE_ID:"
    aws cloudwatch get-metric-statistics \
      --namespace AWS/EC2 \
      --metric-name CPUUtilization \
      --dimensions Name=InstanceId,Value="$INSTANCE_ID" \
      --start-time "$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%SZ)" \
      --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      --period 300 \
      --statistics Average \
      --query 'Datapoints[0].Average' \
      --output text
done
```

---

## 📋 Resumen: Métricas Auto Scaling Compatible

| Métrica | Namespace | Dimensión para Auto Scaling | Compatible |
|---------|-----------|------------------------------|------------|
| **Custom Metrics** | | | |
| RequestDuration | ANB/Backend | `Service=API` | ✅ |
| ErrorCount | ANB/Backend | `Service=API` | ✅ |
| RequestCount | ANB/Backend | `Service=API` | ✅ |
| VideoFileSize | ANB/Worker | `Service=VideoProcessor` | ✅ |
| TaskFailure | ANB/Worker | `Service=VideoProcessor` | ✅ |
| **AWS Native Metrics** | | | |
| ApproximateNumberOfMessagesVisible | AWS/SQS | `QueueName=video-processing-queue` | ✅ |
| ApproximateAgeOfOldestMessage | AWS/SQS | `QueueName=video-processing-queue` | ✅ |
| CPUUtilization | AWS/EC2 | `AutoScalingGroupName=anb-backend-asg` | ✅ |
| CPUUtilization | AWS/EC2 | `InstanceId=i-XXXXX` | ⚠️ Requiere ID específico |
| mem_used_percent | CWAgent | `InstanceId=i-XXXXX` | ⚠️ Requiere ID específico |

---

## 🎉 Resultado

**Con Auto Scaling**:
1. Instancia principal (`i-AAA`) envía métricas: `Service=API, InstanceId=i-AAA`
2. Auto Scaling crea nueva instancia (`i-BBB`) → envía métricas: `Service=API, InstanceId=i-BBB`
3. Auto Scaling crea otra instancia (`i-CCC`) → envía métricas: `Service=API, InstanceId=i-CCC`

**Tu dashboard/query con `Service=API`**:
- ✅ Automáticamente agrega métricas de `i-AAA`, `i-BBB`, `i-CCC`
- ✅ No necesitas actualizar nada
- ✅ P95 latency, error rate, throughput son calculados sobre TODAS las instancias

**Beneficios**:
- Dashboard "set and forget"
- Scripts de reporte funcionan sin cambios
- Alarmas de CloudWatch se mantienen válidas
- Compatibilidad con 1 instancia o 100 instancias
