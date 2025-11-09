# CloudWatch Metrics - Configuración

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

### 3. Deploy

```bash
# Backend
docker-compose build backend && docker-compose up -d backend

# Worker
docker-compose build worker && docker-compose up -d worker
```

### 4. Verificar

```bash
# Ver logs EMF (debe mostrar JSON con "_aws")
docker logs anb-backend 2>&1 | grep '_aws'
docker logs anb-worker 2>&1 | grep '_aws'

# Generar tráfico
for i in {1..50}; do curl http://BACKEND_IP/health; sleep 1; done

# Esperar 2-3 minutos, luego:
# CloudWatch Console → All metrics → ANB/Backend, ANB/Worker
```

---

## 📊 Métricas Disponibles

### Backend (ANB/Backend)
- `RequestCount`, `RequestDuration` (p95, p99), `ErrorCount`
- `ProcessCPU`, `ProcessMemoryMB`, `SystemCPU`

### Worker (ANB/Worker)
- `TaskCount`, `TaskDuration` (p95, p99), `TaskFailure`
- `VideoFileSize`, `QueueLength`, `ActiveTasks`

**Dimensiones**: `InstanceId`, `AvailabilityZone`, `Environment`, `Method`, `Endpoint`, `StatusCode`, `TaskName`, `Status`

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

## 🚨 Crear Alarmas (Opcional)

```bash
# Latencia alta
aws cloudwatch put-metric-alarm \
  --alarm-name ANB-API-Latency-High \
  --metric-name RequestDuration \
  --namespace ANB/Backend \
  --statistic p95 \
  --threshold 1000 \
  --comparison-operator GreaterThanThreshold

# Queue larga
aws cloudwatch put-metric-alarm \
  --alarm-name ANB-Queue-High \
  --metric-name QueueLength \
  --namespace ANB/Worker \
  --dimensions Name=QueueName,Value=video_processing \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
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

## 📁 Archivos de la Migración

- ✅ `shared/cloudwatch_metrics.py` - Módulo EMF
- ✅ `backend/app/main.py` - Middleware CloudWatch
- ✅ `worker/metrics.py` - Cliente CloudWatch
- ✅ `worker/celery_app.py` - Signals con métricas
- ✅ `backend/requirements.txt`, `worker/requirements.txt` - Sin prometheus-client

**Prometheus/Grafana removido** - Ya no se usa.
