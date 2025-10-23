# Arquitectura de Despliegue AWS - ANB Rising Stars

## Vista General del Sistema

```
┌───────────────────────────────────────────────────────────────────────────┐
│                              AWS CLOUD (us-east-1)                        │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                          DEFAULT VPC                                │ │
│  │                                                                     │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │                    Public Subnet                             │  │ │
│  │  │                                                              │  │ │
│  │  │  ┌────────────────────────────────────────────────────┐     │  │ │
│  │  │  │  EC2: anb-backend (t2.medium)                      │     │  │ │
│  │  │  │  Security Group: anb-backend-sg                    │     │  │ │
│  │  │  │  Public IP: 54.xxx.xxx.xxx                         │     │  │ │
│  │  │  │  Private IP: 172.31.10.5                           │     │  │ │
│  │  │  │                                                     │     │  │ │
│  │  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │     │  │ │
│  │  │  │  │    Nginx     │  │   Backend    │  │  Redis   │ │     │  │ │
│  │  │  │  │    :80       │─▶│   :8000      │◀─│  :6379   │ │     │  │ │
│  │  │  │  └──────────────┘  └──────────────┘  └──────────┘ │     │  │ │
│  │  │  │                                                     │     │  │ │
│  │  │  │  Storage: 20GB                                     │     │  │ │
│  │  │  │  Docker Network: anb-network                       │     │  │ │
│  │  │  └─────────────┬───────────────────┬──────────────────┘     │  │ │
│  │  │                │                   │                        │  │ │
│  │  │                │ NFS:2049          │ Redis:6379             │  │ │
│  │  │                ↓                   ↓                        │  │ │
│  │  │  ┌───────────────────────┐  ┌──────────────────────────┐   │  │ │
│  │  │  │  EC2: anb-nfs-server  │  │  EC2: anb-worker         │   │  │ │
│  │  │  │  (t2.small)           │  │  (t2.large)              │   │  │ │
│  │  │  │  SG: anb-nfs-sg       │  │  SG: anb-worker-sg       │   │  │ │
│  │  │  │  Private: 172.31.10.10│◀─│  Private: 172.31.10.20   │   │  │ │
│  │  │  │                       │  │                          │   │  │ │
│  │  │  │  ┌─────────────────┐ │  │  ┌────────────────────┐  │   │  │ │
│  │  │  │  │  NFS Server     │ │  │  │  Celery Worker     │  │   │  │ │
│  │  │  │  │  :2049          │ │  │  │  4 Concurrency     │  │   │  │ │
│  │  │  │  └─────────────────┘ │  │  └────────────────────┘  │   │  │ │
│  │  │  │                       │  │                          │   │  │ │
│  │  │  │  /mnt/nfs_share/      │  │  ┌────────────────────┐  │   │  │ │
│  │  │  │  ├─ uploads/          │  │  │  FFmpeg Processor  │  │   │  │ │
│  │  │  │  │  ├─ original/      │  │  │  Video Transform   │  │   │  │ │
│  │  │  │  │  ├─ processed/     │  │  └────────────────────┘  │   │  │ │
│  │  │  │  │  └─ temp/          │  │                          │   │  │ │
│  │  │  │                       │  │  ┌────────────────────┐  │   │  │ │
│  │  │  │  Storage:             │  │  │  Health API        │  │   │  │ │
│  │  │  │  - Root: 8GB          │  │  │  :8001             │  │   │  │ │
│  │  │  │  - EBS: 50GB          │  │  └────────────────────┘  │   │  │ │
│  │  │  │                       │  │                          │   │  │ │
│  │  │  │                       │  │  Mounted:                │   │  │ │
│  │  │  │                       │  │  /mnt/nfs_uploads        │   │  │ │
│  │  │  │                       │  │  ./assets (local)        │   │  │ │
│  │  │  └───────────────────────┘  └──────────┬───────────────┘   │  │ │
│  │  │                                        │                   │  │ │
│  │  └────────────────────────────────────────┼───────────────────┘  │ │
│  │                                           │                      │ │
│  └───────────────────────────────────────────┼──────────────────────┘ │
│                                              │                        │
│  ┌───────────────────────────────────────────┼──────────────────────┐ │
│  │                    Private Subnet         │                      │ │
│  │                                           │ PostgreSQL:5432      │ │
│  │                                           ↓                      │ │
│  │  ┌──────────────────────────────────────────────────────────┐   │ │
│  │  │  RDS PostgreSQL (db.t3.micro)                            │   │ │
│  │  │  Security Group: anb-rds-sg                              │   │ │
│  │  │  Endpoint: anb-database.xxx.us-east-1.rds.amazonaws.com │   │ │
│  │  │  Database: anbdb                                         │   │ │
│  │  │  Storage: 20GB                                           │   │ │
│  │  │  Multi-AZ: No (Free tier)                                │   │ │
│  │  └──────────────────────────────────────────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────┐
│         Internet Users                │
│              ↓                        │
│      HTTP Requests :80                │
│              ↓                        │
│   Public IP: Backend EC2              │
└───────────────────────────────────────┘
```

---

## Flujo de Datos

### 1. Upload de Video

```
User Browser
    │
    │ POST /api/videos/upload
    │ (multipart/form-data)
    ↓
┌────────────────┐
│  Nginx :80     │  Reverse Proxy
└───────┬────────┘
        │
        │ proxy_pass
        ↓
┌────────────────┐
│ Backend :8000  │  FastAPI
└───────┬────────┘
        │
        │ 1. Save file
        ↓
┌────────────────────┐
│ NFS Server         │  /uploads/original/video_123.mp4
│ /mnt/nfs_share/    │
└────────────────────┘
        │
        │ 2. Create DB record
        ↓
┌────────────────────┐
│ RDS PostgreSQL     │  videos table: status='original'
└────────────────────┘
        │
        │ 3. Queue task
        ↓
┌────────────────────┐
│ Redis :6379        │  video_processing queue
└────────────────────┘
        │
        │ 4. Return response
        ↓
    User Browser
    {
      "id": "123",
      "status": "processing"
    }
```

### 2. Procesamiento de Video

```
┌────────────────────┐
│ Redis :6379        │  Task in queue
└───────┬────────────┘
        │
        │ Celery worker polls
        ↓
┌────────────────────┐
│ Worker (Celery)    │  Pick task from queue
└───────┬────────────┘
        │
        │ 1. Read original video
        ↓
┌────────────────────┐
│ NFS Server         │  /uploads/original/video_123.mp4
│ Mounted on Worker  │
│ /mnt/nfs_uploads/  │
└────────────────────┘
        │
        │ 2. Process with FFmpeg
        ↓
┌────────────────────┐
│ FFmpeg Pipeline    │
│                    │
│ - Trim to 30s      │
│ - Scale to 720p    │
│ - Add watermark    │
│ - Remove audio     │
│ - Add intro/outro  │
│ - H.264 codec      │
└───────┬────────────┘
        │
        │ 3. Save processed video
        ↓
┌────────────────────┐
│ NFS Server         │  /uploads/processed/video_123.mp4
└────────────────────┘
        │
        │ 4. Update DB
        ↓
┌────────────────────┐
│ RDS PostgreSQL     │  videos table: status='processed'
└────────────────────┘
```

### 3. Descarga de Video Procesado

```
User Browser
    │
    │ GET /api/videos/123
    ↓
┌────────────────┐
│ Nginx :80      │
└───────┬────────┘
        │
        ↓
┌────────────────┐
│ Backend :8000  │  1. Query DB
└───────┬────────┘
        │
        ↓
┌────────────────────┐
│ RDS PostgreSQL     │  Get video metadata
└───────┬────────────┘
        │
        │ 2. Generate URL
        ↓
┌────────────────────┐
│ Backend            │  /api/videos/processed/video_123.mp4
└───────┬────────────┘
        │
        │ 3. Stream file
        ↓
┌────────────────────┐
│ NFS Server         │  Read from /uploads/processed/
│ Mounted on Backend │
│ /mnt/nfs_uploads/  │
└───────┬────────────┘
        │
        ↓
    User Browser
    (Video playback)
```

---

## Comunicación Entre Servicios

### Matriz de Conectividad

| Desde ↓ / Hacia → | Backend | Worker | NFS | RDS | Redis |
|-------------------|---------|--------|-----|-----|-------|
| **Internet**      | :80 ✅  | ❌     | ❌  | ❌  | ❌    |
| **Backend**       | -       | ❌     | :2049 ✅ | :5432 ✅ | Local ✅ |
| **Worker**        | :6379 ✅ | -      | :2049 ✅ | :5432 ✅ | :6379 ✅ |
| **NFS**           | ❌      | ❌     | -   | ❌  | ❌    |
| **RDS**           | ❌      | ❌     | ❌  | -   | ❌    |

### Protocolos y Puertos

| Servicio | Puerto | Protocolo | Propósito |
|----------|--------|-----------|-----------|
| Nginx | 80 | HTTP | API Gateway público |
| Backend | 8000 | HTTP | API REST (interno) |
| Redis | 6379 | TCP | Message broker (Celery) |
| Worker Health | 8001 | HTTP | Health checks |
| NFS | 2049 | TCP/NFS | File sharing |
| RPC Portmapper | 111 | TCP/UDP | NFS discovery |
| PostgreSQL | 5432 | TCP | Database |

---

## Security Groups - Diagrama de Reglas

### anb-backend-sg

```
INBOUND:
  Your IP        ──[SSH:22]──────────▶ Backend EC2
  0.0.0.0/0      ──[HTTP:80]─────────▶ Backend EC2
  Your IP        ──[TCP:8000]────────▶ Backend EC2 (debug)
  anb-worker-sg  ──[TCP:6379]────────▶ Backend EC2 (Redis)

OUTBOUND:
  Backend EC2    ──[All traffic]─────▶ 0.0.0.0/0
```

### anb-worker-sg

```
INBOUND:
  Your IP        ──[SSH:22]──────────▶ Worker EC2
  Your IP        ──[TCP:8001]────────▶ Worker EC2 (Health API)

OUTBOUND:
  Worker EC2     ──[All traffic]─────▶ 0.0.0.0/0
                 (Includes: NFS:2049, Redis:6379, PostgreSQL:5432)
```

### anb-nfs-sg

```
INBOUND:
  Your IP         ──[SSH:22]─────────▶ NFS EC2
  anb-backend-sg  ──[TCP:2049]───────▶ NFS EC2
  anb-worker-sg   ──[TCP:2049]───────▶ NFS EC2
  anb-backend-sg  ──[TCP/UDP:111]────▶ NFS EC2 (RPC)
  anb-worker-sg   ──[TCP/UDP:111]────▶ NFS EC2 (RPC)

OUTBOUND:
  NFS EC2        ──[All traffic]─────▶ 0.0.0.0/0
```

### anb-rds-sg

```
INBOUND:
  anb-backend-sg ──[TCP:5432]────────▶ RDS
  anb-worker-sg  ──[TCP:5432]────────▶ RDS
  Your IP        ──[TCP:5432]────────▶ RDS (optional debug)

OUTBOUND:
  RDS            ──[All traffic]─────▶ 0.0.0.0/0
```

---

## Almacenamiento

### Volúmenes EBS

```
┌─────────────────────────────────────────────────┐
│  Backend EC2                                    │
│  ├─ /dev/xvda (root)           20GB gp3        │
│  └─ Docker volumes:                             │
│     └─ anb-redis-data          ~1GB (Redis)    │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  Worker EC2                                     │
│  └─ /dev/xvda (root)           20GB gp3        │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  NFS Server EC2                                 │
│  ├─ /dev/xvda (root)           8GB gp3         │
│  └─ /dev/xvdf (data)           50GB gp3        │
│     └─ /mnt/nfs_share/uploads                  │
│        ├─ original/            (RAW videos)    │
│        ├─ processed/           (Processed)     │
│        └─ temp/                (Temporary)     │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  RDS PostgreSQL                                 │
│  └─ EBS Storage                20GB gp2        │
│     └─ Database: anbdb                          │
│        ├─ players table                         │
│        ├─ videos table                          │
│        └─ votes table                           │
└─────────────────────────────────────────────────┘
```

### NFS Mount Points

```
Backend EC2:
  /mnt/nfs_uploads ──NFS mount──▶ 172.31.10.10:/mnt/nfs_share/uploads
      │
      └─ Mapped to container: /app/uploads

Worker EC2:
  /mnt/nfs_uploads ──NFS mount──▶ 172.31.10.10:/mnt/nfs_share/uploads
      │
      └─ Mapped to container: /app/uploads

NFS Server:
  /mnt/nfs_share/uploads ◀─── Exported via NFS
      │
      └─ Stored on: /dev/xvdf (50GB EBS)
```

---

## Alta Disponibilidad y Escalamiento

### Escalamiento Horizontal (Futuro)

```
┌──────────────────────────────────────────────────────────┐
│  Application Load Balancer                               │
│  (Future)                                                │
└────┬─────────────────────────────┬───────────────────────┘
     │                             │
     ↓                             ↓
┌─────────────┐              ┌─────────────┐
│ Backend #1  │              │ Backend #2  │
│ (Active)    │              │ (Standby)   │
└─────────────┘              └─────────────┘
     │                             │
     └──────────┬──────────────────┘
                ↓
        ┌───────────────┐
        │ Shared Redis  │
        │ (ElastiCache) │
        └───────────────┘
```

```
┌──────────────────────────────────────────────────────────┐
│  Single Redis Queue                                      │
│  (Shared by all workers)                                 │
└────┬─────────────────────────────┬───────────────────────┘
     │                             │
     ↓                             ↓
┌─────────────┐              ┌─────────────┐
│ Worker #1   │              │ Worker #2   │
│ 4 processes │              │ 4 processes │
└─────────────┘              └─────────────┘
     │                             │
     └──────────┬──────────────────┘
                ↓
        ┌───────────────┐
        │ Shared NFS    │
        │ (or EFS)      │
        └───────────────┘
```

### Puntos de Fallo Únicos (SPOF)

| Componente | SPOF? | Mitigación |
|------------|-------|------------|
| Backend EC2 | ✅ Sí | → ALB + Multi-AZ Auto Scaling |
| Worker EC2 | ⚠️ Parcial | → Multiple workers (fácil) |
| NFS Server | ✅ Sí | → Migrate to EFS (AWS managed) |
| Redis | ✅ Sí | → ElastiCache Redis (replication) |
| RDS | ⚠️ Parcial | → Enable Multi-AZ (1 click) |

---

## Monitoreo y Observabilidad

### Endpoints de Health Check

```
Backend:
  http://<BACKEND_IP>/health
  http://<BACKEND_IP>:8000/health

Worker:
  http://<WORKER_IP>:8001/health
  http://<WORKER_IP>:8001/health/detailed

Prometheus Metrics:
  http://<BACKEND_IP>:8000/metrics
  http://<WORKER_IP>:8001/metrics
```

### Logs

```
Backend:
  docker-compose logs -f backend
  docker-compose logs -f nginx
  docker-compose logs -f redis

Worker:
  docker-compose logs -f worker

System:
  /var/log/syslog
  journalctl -u docker
```

---

## Costos Mensuales Estimados

```
┌───────────────────┬──────────────┬──────────────┬──────────────┐
│ Recurso           │ Tipo         │ $/hora       │ $/mes (24/7) │
├───────────────────┼──────────────┼──────────────┼──────────────┤
│ Backend EC2       │ t2.medium    │ $0.0464      │ $33.80       │
│ Worker EC2        │ t2.large     │ $0.0928      │ $67.60       │
│ NFS EC2           │ t2.small     │ $0.023       │ $16.70       │
│ RDS PostgreSQL    │ db.t3.micro  │ $0.016       │ $11.70       │
│ EBS Storage       │ 90GB gp3     │ $0.08/GB-mo  │ $7.20        │
│ Data Transfer     │ ~10GB/mo     │ $0.09/GB     │ $0.90        │
├───────────────────┴──────────────┴──────────────┼──────────────┤
│ TOTAL MENSUAL (24/7)                            │ ~$137.90     │
└─────────────────────────────────────────────────┴──────────────┘

AWS Academy Credits: $100 iniciales
Tiempo estimado con créditos: ~21 días corriendo 24/7
```

**Optimización de costos:**
- Detener instancias cuando no se usen: **~$11.70/mes** (solo RDS + storage)
- Usar Reserved Instances (1 año): **~40% descuento**
- Migrar a Spot Instances (Worker): **~70% descuento**

---

## Conclusión

Esta arquitectura proporciona:

✅ **Separación de responsabilidades**: Cada instancia tiene un rol específico
✅ **Escalabilidad**: Fácil agregar más workers
✅ **Seguridad**: Security Groups bien definidos
✅ **Observabilidad**: Health checks y monitoring
✅ **Almacenamiento compartido**: NFS para videos
✅ **Base de datos gestionada**: RDS PostgreSQL

Próximos pasos para producción:
- [ ] Implementar Load Balancer
- [ ] Migrar a EFS (en lugar de NFS EC2)
- [ ] Habilitar Multi-AZ en RDS
- [ ] Configurar Auto Scaling Groups
- [ ] Implementar HTTPS con ALB + ACM
- [ ] Configurar Route 53 (dominio personalizado)
- [ ] CloudWatch Alarms y SNS notifications
- [ ] Implementar CI/CD con CodePipeline
