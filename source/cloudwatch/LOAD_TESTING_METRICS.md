# Métricas para Pruebas de Carga - CloudWatch

> **Objetivo**: Mantener los mismos criterios de éxito/fallo de las pruebas de carga usando métricas optimizadas de CloudWatch.

---

## 💰 Opciones de Costos

### Opción A: Custom Metrics Optimizadas (~$0.09/mes)

**Scripts disponibles**:
- `generate_load_test_report.sh` - Reporte completo con métricas custom + AWS nativas

**Métricas incluidas**:
- ✅ p95 latency Backend (custom)
- ✅ Error rate Backend (custom)
- ✅ Throughput Worker MB/min (custom)
- ✅ CPU/Memoria (AWS EC2/CWAgent - FREE)
- ✅ Cola estable (AWS SQS - FREE)

**Costo**: ~$0.09/mes (~$1.62/año)

### Opción B: Solo Métricas FREE ($0 total)

**Scripts disponibles**:
- `generate_free_metrics_report.sh` - Reporte usando SOLO métricas AWS nativas

**Métricas incluidas**:
- ✅ CPU/Memoria (AWS EC2/CWAgent - FREE)
- ✅ Cola estable (AWS SQS - FREE)
- ✅ S3 Errors (AWS S3 - FREE)
- ❌ p95 latency Backend (no disponible sin custom)
- ❌ Error rate Backend granular (no disponible sin custom)

**Costo**: $0/mes

**Para habilitar**: Ver [ZERO_COST_MODE.md](./ZERO_COST_MODE.md)

---

## 📊 BACKEND - Criterios de Éxito/Fallo

### Criterio 1: p95 de endpoints ≤ 1s

**Métrica a usar**: `ANB/Backend: RequestDuration` (custom - ya optimizada con sampling)

#### Query CloudWatch Insights:

```bash
# Obtener p95 de latencia durante prueba de carga
aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name RequestDuration \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Average \
  --extended-statistics p95 \
  --dimensions Name=Method,Value=POST Name=Endpoint,Value=/api/videos

# Resultado esperado: p95 ≤ 1000ms
```

#### Dashboard Widget:

```json
{
  "type": "metric",
  "properties": {
    "metrics": [
      ["ANB/Backend", "RequestDuration", {"stat": "p95", "label": "p95 Latency"}],
      ["...", {"stat": "p99", "label": "p99 Latency"}],
      ["...", {"stat": "Average", "label": "Avg Latency"}]
    ],
    "period": 60,
    "region": "us-east-1",
    "title": "API Latency (Target: p95 ≤ 1000ms)",
    "yAxis": {
      "left": {
        "min": 0,
        "max": 2000,
        "label": "Milliseconds"
      }
    },
    "annotations": {
      "horizontal": [
        {
          "value": 1000,
          "label": "SLA Target (1s)",
          "fill": "above",
          "color": "#ff0000"
        }
      ]
    }
  }
}
```

**✅ Costo**: $0 (incluido en las métricas custom optimizadas - sampling 10-20%)

---

### Criterio 2: Errores (4xx evitables/5xx) ≤ 5%

**Métricas a usar**:
- `ANB/Backend: ErrorCount` (custom - 5xx errors)
- `ANB/Backend: RequestCount` (custom - total requests)
- `ANB/Backend: Success` (custom - 2xx responses)

#### Query CloudWatch Insights:

```bash
# Calcular tasa de error durante prueba de carga
aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name ErrorCount \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 300 \
  --statistics Sum

# Comparar con total de requests
aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name RequestCount \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 300 \
  --statistics Sum

# Cálculo manual: (ErrorCount / RequestCount) * 100 ≤ 5%
```

#### Dashboard Widget (con cálculo automático):

```json
{
  "type": "metric",
  "properties": {
    "metrics": [
      ["ANB/Backend", "ErrorCount", {"id": "m1", "stat": "Sum", "visible": false}],
      [".", "RequestCount", {"id": "m2", "stat": "Sum", "visible": false}],
      [{"expression": "(m1/m2)*100", "label": "Error Rate %", "id": "e1"}]
    ],
    "period": 60,
    "region": "us-east-1",
    "title": "Error Rate (Target: ≤ 5%)",
    "yAxis": {
      "left": {
        "min": 0,
        "max": 10,
        "label": "Percentage"
      }
    },
    "annotations": {
      "horizontal": [
        {
          "value": 5,
          "label": "Max Error Rate (5%)",
          "fill": "above",
          "color": "#ff0000"
        }
      ]
    }
  }
}
```

**Separación por tipo de error** (4xx vs 5xx):

```bash
# Filtrar por StatusCode
aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name ErrorCount \
  --dimensions Name=StatusCode,Value=500 \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 300 \
  --statistics Sum
```

**✅ Costo**: $0 (incluido en métricas custom optimizadas)

---

### Criterio 3: Sin resets/timeouts anómalos ni throttling del almacenamiento

**Métricas FREE a usar**:

#### A) Resets/Timeouts de Red - EC2 Metrics (FREE)

```bash
# Verificar errores de red
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name StatusCheckFailed \
  --dimensions Name=InstanceId,Value=i-XXXXX \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Sum

# NetworkPacketsIn/Out para detectar anomalías
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name NetworkPacketsIn \
  --dimensions Name=InstanceId,Value=i-XXXXX \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Average
```

#### B) Throttling de Almacenamiento S3 (FREE)

**Para S3 (si FILE_STORAGE_TYPE=s3)**:

```bash
# Habilitar métricas de request en bucket S3 (ONE-TIME SETUP)
aws s3api put-bucket-metrics-configuration \
  --bucket anb-video-uploads \
  --id EntireBucket \
  --metrics-configuration Id=EntireBucket

# Verificar errores 4xx/5xx de S3 (throttling = 503)
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name 4xxErrors \
  --dimensions Name=BucketName,Value=anb-video-uploads \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Sum

aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name 5xxErrors \
  --dimensions Name=BucketName,Value=anb-video-uploads \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Sum
```

#### Dashboard Widget:

```json
{
  "type": "metric",
  "properties": {
    "metrics": [
      ["AWS/EC2", "StatusCheckFailed", {"stat": "Sum", "label": "EC2 Health Checks Failed"}],
      ["AWS/S3", "4xxErrors", {"dimensions": {"BucketName": "anb-video-uploads"}, "stat": "Sum", "label": "S3 Client Errors"}],
      ["AWS/S3", "5xxErrors", {"dimensions": {"BucketName": "anb-video-uploads"}, "stat": "Sum", "label": "S3 Server Errors (Throttling)"}]
    ],
    "period": 60,
    "region": "us-east-1",
    "title": "Infrastructure Health (Target: 0 errors)",
    "yAxis": {
      "left": {
        "min": 0
      }
    }
  }
}
```

**✅ Costo**: $0 (métricas nativas EC2/S3 - FREE)

---

### Criterio 4: Primer KPI que se degrada (CPU del API, ancho de banda, etc)

**Métricas FREE a monitorear**:

#### A) CPU del API - EC2 Metrics (FREE)

```bash
# CPU utilization de la instancia backend
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-XXXXX \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Average,Maximum

# Umbral de degradación: >80% CPU
```

#### B) Memoria del API - CloudWatch Agent (FREE)

```bash
# Requiere CloudWatch Agent instalado (ver README.md)
aws cloudwatch get-metric-statistics \
  --namespace CWAgent \
  --metric-name mem_used_percent \
  --dimensions Name=InstanceId,Value=i-XXXXX \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Average,Maximum

# Umbral de degradación: >85% Memory
```

#### C) Ancho de Banda - EC2 Metrics (FREE)

```bash
# NetworkIn (bytes received)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name NetworkIn \
  --dimensions Name=InstanceId,Value=i-XXXXX \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Sum

# NetworkOut (bytes sent)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name NetworkOut \
  --dimensions Name=InstanceId,Value=i-XXXXX \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Sum

# Convertir a MB/s: Sum / 60 / 1024 / 1024
```

#### D) Conexiones de Base de Datos - RDS Metrics (FREE)

```bash
# Database connections
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=anb-postgres \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Average,Maximum

# CPU de la base de datos
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=anb-postgres \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Average,Maximum
```

#### Dashboard Widget (Multi-KPI):

```json
{
  "type": "metric",
  "properties": {
    "metrics": [
      ["AWS/EC2", "CPUUtilization", {"dimensions": {"InstanceId": "i-backend"}, "stat": "Average", "label": "Backend CPU %", "yAxis": "left"}],
      ["CWAgent", "mem_used_percent", {"dimensions": {"InstanceId": "i-backend"}, "stat": "Average", "label": "Backend Memory %", "yAxis": "left"}],
      ["AWS/RDS", "CPUUtilization", {"dimensions": {"DBInstanceIdentifier": "anb-postgres"}, "stat": "Average", "label": "DB CPU %", "yAxis": "left"}],
      ["AWS/RDS", "DatabaseConnections", {"dimensions": {"DBInstanceIdentifier": "anb-postgres"}, "stat": "Average", "label": "DB Connections", "yAxis": "right"}],
      ["AWS/EC2", "NetworkIn", {"dimensions": {"InstanceId": "i-backend"}, "stat": "Sum", "label": "Network In (bytes)", "yAxis": "right"}]
    ],
    "period": 60,
    "region": "us-east-1",
    "title": "Resource Utilization - Identify First Degraded KPI",
    "yAxis": {
      "left": {
        "min": 0,
        "max": 100,
        "label": "Percentage"
      },
      "right": {
        "label": "Count/Bytes"
      }
    },
    "annotations": {
      "horizontal": [
        {
          "value": 80,
          "label": "CPU/Memory Warning (80%)",
          "fill": "above",
          "color": "#ff9900"
        }
      ]
    }
  }
}
```

**✅ Costo**: $0 (todas métricas nativas EC2/RDS/CWAgent - FREE)

---

## 📊 WORKER - Criterios de Éxito/Fallo

### Criterio 1: Capacidad nominal (MB/min)

**Métricas a usar**:
- `ANB/Worker: VideoFileSize` (custom - histogram de tamaños procesados)
- `ANB/Worker: TaskCount` (custom - tareas completadas)
- `ANB/Worker: TaskDuration` (custom - tiempo de procesamiento)

#### Query CloudWatch Insights:

```bash
# Total de bytes procesados
aws cloudwatch get-metric-statistics \
  --namespace ANB/Worker \
  --metric-name VideoFileSize \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 300 \
  --statistics Sum,SampleCount

# Cálculo:
# Capacidad (MB/min) = (Sum in bytes / 1024 / 1024) / (duration in minutes)
# Throughput = SampleCount / (duration in minutes)
```

#### Dashboard Widget:

```json
{
  "type": "metric",
  "properties": {
    "metrics": [
      ["ANB/Worker", "VideoFileSize", {"id": "m1", "stat": "Sum", "visible": false}],
      [".", "TaskCount", {"id": "m2", "stat": "Sum", "dimensions": {"Status": "Success"}, "label": "Videos Processed"}],
      [{"expression": "m1/1024/1024/5", "label": "Throughput (MB/min)", "id": "e1"}]
    ],
    "period": 60,
    "region": "us-east-1",
    "title": "Worker Throughput (MB/min)",
    "yAxis": {
      "left": {
        "min": 0,
        "label": "MB/min"
      }
    }
  }
}
```

**Métricas complementarias (Worker CPU/Memory - FREE)**:

```bash
# CPU del worker (EC2)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-worker \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Average,Maximum

# Memoria del worker (CWAgent)
aws cloudwatch get-metric-statistics \
  --namespace CWAgent \
  --metric-name mem_used_percent \
  --dimensions Name=InstanceId,Value=i-worker \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Average,Maximum
```

**✅ Costo**: $0 (custom metrics ya optimizadas + EC2/CWAgent FREE)

---

### Criterio 2: Estabilidad - Cola no crece sin control (tendencia ~0)

**Métrica FREE a usar**: `AWS/SQS: ApproximateNumberOfMessagesVisible` (100% GRATIS)

#### Query CloudWatch Insights:

```bash
# Profundidad de cola durante prueba de carga
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value=video-processing-queue \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Average,Maximum

# Tendencia esperada: valores estables o decrecientes
# Fallo: valores crecientes continuamente (cola acumulándose)
```

#### Métrica adicional - Latencia de procesamiento (FREE):

```bash
# Edad del mensaje más antiguo (detecta cuellos de botella)
aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateAgeOfOldestMessage \
  --dimensions Name=QueueName,Value=video-processing-queue \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Maximum

# Umbral de alerta: >300 segundos (5 minutos)
```

#### Dashboard Widget:

```json
{
  "type": "metric",
  "properties": {
    "metrics": [
      ["AWS/SQS", "ApproximateNumberOfMessagesVisible", {"dimensions": {"QueueName": "video-processing-queue"}, "stat": "Average", "label": "Queue Depth (Avg)", "yAxis": "left"}],
      ["...", {"stat": "Maximum", "label": "Queue Depth (Max)", "yAxis": "left"}],
      [".", "ApproximateAgeOfOldestMessage", {"dimensions": {"QueueName": "video-processing-queue"}, "stat": "Maximum", "label": "Oldest Message Age (s)", "yAxis": "right"}],
      [".", "NumberOfMessagesReceived", {"dimensions": {"QueueName": "video-processing-queue"}, "stat": "Sum", "label": "Messages Consumed", "yAxis": "right"}]
    ],
    "period": 60,
    "region": "us-east-1",
    "title": "Queue Stability (Target: Trend ~0, Age <300s)",
    "yAxis": {
      "left": {
        "min": 0,
        "label": "Queue Depth"
      },
      "right": {
        "label": "Age (seconds) / Count"
      }
    },
    "annotations": {
      "horizontal": [
        {
          "value": 300,
          "label": "Max Age Warning (5 min)",
          "fill": "above",
          "color": "#ff9900",
          "yAxis": "right"
        }
      ]
    }
  }
}
```

**Cálculo de tendencia** (manual o con CloudWatch Insights):

```bash
# Obtener valores al inicio y final de la prueba
START_DEPTH=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value=video-processing-queue \
  --start-time 2025-01-15T10:00:00Z \
  --end-time 2025-01-15T10:01:00Z \
  --period 60 \
  --statistics Average \
  --query 'Datapoints[0].Average')

END_DEPTH=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value=video-processing-queue \
  --start-time 2025-01-15T10:29:00Z \
  --end-time 2025-01-15T10:30:00Z \
  --period 60 \
  --statistics Average \
  --query 'Datapoints[0].Average')

# Tendencia = END_DEPTH - START_DEPTH
# Criterio éxito: tendencia ≈ 0 (±10%)
```

**✅ Costo**: $0 (métricas SQS nativas - 100% FREE)

---

## 🎯 Dashboard Completo para Pruebas de Carga

### Comando para crear dashboard:

```bash
aws cloudwatch put-dashboard --dashboard-name ANB-LoadTest-Dashboard \
  --dashboard-body file://load_test_dashboard.json
```

### Archivo `load_test_dashboard.json`:

```json
{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["ANB/Backend", "RequestDuration", {"stat": "p95", "label": "p95 Latency"}],
          ["...", {"stat": "p99", "label": "p99 Latency"}],
          ["...", {"stat": "Average", "label": "Avg Latency"}]
        ],
        "period": 60,
        "region": "us-east-1",
        "title": "✅ Backend: p95 Latency (≤1000ms)",
        "yAxis": {"left": {"min": 0, "max": 2000}},
        "annotations": {
          "horizontal": [{"value": 1000, "label": "SLA", "fill": "above", "color": "#ff0000"}]
        }
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["ANB/Backend", "ErrorCount", {"id": "m1", "stat": "Sum", "visible": false}],
          [".", "RequestCount", {"id": "m2", "stat": "Sum", "visible": false}],
          [{"expression": "(m1/m2)*100", "label": "Error Rate %", "id": "e1"}]
        ],
        "period": 60,
        "region": "us-east-1",
        "title": "✅ Backend: Error Rate (≤5%)",
        "yAxis": {"left": {"min": 0, "max": 10}},
        "annotations": {
          "horizontal": [{"value": 5, "label": "Max 5%", "fill": "above", "color": "#ff0000"}]
        }
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/EC2", "CPUUtilization", {"dimensions": {"InstanceId": "i-backend"}, "stat": "Average", "label": "Backend CPU"}],
          ["CWAgent", "mem_used_percent", {"dimensions": {"InstanceId": "i-backend"}, "stat": "Average", "label": "Backend Memory"}],
          ["AWS/RDS", "CPUUtilization", {"dimensions": {"DBInstanceIdentifier": "anb-postgres"}, "stat": "Average", "label": "DB CPU"}]
        ],
        "period": 60,
        "region": "us-east-1",
        "title": "🔍 Backend: Resource Utilization (First to degrade?)",
        "yAxis": {"left": {"min": 0, "max": 100}},
        "annotations": {
          "horizontal": [{"value": 80, "label": "Warning", "fill": "above", "color": "#ff9900"}]
        }
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/S3", "4xxErrors", {"dimensions": {"BucketName": "anb-video-uploads"}, "stat": "Sum"}],
          [".", "5xxErrors", {"dimensions": {"BucketName": "anb-video-uploads"}, "stat": "Sum"}],
          ["AWS/EC2", "StatusCheckFailed", {"dimensions": {"InstanceId": "i-backend"}, "stat": "Sum"}]
        ],
        "period": 60,
        "region": "us-east-1",
        "title": "✅ Backend: Infrastructure Health (0 errors)",
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 12,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["ANB/Worker", "VideoFileSize", {"id": "m1", "stat": "Sum", "visible": false}],
          [".", "TaskCount", {"id": "m2", "stat": "Sum", "dimensions": {"Status": "Success"}, "label": "Videos Processed"}],
          [{"expression": "m1/1024/1024/5", "label": "Throughput (MB/min)", "id": "e1"}]
        ],
        "period": 300,
        "region": "us-east-1",
        "title": "✅ Worker: Capacity (MB/min)",
        "yAxis": {"left": {"min": 0}}
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 12,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/SQS", "ApproximateNumberOfMessagesVisible", {"dimensions": {"QueueName": "video-processing-queue"}, "stat": "Average", "label": "Queue Depth"}],
          [".", "ApproximateAgeOfOldestMessage", {"dimensions": {"QueueName": "video-processing-queue"}, "stat": "Maximum", "label": "Oldest Msg Age (s)", "yAxis": "right"}]
        ],
        "period": 60,
        "region": "us-east-1",
        "title": "✅ Worker: Queue Stability (Trend ~0, Age <300s)",
        "yAxis": {
          "left": {"min": 0, "label": "Queue Depth"},
          "right": {"label": "Age (s)"}
        },
        "annotations": {
          "horizontal": [{"value": 300, "label": "Max Age", "yAxis": "right", "fill": "above", "color": "#ff9900"}]
        }
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 18,
      "width": 24,
      "height": 6,
      "properties": {
        "metrics": [
          ["AWS/EC2", "CPUUtilization", {"dimensions": {"InstanceId": "i-worker"}, "stat": "Average", "label": "Worker CPU"}],
          ["CWAgent", "mem_used_percent", {"dimensions": {"InstanceId": "i-worker"}, "stat": "Average", "label": "Worker Memory"}],
          ["ANB/Worker", "TaskDuration", {"stat": "p95", "label": "Task Duration p95 (s)", "yAxis": "right"}],
          [".", "TaskFailure", {"stat": "Sum", "label": "Failed Tasks", "yAxis": "right"}]
        ],
        "period": 60,
        "region": "us-east-1",
        "title": "🔍 Worker: Resource Utilization & Performance",
        "yAxis": {
          "left": {"min": 0, "max": 100, "label": "CPU/Memory %"},
          "right": {"label": "Duration (s) / Count"}
        }
      }
    }
  ]
}
```

**✅ Costo Total del Dashboard**: $0 (todas métricas FREE o custom optimizadas)

---

## 📋 Checklist Pre-Prueba de Carga

### 1. Habilitar métricas FREE necesarias:

```bash
# ✅ EC2 Detailed Monitoring (si aún no está habilitado)
aws ec2 monitor-instances --instance-ids i-backend i-worker

# ✅ Instalar CloudWatch Agent (para métricas de memoria)
# Ver source/cloudwatch/README.md sección 3

# ✅ Habilitar métricas de S3 (si usas S3)
aws s3api put-bucket-metrics-configuration \
  --bucket anb-video-uploads \
  --id EntireBucket \
  --metrics-configuration Id=EntireBucket

# ✅ Verificar que SQS metrics están disponibles (automático)
aws cloudwatch list-metrics --namespace AWS/SQS
```

### 2. Crear dashboard de pruebas de carga:

```bash
# Editar load_test_dashboard.json con tus IDs de instancia/bucket/queue
# Luego crear:
aws cloudwatch put-dashboard --dashboard-name ANB-LoadTest --dashboard-body file://load_test_dashboard.json
```

### 3. Configurar alarmas críticas:

```bash
# p95 latency >1s
aws cloudwatch put-metric-alarm \
  --alarm-name LoadTest-Latency-Failed \
  --metric-name RequestDuration \
  --namespace ANB/Backend \
  --statistic p95 \
  --period 60 \
  --evaluation-periods 3 \
  --threshold 1000 \
  --comparison-operator GreaterThanThreshold

# Error rate >5%
# (Ver source/cloudwatch/README.md para más alarmas)
```

---

## 📊 Extracción de Resultados Post-Prueba

### Script de reporte automatizado:

```bash
#!/bin/bash
# generate_load_test_report.sh

START_TIME="2025-01-15T10:00:00Z"
END_TIME="2025-01-15T10:30:00Z"
BACKEND_INSTANCE="i-xxxxx"
WORKER_INSTANCE="i-xxxxx"
QUEUE_NAME="video-processing-queue"

echo "=== LOAD TEST REPORT ==="
echo "Period: $START_TIME to $END_TIME"
echo ""

# Backend: p95 Latency
echo "✅ Backend p95 Latency (target: ≤1000ms):"
aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name RequestDuration \
  --start-time $START_TIME \
  --end-time $END_TIME \
  --period 1800 \
  --extended-statistics p95 \
  --query 'Datapoints[0].[ExtendedStatistics.p95]' \
  --output text
echo ""

# Backend: Error Rate
echo "✅ Backend Error Rate (target: ≤5%):"
ERRORS=$(aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name ErrorCount \
  --start-time $START_TIME \
  --end-time $END_TIME \
  --period 1800 \
  --statistics Sum \
  --query 'Datapoints[0].Sum' \
  --output text)

REQUESTS=$(aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name RequestCount \
  --start-time $START_TIME \
  --end-time $END_TIME \
  --period 1800 \
  --statistics Sum \
  --query 'Datapoints[0].Sum' \
  --output text)

ERROR_RATE=$(echo "scale=2; ($ERRORS / $REQUESTS) * 100" | bc)
echo "$ERROR_RATE%"
echo ""

# Backend: CPU Peak
echo "🔍 Backend CPU Peak:"
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=$BACKEND_INSTANCE \
  --start-time $START_TIME \
  --end-time $END_TIME \
  --period 1800 \
  --statistics Maximum \
  --query 'Datapoints[0].Maximum' \
  --output text
echo ""

# Worker: Queue Trend
echo "✅ Worker Queue Stability:"
START_DEPTH=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value=$QUEUE_NAME \
  --start-time $START_TIME \
  --end-time $(date -u -d "$START_TIME + 1 minute" +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Average \
  --query 'Datapoints[0].Average' \
  --output text)

END_DEPTH=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value=$QUEUE_NAME \
  --start-time $(date -u -d "$END_TIME - 1 minute" +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $END_TIME \
  --period 60 \
  --statistics Average \
  --query 'Datapoints[0].Average' \
  --output text)

TREND=$(echo "$END_DEPTH - $START_DEPTH" | bc)
echo "Start: $START_DEPTH | End: $END_DEPTH | Trend: $TREND"
echo ""

# Worker: Throughput
echo "✅ Worker Throughput (MB/min):"
BYTES=$(aws cloudwatch get-metric-statistics \
  --namespace ANB/Worker \
  --metric-name VideoFileSize \
  --start-time $START_TIME \
  --end-time $END_TIME \
  --period 1800 \
  --statistics Sum \
  --query 'Datapoints[0].Sum' \
  --output text)

DURATION=30 # minutos
THROUGHPUT=$(echo "scale=2; ($BYTES / 1024 / 1024) / $DURATION" | bc)
echo "$THROUGHPUT MB/min"
echo ""

echo "=== END REPORT ==="
```

**Uso**:
```bash
chmod +x generate_load_test_report.sh
./generate_load_test_report.sh > load_test_results.txt
```

---

## 💰 Resumen de Costos

| Métrica/Dashboard | Tipo | Costo |
|-------------------|------|-------|
| Backend p95 Latency | Custom (optimizada) | $0 (incluido) |
| Backend Error Rate | Custom (optimizada) | $0 (incluido) |
| EC2 CPU/Memory/Network | AWS Native | $0 (FREE) |
| RDS CPU/Connections | AWS Native | $0 (FREE) |
| S3 Errors/Throttling | AWS Native | $0 (FREE) |
| SQS Queue Depth/Age | AWS Native | $0 (FREE) |
| Worker Throughput | Custom (optimizada) | $0 (incluido) |
| CloudWatch Dashboard | AWS Service | $0 (FREE - primeros 3) |
| CloudWatch Alarms | AWS Service | $0 (FREE - primeros 10) |
| **TOTAL** | | **$0.00** |

---

## 🎓 Conclusión

**Todos los criterios de pruebas de carga se pueden medir con métricas FREE** (o custom ya optimizadas):

✅ **Backend**:
- p95 ≤ 1s → `ANB/Backend: RequestDuration` (custom optimizada)
- Errores ≤ 5% → `ANB/Backend: ErrorCount / RequestCount` (custom optimizada)
- Sin throttling → `AWS/S3: 5xxErrors` + `AWS/EC2: StatusCheckFailed` (FREE)
- Primer KPI degradado → `AWS/EC2: CPUUtilization`, `CWAgent: mem_used_percent`, `AWS/RDS: CPUUtilization` (FREE)

✅ **Worker**:
- Capacidad MB/min → `ANB/Worker: VideoFileSize` (custom optimizada)
- Cola estable → `AWS/SQS: ApproximateNumberOfMessagesVisible` (FREE)

**No necesitas pagar nada adicional para mantener tus KPIs de pruebas de carga.** 🚀
