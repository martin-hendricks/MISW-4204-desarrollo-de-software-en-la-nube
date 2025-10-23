# 🚀 Comenzar - Pasos Rápidos

## Tu Situación Actual

✅ **Ya tienes:**
- Instancia Backend EC2 (Ubuntu + Docker + Docker Compose)
- Instancia Worker EC2 (Ubuntu + Docker + Docker Compose)

⏳ **Aún necesitas crear:**
1. Servidor NFS
2. RDS PostgreSQL
3. Configurar Security Groups

---

## Paso 1: Crear Security Groups (15 min)

Antes de crear las instancias, crea los Security Groups en AWS Console.

**En AWS Console > EC2 > Security Groups > Create Security Group:**

### 1.1 Backend Security Group

```
Name: anb-backend-sg
Description: Security group for Backend (Nginx + API + Redis)

Inbound Rules:
- SSH (22) from Your IP
- HTTP (80) from 0.0.0.0/0
- Custom TCP (8000) from Your IP [opcional para debug]
- Custom TCP (6379) from anb-worker-sg [agregar después de crear worker-sg]

Outbound Rules:
- All traffic to 0.0.0.0/0
```

### 1.2 Worker Security Group

```
Name: anb-worker-sg
Description: Security group for Worker (Celery)

Inbound Rules:
- SSH (22) from Your IP
- Custom TCP (8001) from Your IP [opcional para debug]

Outbound Rules:
- All traffic to 0.0.0.0/0
```

### 1.3 NFS Security Group

```
Name: anb-nfs-sg
Description: Security group for NFS Server

Inbound Rules:
- SSH (22) from Your IP
- NFS (2049) from anb-backend-sg
- NFS (2049) from anb-worker-sg
- Custom TCP (111) from anb-backend-sg
- Custom TCP (111) from anb-worker-sg

Outbound Rules:
- All traffic to 0.0.0.0/0
```

### 1.4 RDS Security Group

```
Name: anb-rds-sg
Description: Security group for RDS PostgreSQL

Inbound Rules:
- PostgreSQL (5432) from anb-backend-sg
- PostgreSQL (5432) from anb-worker-sg
- PostgreSQL (5432) from Your IP [opcional para debug]

Outbound Rules:
- All traffic to 0.0.0.0/0
```

**⚠️ IMPORTANTE:** Después de crear `anb-worker-sg`, vuelve a `anb-backend-sg` y agrega la regla para Redis (6379).

---

## Paso 2: Crear RDS PostgreSQL (30 min)

**En AWS Console > RDS > Create Database:**

```
1. Engine: PostgreSQL 15.x
2. Templates: Free tier
3. DB instance identifier: anb-database
4. Master username: postgres
5. Master password: <CREAR_PASSWORD_SEGURO>
6. DB instance class: db.t3.micro
7. Storage: 20 GB, NO autoscaling
8. VPC: Default VPC
9. Public access: No
10. VPC security group: anb-rds-sg
11. Database name: anbdb
12. Click: Create database
```

**Esperar 15-20 minutos a que esté "Available".**

**Anotar:**
```
RDS_ENDPOINT: _____________________________________________
RDS_PASSWORD: _____________________________________________
```

---

## Paso 3: Crear y Configurar Servidor NFS (45 min)

### 3.1 Crear Instancia EC2

```
Name: anb-nfs-server
AMI: Ubuntu Server 22.04 LTS
Instance type: t2.small
Key pair: <tu-key>
Security group: anb-nfs-sg

Storage:
  - Root volume: 8 GB (gp3)
  - Add New Volume: 50 GB (gp3) ← IMPORTANTE
```

### 3.2 Configurar NFS

```bash
# Conectarse
ssh -i "your-key.pem" ubuntu@<NFS_PUBLIC_IP>

# Seguir la guía completa
```

📄 **Guía detallada:** [NFS_SERVER_SETUP.md](./NFS_SERVER_SETUP.md)

**Comandos rápidos:**

```bash
# Instalar NFS
sudo apt update && sudo apt install -y nfs-kernel-server

# Formatear disco (SOLO SI ES NUEVO)
sudo mkfs.ext4 /dev/xvdf

# Montar
sudo mkdir -p /mnt/nfs_share
sudo mount /dev/xvdf /mnt/nfs_share

# Crear directorios
sudo mkdir -p /mnt/nfs_share/uploads/{original,processed,temp}
sudo chmod -R 777 /mnt/nfs_share/uploads

# Configurar exports
sudo nano /etc/exports
# Agregar (reemplaza IPs con las PRIVADAS de Backend y Worker):
/mnt/nfs_share/uploads 172.31.X.X(rw,sync,no_subtree_check,no_root_squash) 172.31.Y.Y(rw,sync,no_subtree_check,no_root_squash)

# Aplicar
sudo exportfs -a
sudo systemctl restart nfs-kernel-server

# Verificar
sudo exportfs -v
showmount -e localhost
```

**Anotar IP privada:**
```bash
hostname -I
# Ejemplo: 172.31.10.10
```

```
NFS_PRIVATE_IP: _____________________________________________
```

---

## Paso 4: Configurar Backend (YA TIENES LA INSTANCIA) (30 min)

### 4.1 Copiar archivos al servidor

**Opción A: Git**
```bash
ssh -i "key.pem" ubuntu@<BACKEND_PUBLIC_IP>
git clone <REPO_URL> ~/anb-backend
cd ~/anb-backend/source/deployment/backend-instance
```

**Opción B: SCP desde tu PC**
```bash
# Desde tu máquina local
scp -i "key.pem" -r ./source/deployment/backend-instance ubuntu@<BACKEND_IP>:~/
scp -i "key.pem" -r ./source/backend ubuntu@<BACKEND_IP>:~/
scp -i "key.pem" -r ./source/api-gateway ubuntu@<BACKEND_IP>:~/
```

### 4.2 Configurar .env

```bash
cd ~/anb-backend/source/deployment/backend-instance
cp .env.example .env
nano .env
```

**Completar:**
```bash
DATABASE_URL=postgresql://postgres:TU_PASSWORD@anb-database.xxx.us-east-1.rds.amazonaws.com:5432/anbdb
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<generar-clave-aleatoria-minimo-32-caracteres>
BASE_PATH=http://<BACKEND_PUBLIC_IP>/api/videos
FILE_STORAGE_TYPE=local
UPLOAD_DIR=/app/uploads
```

### 4.3 Montar NFS

```bash
# Editar script
nano setup-nfs-mount.sh
# Cambiar línea 17:
# NFS_SERVER_IP="172.31.10.10"  ← Tu IP privada del NFS

chmod +x setup-nfs-mount.sh
./setup-nfs-mount.sh

# Verificar
df -h | grep nfs
ls -la /mnt/nfs_uploads
```

### 4.4 Desplegar

```bash
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar contenedores
docker-compose ps
```

### 4.5 Ejecutar migraciones

```bash
docker exec -it anb-backend alembic upgrade head
```

### 4.6 Verificar

```bash
# Health check
curl http://localhost/health

# Desde tu PC
curl http://<BACKEND_PUBLIC_IP>/health

# Swagger Docs (navegador)
http://<BACKEND_PUBLIC_IP>/docs
```

**Anotar IPs:**
```
BACKEND_PUBLIC_IP: _____________________________________________
BACKEND_PRIVATE_IP (hostname -I): _________________________________
```

---

## Paso 5: Configurar Worker (YA TIENES LA INSTANCIA) (30 min)

### 5.1 Copiar archivos

```bash
ssh -i "key.pem" ubuntu@<WORKER_PUBLIC_IP>

# Opción A: Git
git clone <REPO_URL> ~/anb-worker
cd ~/anb-worker/source/deployment/worker-instance

# Opción B: SCP (desde tu PC)
# scp -i "key.pem" -r ./source/deployment/worker-instance ubuntu@<WORKER_IP>:~/
# scp -i "key.pem" -r ./source/worker ubuntu@<WORKER_IP>:~/
```

### 5.2 Copiar assets de video

**Desde tu PC:**
```bash
scp -i "key.pem" anb_logo.png ubuntu@<WORKER_IP>:~/
scp -i "key.pem" intro.mp4 ubuntu@<WORKER_IP>:~/
scp -i "key.pem" outro.mp4 ubuntu@<WORKER_IP>:~/
```

**En el Worker:**
```bash
mkdir -p ~/anb-worker/source/deployment/worker-instance/assets
mv ~/*.png ~/*.mp4 ~/anb-worker/source/deployment/worker-instance/assets/
```

### 5.3 Configurar .env

```bash
cd ~/anb-worker/source/deployment/worker-instance
cp .env.example .env
nano .env
```

**Completar:**
```bash
DATABASE_URL=postgresql://postgres:TU_PASSWORD@anb-database.xxx.us-east-1.rds.amazonaws.com:5432/anbdb
REDIS_URL=redis://172.31.X.X:6379/0  ← IP PRIVADA del Backend
BASE_PATH=http://54.X.X.X/api/videos  ← IP PÚBLICA del Backend
UPLOAD_DIR=/app/uploads
```

### 5.4 Verificar conectividad a Redis

```bash
sudo apt install -y redis-tools
redis-cli -h <BACKEND_PRIVATE_IP> ping
# Debe retornar: PONG
```

### 5.5 Montar NFS

```bash
nano setup-nfs-mount.sh
# Cambiar: NFS_SERVER_IP="172.31.10.10"  ← Tu IP privada del NFS

chmod +x setup-nfs-mount.sh
./setup-nfs-mount.sh

# Verificar
df -h | grep nfs
ls -la /mnt/nfs_uploads
# Deberías ver los mismos archivos que en Backend
```

### 5.6 Desplegar

```bash
docker-compose up -d

# Ver logs
docker-compose logs -f worker

# Verificar
docker-compose ps
curl http://localhost:8001/health
```

---

## Paso 6: Verificación End-to-End (15 min)

### 6.1 Registrar usuario

```bash
curl -X POST http://<BACKEND_PUBLIC_IP>/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@test.com",
    "password": "Test123456",
    "full_name": "Test User",
    "birth_date": "2000-01-01",
    "country": "USA",
    "gender": "M"
  }'
```

### 6.2 Login

```bash
curl -X POST http://<BACKEND_PUBLIC_IP>/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@test.com&password=Test123456"

# GUARDAR EL access_token
```

### 6.3 Subir video

```bash
curl -X POST http://<BACKEND_PUBLIC_IP>/api/videos/upload \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "file=@test_video.mp4"
```

### 6.4 Verificar procesamiento

**Ver logs del Worker:**
```bash
# En instancia Worker
docker-compose logs -f worker | grep process_video
```

**Verificar en NFS:**
```bash
# En servidor NFS
ls -lht /mnt/nfs_share/uploads/processed/ | head

# Deberías ver el video procesado
```

**Consultar API:**
```bash
curl -X GET http://<BACKEND_PUBLIC_IP>/api/videos \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# El video debería tener status: "processed"
```

---

## ✅ Checklist Final

- [ ] Security Groups creados (4)
- [ ] RDS PostgreSQL funcionando
- [ ] NFS Server montado y exportando
- [ ] Backend desplegado y respondiendo en puerto 80
- [ ] Worker desplegado y procesando tareas
- [ ] Test end-to-end exitoso

---

## 📊 Información Recopilada

```
# RDS
RDS_ENDPOINT = _____________________________________________
RDS_PASSWORD = _____________________________________________

# NFS
NFS_PRIVATE_IP = _____________________________________________

# Backend
BACKEND_PUBLIC_IP = _____________________________________________
BACKEND_PRIVATE_IP = _____________________________________________

# Worker
WORKER_PUBLIC_IP = _____________________________________________
WORKER_PRIVATE_IP = _____________________________________________

# JWT
SECRET_KEY = _____________________________________________
```

---

## 🐛 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| Backend no conecta a RDS | Verificar SG `anb-rds-sg` permite desde `anb-backend-sg` |
| Worker no ve Redis | Usar IP PRIVADA del Backend en `REDIS_URL` |
| NFS mount failed | Verificar SG `anb-nfs-sg` puerto 2049 desde las instancias |
| Worker no procesa | Verificar assets en `/app/assets` del contenedor |
| 502 Bad Gateway | Backend caído, ver logs: `docker-compose logs backend` |

---

## 📚 Guías Completas

Si necesitas más detalles:
- [README.md](./README.md) - Guía completa paso a paso
- [NFS_SERVER_SETUP.md](./NFS_SERVER_SETUP.md) - Servidor NFS detallado
- [SECURITY_GROUPS.md](./SECURITY_GROUPS.md) - Security Groups completos
- [backend-instance/DEPLOY.md](./backend-instance/DEPLOY.md) - Backend detallado
- [worker-instance/DEPLOY.md](./worker-instance/DEPLOY.md) - Worker detallado

---

**Tiempo estimado total: 2.5 - 3 horas**

¡Éxito! 🎉
