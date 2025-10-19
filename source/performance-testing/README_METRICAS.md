# Guía Completa de Métricas y Monitoreo

## 🚀 Inicio Rápido

### 1. Levantar todos los servicios

```bash
# Terminal 1: Servicios principales
cd source
docker-compose up -d

# Terminal 2: Stack de testing (Prometheus + Grafana + JMeter)
cd performance-testing
docker-compose -f docker-compose.testing.yml up -d
```

### 2. Verificar que todo está funcionando

**Backend API:**
```bash
curl http://localhost:8000/metrics | grep http_requests_total
# Debería mostrar métricas
```

**Worker:**
```bash
curl http://localhost:8001/metrics | grep celery
# Debería mostrar métricas de Celery
```

**Prometheus:**
- Abrir: http://localhost:9090
- Ir a "Status" → "Targets"
- Verificar que `backend-api` y `worker` estén **UP** (verde)

**Grafana:**
- Abrir: http://localhost:3000
- Login: `admin` / `admin`
- Ir a **Dashboards** → **Browse**
- Deberías ver 2 dashboards:
  - Backend API Performance
  - Worker Performance - Video Processing

---

## 📊 Métricas Disponibles

### Backend API (puerto 8000)

| Métrica | Descripción | Labels |
|---------|-------------|--------|
| `http_requests_total` | Total de requests HTTP | method, endpoint, status |
| `http_request_duration_seconds` | Duración de requests (histogram) | method, endpoint |
| `process_cpu_seconds_total` | CPU del proceso | - |
| `process_resident_memory_bytes` | Memoria RAM usada | - |

**Ejemplo de queries en Prometheus:**
```promql
# RPS total
rate(http_requests_total[1m])

# Latencia p95
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[1m])) by (le))

# Tasa de errores 5xx
100 * (
  sum(rate(http_requests_total{status=~"5.."}[1m]))
  /
  sum(rate(http_requests_total[1m]))
)
```

### Worker (puerto 8001)

| Métrica | Descripción | Labels |
|---------|-------------|--------|
| `celery_tasks_total` | Total de tareas procesadas | task_name, status |
| `celery_tasks_failed_total` | Tareas fallidas | task_name, error_type |
| `celery_task_duration_seconds` | Duración de tareas (histogram) | task_name |
| `celery_queue_length` | Tamaño de cola Redis | queue_name |
| `celery_active_tasks` | Workers activos ahora | - |
| `celery_reserved_tasks` | Tareas reservadas | - |
| `video_file_size_bytes` | Tamaño de videos (histogram) | - |

**Ejemplo de queries en Prometheus:**
```promql
# Throughput (videos/min)
rate(celery_tasks_total{task_name="process_video", status="success"}[1m]) * 60

# Tiempo medio de servicio
rate(celery_task_duration_seconds_sum{task_name="process_video"}[5m])
/
rate(celery_task_duration_seconds_count{task_name="process_video"}[5m])

# Tamaño de cola
celery_queue_length{queue_name="video_processing"}

# Tendencia de la cola (debe ser ~0)
deriv(celery_queue_length{queue_name="video_processing"}[5m]) * 60
```

---

## 🎯 KPIs para Pruebas de Rendimiento

### Backend API - Escenarios JMeter

**Criterios de éxito:**
- p95 latencia ≤ 1s
- Errores 5xx ≤ 5%
- Sin timeouts anómalos

**Métricas clave:**
1. **RPS sostenido** - `rate(http_requests_total[1m])`
2. **Latencia p95** - Ver query arriba
3. **Tasa de errores** - Ver query arriba
4. **Usuarios concurrentes** - `http_requests_in_progress`
5. **CPU** - `rate(process_cpu_seconds_total{job="backend-api"}[1m]) * 100`

### Worker - Procesamiento de Videos

**Criterios de éxito:**
- Cola estable (tendencia ~0)
- Throughput constante
- Sin crecimiento descontrolado

**Métricas clave:**
1. **Throughput** - Videos/minuto
2. **Tiempo medio S** - Duración promedio
3. **Tamaño de cola** - Debe mantenerse estable
4. **Tendencia de cola** - Debe ser cercana a 0

---

## 🔧 Troubleshooting

### Problema: No veo métricas en Grafana

**Solución:**
```bash
# 1. Verificar que Prometheus está scrapeando
curl http://localhost:9090/api/v1/targets

# 2. Ver targets en el navegador
# http://localhost:9090/targets
# backend-api y worker deben estar UP

# 3. Generar tráfico
for i in {1..50}; do
  curl -s http://localhost/api/health > /dev/null
done

# 4. Verificar métricas en Prometheus
# http://localhost:9090/graph
# Query: rate(http_requests_total[1m])
```

### Problema: Dashboards no aparecen en Grafana

**Solución:**
```bash
# 1. Eliminar volúmenes y empezar de cero
cd performance-testing
docker-compose -f docker-compose.testing.yml down -v

# 2. Verificar que los archivos existen
ls -la grafana/provisioning/dashboards/
# Deben aparecer:
# - backend_performance.json
# - worker_performance.json
# - dashboard.yml

# 3. Levantar de nuevo
docker-compose -f docker-compose.testing.yml up -d

# 4. Esperar 30 segundos y acceder
# http://localhost:3000 (admin/admin)
```

### Problema: Métricas en cero

**Backend:**
```bash
# Generar tráfico real
for i in {1..100}; do
  curl -s http://localhost/api/config > /dev/null
  curl -s http://localhost/api/health > /dev/null
done

# Verificar que aparecen
curl http://localhost:8000/metrics | grep http_requests_total
```

**Worker:**
```bash
# Las métricas de Celery solo aparecen cuando hay tareas
# Sube un video para que se procese
# O verifica métricas de cola
curl http://localhost:8001/metrics | grep celery_queue_length
```

---

## 📁 Archivos del Proyecto

### Métricas del Backend
**Archivo:** `source/backend/app/main.py`
- Definición de métricas con `prometheus_client`
- Middleware para capturar todas las requests
- Endpoint `/metrics`

### Métricas del Worker
**Archivo:** `source/worker/main.py`
- Definición de métricas de Celery
- Endpoint `/metrics` con información de colas

**Archivo:** `source/worker/celery_app.py`
- Signals para actualizar métricas automáticamente
- Instrumentación de tareas

### Configuración de Prometheus
**Archivo:** `performance-testing/prometheus/prometheus.yml`
- Scrape configs para backend y worker
- Usa red compartida `app-network`

### Dashboards de Grafana
**Archivos:**
- `performance-testing/grafana/provisioning/dashboards/backend_performance.json`
- `performance-testing/grafana/provisioning/dashboards/worker_performance.json`
- `performance-testing/grafana/provisioning/dashboards/dashboard.yml`

### Queries de Prometheus
**Archivo:** `performance-testing/PROMETHEUS_QUERIES.md`
- Todas las queries listas para copiar
- Ejemplos de alertas
- Fórmulas para reportes

---

## 🎬 Ejecutar Pruebas

### Prueba Rápida (Smoke Test)
```bash
# Generar tráfico ligero
for i in {1..100}; do
  curl -s http://localhost/api/health > /dev/null
  sleep 0.1
done

# Ver métricas en Grafana
# http://localhost:3000/d/backend-api-perf
```

### Prueba con JMeter
```bash
# 1. Acceder al contenedor de JMeter
docker exec -it jmeter bash

# 2. Ejecutar test
jmeter -n -t /scripts/ramp_up_test.jmx -l results.jtl

# 3. Monitorear en Grafana en tiempo real
# http://localhost:3000/d/backend-api-perf
```

### Prueba de Worker
```bash
# 1. Subir un video
curl -X POST http://localhost/api/videos/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=Test Video" \
  -F "video_file=@/path/to/video.mp4"

# 2. Ver métricas de procesamiento en Grafana
# http://localhost:3000/d/worker-perf
```

---

## 📈 Captura de Resultados

### Screenshots de Grafana
1. Ejecutar pruebas de carga
2. Ir a cada dashboard
3. Tomar screenshots de los paneles clave
4. Guardar para el reporte

### Exportar Datos de Prometheus
```bash
# Query para exportar datos
curl -g 'http://localhost:9090/api/v1/query_range?query=rate(http_requests_total[1m])&start=START_TIME&end=END_TIME&step=15s' > results.json
```

### Reportes Recomendados
1. **Curva de latencia vs usuarios** - Dashboard Backend → Latencia p95 + RPS
2. **Throughput del worker** - Dashboard Worker → Videos/min
3. **Estabilidad de cola** - Dashboard Worker → Tendencia de cola
4. **Recursos utilizados** - Ambos dashboards → CPU/Memoria

---

## ✅ Checklist Pre-Pruebas

- [ ] Servicios principales levantados (`docker-compose ps`)
- [ ] Stack de testing levantado
- [ ] Prometheus targets UP (http://localhost:9090/targets)
- [ ] Dashboards visibles en Grafana (http://localhost:3000)
- [ ] Métricas del backend con datos (generar tráfico de prueba)
- [ ] JWT configurado para JMeter (setup-jwt completado)
- [ ] Scripts de JMeter listos

---

## 🆘 Soporte

Si algo no funciona:
1. Revisar logs: `docker logs [container_name]`
2. Verificar red compartida: `docker network inspect app-network`
3. Reiniciar todo desde cero (ver Troubleshooting)
4. Revisar este README paso a paso
