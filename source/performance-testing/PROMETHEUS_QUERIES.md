# Queries de Prometheus para KPIs de Pruebas de Rendimiento

## 1. BACKEND API - Escenarios JMeter

### 1.1 Latencia (p95 ≤ 1s)

**Percentil 95 de latencia de todos los endpoints:**
```promql
histogram_quantile(0.95,
  rate(http_request_duration_highr_seconds_bucket[1m])
)
```

**Percentil 95 por endpoint específico:**
```promql
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket{handler="/api/videos"}[1m])
)
```

**Percentil 99 (para análisis de outliers):**
```promql
histogram_quantile(0.99,
  rate(http_request_duration_highr_seconds_bucket[1m])
)
```

### 1.2 Tasa de Errores (≤ 5%)

**Porcentaje de errores 4xx y 5xx:**
```promql
100 * (
  sum(rate(http_requests_total{status=~"4..|5.."}[1m]))
  /
  sum(rate(http_requests_total[1m]))
)
```

**Desglose por tipo de error:**
```promql
sum by (status) (
  rate(http_requests_total{status=~"4..|5.."}[1m])
)
```

**Errores 5xx solamente (errores del servidor):**
```promql
sum(rate(http_requests_total{status=~"5.."}[1m]))
```

### 1.3 RPS (Requests por Segundo)

**RPS total:**
```promql
sum(rate(http_requests_total[1m]))
```

**RPS por endpoint:**
```promql
sum by (handler) (
  rate(http_requests_total[1m])
)
```

**RPS sostenido en ventana de 5 minutos:**
```promql
sum(rate(http_requests_total[5m]))
```

### 1.4 Usuarios Concurrentes

**Requests en progreso (aproximación de usuarios concurrentes):**
```promql
fastapi_inprogress
```

**Máximo de requests concurrentes en la última hora:**
```promql
max_over_time(fastapi_inprogress[1h])
```

### 1.5 Recursos del Backend

**Uso de CPU (% aproximado):**
```promql
rate(process_cpu_seconds_total{job="backend-api"}[1m]) * 100
```

**Uso de memoria (MB):**
```promql
process_resident_memory_bytes{job="backend-api"} / 1024 / 1024
```

**Memoria virtual:**
```promql
process_virtual_memory_bytes{job="backend-api"} / 1024 / 1024
```

### 1.6 Curva Usuarios → Latencia

**Para graficar en Grafana (latencia vs tiempo):**
```promql
# Eje Y: Latencia p95
histogram_quantile(0.95, rate(http_request_duration_highr_seconds_bucket[1m]))

# Eje Y secundario: Usuarios concurrentes
fastapi_inprogress
```

---

## 2. WORKER - Procesamiento de Videos

### 2.1 Throughput (videos procesados/minuto)

**Videos procesados por minuto:**
```promql
rate(celery_tasks_total{task_name="process_video", status="success"}[1m]) * 60
```

**Videos procesados en los últimos 5 minutos:**
```promql
increase(celery_tasks_total{task_name="process_video", status="success"}[5m])
```

**Throughput promedio en ventana de 10 minutos:**
```promql
rate(celery_tasks_total{task_name="process_video", status="success"}[10m]) * 60
```

### 2.2 Tiempo Medio de Servicio (S)

**Duración promedio de procesamiento:**
```promql
rate(celery_task_duration_seconds_sum{task_name="process_video"}[5m])
/
rate(celery_task_duration_seconds_count{task_name="process_video"}[5m])
```

**Percentil 50 (mediana):**
```promql
histogram_quantile(0.50,
  rate(celery_task_duration_seconds_bucket{task_name="process_video"}[5m])
)
```

**Percentil 95:**
```promql
histogram_quantile(0.95,
  rate(celery_task_duration_seconds_bucket{task_name="process_video"}[5m])
)
```

### 2.3 Tamaño de Cola (estabilidad)

**Tamaño actual de la cola de videos:**
```promql
celery_queue_length{queue_name="video_processing"}
```

**Tamaño de Dead Letter Queue:**
```promql
celery_queue_length{queue_name="dlq"}
```

**Tendencia de la cola (crecimiento por minuto):**
```promql
deriv(celery_queue_length{queue_name="video_processing"}[5m]) * 60
```

**Alerta: Cola creciendo sin control (pendiente > 0):**
```promql
deriv(celery_queue_length{queue_name="video_processing"}[10m]) > 0
```

### 2.4 Tareas Activas y Reservadas

**Tareas en ejecución:**
```promql
celery_active_tasks
```

**Tareas esperando ejecución:**
```promql
celery_reserved_tasks
```

**Utilización del worker (%):**
```promql
(celery_active_tasks / 4) * 100  # 4 = CELERY_CONCURRENCY
```

### 2.5 Tasa de Fallos

**Porcentaje de videos fallidos:**
```promql
100 * (
  sum(rate(celery_tasks_total{task_name="process_video", status="failed"}[5m]))
  /
  sum(rate(celery_tasks_total{task_name="process_video"}[5m]))
)
```

**Total de fallos:**
```promql
sum(rate(celery_tasks_failed_total{task_name="process_video"}[5m]))
```

**Fallos por tipo de error:**
```promql
sum by (error_type) (
  rate(celery_tasks_failed_total{task_name="process_video"}[5m])
)
```

### 2.6 Tamaño de Videos Procesados

**Distribución de tamaños de archivos:**
```promql
rate(video_file_size_bytes_bucket[5m])
```

**Tamaño promedio de videos (MB):**
```promql
(
  rate(video_file_size_bytes_sum[5m])
  /
  rate(video_file_size_bytes_count[5m])
) / 1024 / 1024
```

**Percentil 95 de tamaño (MB):**
```promql
histogram_quantile(0.95, rate(video_file_size_bytes_bucket[5m])) / 1024 / 1024
```

### 2.7 Recursos del Worker

**CPU del worker (%):**
```promql
rate(process_cpu_seconds_total{job="worker"}[1m]) * 100
```

**Memoria del worker (MB):**
```promql
process_resident_memory_bytes{job="worker"} / 1024 / 1024
```

---

## 3. FÓRMULAS PARA REPORTES

### 3.1 Capacidad Máxima del Backend

**Criterio: RPS sostenido con p95 ≤ 1s y errores ≤ 5%**

```promql
# Verificar si se cumple el criterio
(
  histogram_quantile(0.95, rate(http_request_duration_highr_seconds_bucket[5m])) <= 1
)
and
(
  100 * (sum(rate(http_requests_total{status=~"4..|5.."}[5m])) / sum(rate(http_requests_total[5m]))) <= 5
)
```

Si retorna `1`, se cumple. Si retorna `0`, hay degradación.

### 3.2 Capacidad Nominal del Worker

**Videos/minuto sostenidos:**

```promql
# Throughput en ventana de 5 minutos
rate(celery_tasks_total{task_name="process_video", status="success"}[5m]) * 60

# Con estabilidad de cola (pendiente ~0)
(rate(celery_tasks_total{task_name="process_video", status="success"}[5m]) * 60)
and
(abs(deriv(celery_queue_length{queue_name="video_processing"}[5m]) * 60) < 0.1)
```

### 3.3 Bottleneck Detection

**CPU saturado (>90%):**
```promql
rate(process_cpu_seconds_total[1m]) * 100 > 90
```

**Cola creciendo (posible saturación):**
```promql
increase(celery_queue_length{queue_name="video_processing"}[5m]) > 10
```

**Latencia degradada:**
```promql
histogram_quantile(0.95, rate(http_request_duration_highr_seconds_bucket[1m])) > 1
```

---

## 4. QUERIES PARA GRAFANA DASHBOARDS

### Dashboard 1: Backend Performance

**Panel 1 - Latencia p95 (Time Series):**
```promql
histogram_quantile(0.95, sum(rate(http_request_duration_highr_seconds_bucket[1m])) by (le))
```

**Panel 2 - RPS (Time Series):**
```promql
sum(rate(http_requests_total[1m]))
```

**Panel 3 - Tasa de Errores (Gauge):**
```promql
100 * (sum(rate(http_requests_total{status=~"4..|5.."}[1m])) / sum(rate(http_requests_total[1m])))
```

**Panel 4 - Usuarios Concurrentes (Time Series):**
```promql
fastapi_inprogress
```

**Panel 5 - CPU/Memoria (Time Series):**
```promql
# CPU
rate(process_cpu_seconds_total{job="backend-api"}[1m]) * 100

# Memoria
process_resident_memory_bytes{job="backend-api"} / 1024 / 1024
```

### Dashboard 2: Worker Performance

**Panel 1 - Throughput (Gauge):**
```promql
rate(celery_tasks_total{task_name="process_video", status="success"}[1m]) * 60
```

**Panel 2 - Duración Promedio (Time Series):**
```promql
rate(celery_task_duration_seconds_sum{task_name="process_video"}[5m]) / rate(celery_task_duration_seconds_count{task_name="process_video"}[5m])
```

**Panel 3 - Tamaño de Cola (Time Series):**
```promql
celery_queue_length{queue_name="video_processing"}
```

**Panel 4 - Tareas Activas (Time Series):**
```promql
celery_active_tasks
```

**Panel 5 - Tasa de Fallos (Gauge):**
```promql
100 * (sum(rate(celery_tasks_total{task_name="process_video", status="failed"}[5m])) / sum(rate(celery_tasks_total{task_name="process_video"}[5m])))
```

---

## 5. ALERTAS RECOMENDADAS

### Backend Alerts

```yaml
# Latencia alta
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_highr_seconds_bucket[5m])) > 1
  for: 2m
  annotations:
    summary: "p95 latency above 1s"

# Alta tasa de errores
- alert: HighErrorRate
  expr: 100 * (sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) > 5
  for: 2m
  annotations:
    summary: "Error rate above 5%"
```

### Worker Alerts

```yaml
# Cola creciendo sin control
- alert: QueueGrowing
  expr: deriv(celery_queue_length{queue_name="video_processing"}[10m]) > 1
  for: 5m
  annotations:
    summary: "Queue growing faster than processing"

# Workers saturados
- alert: WorkerSaturated
  expr: celery_active_tasks >= 4
  for: 10m
  annotations:
    summary: "All workers busy for 10+ minutes"
```

---

## Uso de estas queries:

1. **En Prometheus UI** (http://localhost:9090):
   - Pega la query directamente en el campo de búsqueda
   - Cambia de "Table" a "Graph" para visualizar

2. **En Grafana** (http://localhost:3000):
   - Crea un nuevo panel
   - Selecciona "Prometheus" como datasource
   - Pega la query en el campo "Metrics browser"

3. **Para pruebas JMeter**:
   - Ejecuta JMeter
   - Monitorea en tiempo real con las queries de "Backend Performance"
   - Al finalizar, calcula promedios con ventanas de tiempo más largas (5m, 10m)

4. **Para pruebas de Worker**:
   - Sube videos a la cola
   - Monitorea throughput y cola en tiempo real
   - Verifica que la tendencia de la cola sea ~0 (estable)
