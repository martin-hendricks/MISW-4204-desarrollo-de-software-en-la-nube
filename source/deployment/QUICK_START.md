# 🚀 Quick Start - Despliegue en AWS EC2

## Checklist de Despliegue Rápido

### ✅ Pre-requisitos
- [ ] Cuenta AWS Academy activada
- [ ] Par de llaves (.pem) descargado
- [ ] Assets de video preparados (logo.png, intro.mp4, outro.mp4)
- [ ] Repositorio clonado localmente

---

## 📝 Orden de Ejecución (3-4 horas total)

### 1️⃣ Security Groups (15 min)
```bash
# En AWS Console > EC2 > Security Groups
# Crear 4 Security Groups siguiendo: SECURITY_GROUPS.md

✅ anb-backend-sg
✅ anb-worker-sg
✅ anb-nfs-sg
✅ anb-rds-sg
```

### 2️⃣ RDS PostgreSQL (30 min)
```bash
# En AWS Console > RDS > Create Database

Engine: PostgreSQL 15.x
Instance: db.t3.micro
Database name: anbdb
Username: postgres
Password: <ANOTAR_PASSWORD>
Security Group: anb-rds-sg

# Esperar 15-20 min a que esté "Available"
# ANOTAR ENDPOINT
```

### 3️⃣ NFS Server (45 min)

**Crear instancia:**
- Name: `anb-nfs-server`
- Type: `t2.small`
- Storage: 8GB root + **50GB adicional**
- Security Group: `anb-nfs-sg`

**Configurar:**
```bash
ssh -i "key.pem" ubuntu@<NFS_PUBLIC_IP>

# Seguir: NFS_SERVER_SETUP.md (pasos 2.2 a 2.9)

# ANOTAR IP PRIVADA:
hostname -I
# Ejemplo: 172.31.10.10
```

### 4️⃣ Backend Instance (60 min)

**Crear instancia:**
- Name: `anb-backend`
- Type: `t2.medium`
- Storage: 20GB
- Security Group: `anb-backend-sg`

**Configurar:**
```bash
ssh -i "key.pem" ubuntu@<BACKEND_PUBLIC_IP>

# Instalar Docker
sudo apt update && sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
exit && ssh -i "key.pem" ubuntu@<BACKEND_PUBLIC_IP>

# Clonar repo o copiar archivos
git clone <REPO_URL> ~/anb-backend
cd ~/anb-backend/source/deployment/backend-instance

# Configurar .env
cp .env.example .env
nano .env
# Completar: DATABASE_URL, SECRET_KEY, BASE_PATH

# Montar NFS
nano setup-nfs-mount.sh
# Cambiar: NFS_SERVER_IP="172.31.10.10"
chmod +x setup-nfs-mount.sh
./setup-nfs-mount.sh

# Deploy
docker-compose up -d

# Migraciones
docker exec -it anb-backend alembic upgrade head

# ANOTAR IPs:
# Pública: para acceso externo
# Privada: para Worker
```

### 5️⃣ Worker Instance (45 min)

**Crear instancia:**
- Name: `anb-worker`
- Type: `t2.large`
- Storage: 20GB
- Security Group: `anb-worker-sg`

**Copiar assets PRIMERO (desde tu máquina local):**
```bash
scp -i "key.pem" anb_logo.png ubuntu@<WORKER_PUBLIC_IP>:~/assets/
scp -i "key.pem" intro.mp4 ubuntu@<WORKER_PUBLIC_IP>:~/assets/
scp -i "key.pem" outro.mp4 ubuntu@<WORKER_PUBLIC_IP>:~/assets/
```

**Configurar:**
```bash
ssh -i "key.pem" ubuntu@<WORKER_PUBLIC_IP>

# Instalar Docker
sudo apt update && sudo apt install -y docker.io docker-compose redis-tools
sudo usermod -aG docker ubuntu
exit && ssh -i "key.pem" ubuntu@<WORKER_PUBLIC_IP>

# Clonar repo
git clone <REPO_URL> ~/anb-worker
cd ~/anb-worker/source/deployment/worker-instance

# Mover assets
mkdir -p assets
mv ~/assets/* ./assets/

# Configurar .env
cp .env.example .env
nano .env
# Completar: DATABASE_URL, REDIS_URL (IP privada Backend), BASE_PATH

# Verificar Redis
redis-cli -h <BACKEND_PRIVATE_IP> ping
# Debe retornar: PONG

# Montar NFS
nano setup-nfs-mount.sh
# Cambiar: NFS_SERVER_IP="172.31.10.10"
chmod +x setup-nfs-mount.sh
./setup-nfs-mount.sh

# Deploy
docker-compose up -d
```

---

## ✅ Verificación Final

### Health Checks
```bash
# Backend
curl http://<BACKEND_PUBLIC_IP>/health

# Worker
curl http://<WORKER_PUBLIC_IP>:8001/health

# Flower (navegador)
http://<BACKEND_PUBLIC_IP>:5555
```

### Test E2E
```bash
# 1. Registrar usuario
curl -X POST http://<BACKEND_PUBLIC_IP>/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@test.com",
    "password": "Test123",
    "full_name": "Test User",
    "birth_date": "2000-01-01",
    "country": "USA",
    "gender": "M"
  }'

# 2. Login
curl -X POST http://<BACKEND_PUBLIC_IP>/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@test.com&password=Test123"
# GUARDAR access_token

# 3. Subir video
curl -X POST http://<BACKEND_PUBLIC_IP>/api/videos/upload \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@test.mp4"

# 4. Ver en Flower
# http://<BACKEND_PUBLIC_IP>:5555/tasks

# 5. Verificar en NFS (desde servidor NFS)
ls -lh /mnt/nfs_share/uploads/processed/
```

---

## 📊 Variables Importantes a Anotar

```bash
# RDS
RDS_ENDPOINT=_______________________________________________
RDS_PASSWORD=_______________________________________________

# NFS
NFS_PRIVATE_IP=_____________________________________________

# Backend
BACKEND_PUBLIC_IP=__________________________________________
BACKEND_PRIVATE_IP=_________________________________________

# Worker
WORKER_PUBLIC_IP=___________________________________________
WORKER_PRIVATE_IP=__________________________________________

# JWT
SECRET_KEY=_________________________________________________
```

---

## 🔥 Comandos de Emergencia

### Ver logs
```bash
# Backend
docker-compose logs -f backend

# Worker
docker-compose logs -f worker
```

### Reiniciar servicio
```bash
docker-compose restart <service>
```

### Reconstruir
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Verificar montaje NFS
```bash
df -h | grep nfs
ls -la /mnt/nfs_uploads
```

### Verificar conectividad
```bash
# Redis desde Worker
redis-cli -h <BACKEND_PRIVATE_IP> ping

# RDS desde Backend o Worker
telnet <RDS_ENDPOINT> 5432

# NFS desde Backend o Worker
showmount -e <NFS_PRIVATE_IP>
```

---

## 🐛 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| Backend no conecta a RDS | Verificar Security Group `anb-rds-sg` permite desde `anb-backend-sg` |
| Worker no ve Redis | Usar IP PRIVADA del Backend, no pública |
| NFS mount fail | Verificar Security Group `anb-nfs-sg` puerto 2049 |
| Worker no procesa | Verificar assets en `/app/assets` dentro del contenedor |
| 502 Bad Gateway | Backend probablemente caído, ver logs |

---

## 📚 Guías Completas

- [README.md](./README.md) - Guía maestra completa
- [SECURITY_GROUPS.md](./SECURITY_GROUPS.md) - Configuración detallada de SGs
- [NFS_SERVER_SETUP.md](./NFS_SERVER_SETUP.md) - Setup completo NFS
- [backend-instance/DEPLOY.md](./backend-instance/DEPLOY.md) - Deploy Backend
- [worker-instance/DEPLOY.md](./worker-instance/DEPLOY.md) - Deploy Worker

---

## ⏱️ Tiempos Estimados

| Fase | Tiempo |
|------|--------|
| Security Groups + RDS | 45 min |
| NFS Server | 45 min |
| Backend | 60 min |
| Worker | 45 min |
| Testing | 30 min |
| **TOTAL** | **3-4 horas** |

---

**¡Éxito!** 🎉

Si todo funcionó, deberías poder:
- Acceder a Swagger UI: `http://<BACKEND_IP>/docs`
- Ver Flower: `http://<BACKEND_IP>:5555`
- Subir videos y verlos procesarse en tiempo real
