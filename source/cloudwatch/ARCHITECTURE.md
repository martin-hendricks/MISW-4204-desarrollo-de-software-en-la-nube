# Arquitectura de Métricas CloudWatch

## 📚 Propósito de cloudwatch_metrics.py

`cloudwatch_metrics.py` es el **módulo core** que implementa la publicación de métricas a CloudWatch usando **Embedded Metric Format (EMF)**.

### ¿Qué es EMF (Embedded Metric Format)?

EMF es un formato JSON especial que permite enviar métricas a CloudWatch a través de **logs estructurados** en lugar de llamadas API directas.

#### Ventajas de EMF:

1. **Zero Latency**: No bloquea tu aplicación esperando respuestas de AWS API
2. **Más Económico**: Menos llamadas API = menos costos
3. **Batch Automático**: Múltiples métricas en un solo log
4. **Compatible con Lambda/ECS/EC2**: Funciona en cualquier entorno AWS
5. **Async por defecto**: Solo escribe a stdout, CloudWatch Agent lo procesa

#### Ejemplo de EMF JSON:

```json
{
  "_aws": {
    "Timestamp": 1673456789000,
    "CloudWatchMetrics": [
      {
        "Namespace": "ANB/Backend",
        "Dimensions": [["Method", "Endpoint", "StatusCode"]],
        "Metrics": [
          {"Name": "RequestDuration", "Unit": "Milliseconds"},
          {"Name": "RequestCount", "Unit": "Count"}
        ]
      }
    ]
  },
  "Method": "POST",
  "Endpoint": "/api/videos",
  "StatusCode": "200",
  "RequestDuration": 345.67,
  "RequestCount": 1,
  "InstanceId": "i-xxxxxxxxx",
  "Service": "API",
  "Environment": "production"
}
```

Cuando tu aplicación escribe este JSON a `stdout`, **CloudWatch lo detecta automáticamente** y crea las métricas.

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    TU APLICACIÓN                            │
│  ┌────────────────┐              ┌──────────────┐           │
│  │  Backend API   │              │    Worker    │           │
│  │  (FastAPI)     │              │   (Celery)   │           │
│  └────────┬───────┘              └──────┬───────┘           │
│           │                             │                   │
│           │   import cloudwatch_metrics │                   │
│           └─────────────────────────────┘                   │
│                         │                                   │
│                         ▼                                   │
│         ┌───────────────────────────────┐                   │
│         │  cloudwatch_metrics.py        │                   │
│         │  ┌─────────────────────────┐  │                   │
│         │  │ CloudWatchMetrics class │  │                   │
│         │  │                         │  │                   │
│         │  │ • put_metric()          │  │                   │
│         │  │ • put_metrics()         │  │                   │
│         │  │ • EMF JSON generator    │  │                   │
│         │  │ • Auto EC2 metadata     │  │                   │
│         │  └─────────────────────────┘  │                   │
│         └───────────────┬───────────────┘                   │
│                         │                                   │
│                         ▼                                   │
│                   print(emf_json)  ← Escribe a stdout       │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  Docker Container      │
              │  stdout/stderr         │
              └────────────┬───────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  CloudWatch Logs       │  ← Captura automática
              │  (Log Group)           │
              └────────────┬───────────┘
                          │
                          │  CloudWatch detecta EMF
                          │  en los logs
                          ▼
              ┌────────────────────────┐
              │  CloudWatch Metrics    │  ← Métricas disponibles
              │  Namespace: ANB/xxx    │
              └────────────────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  CloudWatch Dashboards │  ← Visualización
              │  CloudWatch Alarms     │  ← Alertas
              └────────────────────────┘
```

---

## 🔧 Funciones Principales de cloudwatch_metrics.py

### 1. `CloudWatchMetrics.__init__(namespace, service_name)`

Inicializa el cliente de métricas.

**Parámetros:**
- `namespace`: Nombre del namespace en CloudWatch (ej: "ANB/Backend", "ANB/Worker")
- `service_name`: Identificador del servicio (ej: "API", "VideoProcessor")

**Qué hace automáticamente:**
- Detecta metadata de EC2 (InstanceId, AvailabilityZone, InstanceType)
- Configura logging
- Agrega dimensiones por defecto (Service, Environment, InstanceId)

**Ejemplo:**
```python
from cloudwatch.cloudwatch_metrics import CloudWatchMetrics, MetricUnit

cw_metrics = CloudWatchMetrics(
    namespace="ANB/Backend",
    service_name="API"
)
```

---

### 2. `put_metric(name, value, unit, dimensions={})`

Publica **una sola métrica**.

**Parámetros:**
- `name`: Nombre de la métrica (ej: "RequestDuration")
- `value`: Valor numérico
- `unit`: Unidad (ej: `MetricUnit.MILLISECONDS`)
- `dimensions`: Dict con dimensiones adicionales

**Ejemplo:**
```python
cw_metrics.put_metric(
    name="RequestDuration",
    value=345.67,
    unit=MetricUnit.MILLISECONDS,
    dimensions={
        "Method": "POST",
        "Endpoint": "/api/videos",
        "StatusCode": "200"
    }
)
```

**Salida (stdout):**
```json
{"_aws": {...}, "RequestDuration": 345.67, "Method": "POST", ...}
```

---

### 3. `put_metrics(metrics, dimensions={})`

Publica **múltiples métricas en un solo batch** (más eficiente).

**Parámetros:**
- `metrics`: Lista de dicts con `name`, `value`, `unit`
- `dimensions`: Dict con dimensiones compartidas

**Ejemplo:**
```python
cw_metrics.put_metrics(
    metrics=[
        {"name": "RequestCount", "value": 1, "unit": MetricUnit.COUNT},
        {"name": "RequestDuration", "value": 345.67, "unit": MetricUnit.MILLISECONDS},
        {"name": "ErrorCount", "value": 0, "unit": MetricUnit.COUNT}
    ],
    dimensions={
        "Method": "POST",
        "Endpoint": "/api/videos",
        "StatusCode": "200"
    }
)
```

**Ventaja:** 3 métricas en 1 solo log EMF = más eficiente

---

### 4. `_get_instance_metadata()`

Obtiene automáticamente información de la instancia EC2.

**Qué detecta:**
- `InstanceId`: ID de la instancia EC2 (ej: "i-0abc123...")
- `AvailabilityZone`: Zona de disponibilidad (ej: "us-east-1a")
- `InstanceType`: Tipo de instancia (ej: "t2.micro")
- `Environment`: Variable de entorno `ENVIRONMENT` (ej: "production")

**Cómo funciona:**
1. Intenta conectarse a EC2 Instance Metadata Service (IMDS v2)
2. Si falla (local/docker), usa valores por defecto (hostname)
3. Agrega estas dimensiones **automáticamente** a todas las métricas

**Fallback seguro:**
- Si no está en EC2: usa hostname del sistema
- Si no hay network: valores "unknown"

---

## 🔐 Seguridad y Privacidad

### ✅ Datos que SÍ se envían (seguros):

- Nombres de métricas (RequestDuration, TaskCount, etc.)
- Valores numéricos (latencias, contadores)
- Dimensiones genéricas (Method, StatusCode, TaskName)
- Metadata de EC2 (InstanceId, AZ) - **pública dentro de tu cuenta AWS**

### ❌ Datos que NO se envían:

- IPs de usuarios
- Datos de sesión/cookies
- Contenido de requests/responses
- Información personal identificable (PII)
- Credenciales o tokens
- Datos de videos o archivos

### 🔒 Mejores Prácticas Implementadas:

1. **No exponer PII**: Solo métricas agregadas
2. **Dimensiones limitadas**: Solo metadatos técnicos
3. **No logging de payloads**: Solo duración/códigos de estado
4. **Metadata segura**: InstanceId es seguro (solo tú puedes verlo)

---

## 📊 Flujo de una Métrica

### Backend Example:

```python
# 1. Usuario hace request: POST /api/videos
# 2. Middleware captura inicio: start_time = time.time()
# 3. FastAPI procesa request...
# 4. Middleware calcula duración: duration_ms = (time.time() - start_time) * 1000
# 5. Middleware llama CloudWatchMetrics:

cw_metrics.put_metrics(
    metrics=[
        {"name": "RequestCount", "value": 1, "unit": MetricUnit.COUNT},
        {"name": "RequestDuration", "value": duration_ms, "unit": MetricUnit.MILLISECONDS},
        {"name": "ErrorCount", "value": 0, "unit": MetricUnit.COUNT}
    ],
    dimensions={
        "Method": "POST",
        "Endpoint": "/api/videos",  # ← NO incluye parámetros ni query strings
        "StatusCode": "200"
    }
)

# 6. cloudwatch_metrics.py genera JSON EMF
# 7. print(json_emf) → stdout
# 8. Docker captura stdout → CloudWatch Logs
# 9. CloudWatch detecta EMF → crea métricas
# 10. Disponible en dashboard en ~2-3 minutos
```

---

## 🎯 Uso en el Proyecto

### Backend (source/backend/app/main.py):

```python
# Inicialización
cw_metrics = CloudWatchMetrics(
    namespace="ANB/Backend",
    service_name="API"
)

# Middleware HTTP
@app.middleware("http")
async def cloudwatch_middleware(request, call_next):
    # Sampling para /health (10%)
    if request.url.path == "/health" and random.random() > 0.1:
        return await call_next(request)

    # Capturar métricas de todas las requests
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000

    cw_metrics.put_metrics(
        metrics=[...],
        dimensions={
            "Method": request.method,
            "Endpoint": request.url.path,  # Solo path, NO query params
            "StatusCode": str(response.status_code)
        }
    )

    return response

# Heartbeat cada 5 minutos
async def publish_heartbeat():
    while True:
        await asyncio.sleep(300)
        cw_metrics.put_metrics(
            metrics=[{"name": "ServiceHeartbeat", "value": 1, "unit": MetricUnit.COUNT}],
            dimensions={"MetricType": "Health"}
        )
```

### Worker (source/worker/celery_app.py):

```python
# Inicialización (en metrics.py)
cw_metrics = CloudWatchMetrics(
    namespace="ANB/Worker",
    service_name="VideoProcessor"
)

# Celery signal: task success
@task_success.connect
def task_success_handler(sender=None, result=None, **kwargs):
    cw_metrics.put_metrics(
        metrics=[
            {"name": "TaskCount", "value": 1, "unit": MetricUnit.COUNT}
        ],
        dimensions={
            "TaskName": sender.name,
            "Status": "Success"
        }
    )

# Celery signal: task failure
@task_failure.connect
def task_failure_handler(sender=None, exception=None, **kwargs):
    cw_metrics.put_metrics(
        metrics=[
            {"name": "TaskCount", "value": 1, "unit": MetricUnit.COUNT},
            {"name": "TaskFailure", "value": 1, "unit": MetricUnit.COUNT}
        ],
        dimensions={
            "TaskName": sender.name,
            "Status": "Failed",
            "ErrorType": type(exception).__name__  # Solo tipo de error, NO mensaje
        }
    )
```

---

## 🚀 Cómo Usar generate_load_test_report.sh

### 1. Configurar Variables de Entorno

```bash
# NO hardcodear en el script!
export BACKEND_INSTANCE_ID="i-xxxxxxxxxxxx"  # Tu instancia backend
export WORKER_INSTANCE_ID="i-yyyyyyyyyyyy"   # Tu instancia worker
export SQS_QUEUE_NAME="video-processing-queue"
export DB_INSTANCE_ID="anb-postgres-db"
export AWS_REGION="us-east-1"
```

### 2. Ejecutar el Script

```bash
# Dar permisos de ejecución
chmod +x source/cloudwatch/generate_load_test_report.sh

# Uso básico (últimos 30 minutos)
./source/cloudwatch/generate_load_test_report.sh

# Especificar periodo exacto
./source/cloudwatch/generate_load_test_report.sh \
  "2025-01-15T10:00:00Z" \
  "2025-01-15T10:30:00Z"

# Guardar reporte
./source/cloudwatch/generate_load_test_report.sh > load_test_results.txt
```

### 3. Salida del Script

```
=============================================
    LOAD TEST REPORT - CloudWatch Metrics
=============================================
Period: 2025-01-15T10:00:00Z to 2025-01-15T10:30:00Z
Region: us-east-1

=== BACKEND METRICS ===

✅ Backend p95 Latency (target: ≤1000ms): 876.3ms PASS ✅

✅ Backend Error Rate (target: ≤5%): 1.2% (12/1000) PASS ✅

🔍 Backend CPU Peak: 65.4% (healthy) ✅

✅ Backend S3 Errors (target: 0): 0 errors PASS ✅

=== WORKER METRICS ===

✅ Worker Queue Stability (target: trend ~0):
  Start Queue Depth: 15
  End Queue Depth: 3
  Trend: -12 (stable) PASS ✅

✅ Worker Throughput (MB/min): 45.6 MB/min

✅ Worker Failed Tasks: 0 failures PASS ✅

=============================================
    END REPORT
=============================================
```

---

## 📁 Estructura de Archivos

```
source/cloudwatch/
├── cloudwatch_metrics.py          # ← Core EMF implementation
├── README.md                       # ← Setup y configuración general
├── LOAD_TESTING_METRICS.md        # ← Guía de pruebas de carga
├── ARCHITECTURE.md                 # ← Este documento (arquitectura)
└── generate_load_test_report.sh   # ← Script de reporte

source/backend/app/
└── main.py                         # ← Usa cloudwatch_metrics para API

source/worker/
├── metrics.py                      # ← Inicializa cloudwatch_metrics
├── celery_app.py                   # ← Hooks de Celery con métricas
└── main.py                         # ← Health API con heartbeat
```

---

## 🔍 Debugging

### Ver logs EMF en tiempo real:

```bash
# Backend
docker logs -f anb-backend | grep '_aws'

# Worker
docker logs -f anb-worker | grep '_aws'
```

### Verificar que las métricas llegan a CloudWatch:

```bash
# Listar métricas disponibles
aws cloudwatch list-metrics --namespace ANB/Backend
aws cloudwatch list-metrics --namespace ANB/Worker

# Ver valores de una métrica
aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name RequestDuration \
  --start-time $(date -u -d '10 minutes ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Average
```

---

## 💡 Preguntas Frecuentes

### ¿Por qué usar EMF en vez de boto3 put_metric_data()?

**EMF (Recomendado)**:
- ✅ Zero latency (async)
- ✅ Más económico
- ✅ Batch automático
- ✅ Compatible con Lambda/ECS

**boto3 (No recomendado)**:
- ❌ Bloquea tu app esperando API
- ❌ Más caro (más llamadas API)
- ❌ Necesitas hacer batch manual
- ❌ Requiere credenciales configuradas

### ¿Los logs EMF cuentan para el costo de CloudWatch Logs?

**Sí**, pero es mínimo:
- Logs EMF: ~200 bytes por métrica
- 10,000 requests/día = ~2 MB/día = ~60 MB/mes
- Costo: 60 MB × $0.50/GB = **$0.03/mes**

Es mucho más barato que métricas custom directas!

### ¿Puedo ver los logs EMF en CloudWatch Logs?

Sí! Van a:
- `/aws/ecs/containerinsights/{cluster-name}` (si usas ECS)
- Log group de tu aplicación (si usas EC2/Docker)

Pero **no necesitas** leer los logs, las métricas se extraen automáticamente.

---

## 🎓 Conclusión

`cloudwatch_metrics.py` es tu **puente eficiente** entre la aplicación y CloudWatch:

1. Tu app llama `put_metrics()`
2. Se genera JSON EMF
3. Se escribe a stdout (log)
4. CloudWatch lo detecta
5. Métricas disponibles automáticamente

**Todo esto sin:**
- ❌ Llamadas API síncronas
- ❌ Latencia adicional
- ❌ Credenciales hardcodeadas
- ❌ Exponer información sensible

🚀 Simple, seguro y eficiente!
