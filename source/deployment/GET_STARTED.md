# 🚀 Guía de Instalación en AWS EC2

Esta guía te llevará paso a paso para desplegar el proyecto ANB Rising Stars en AWS EC2 con una arquitectura distribuida de microservicios.

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

**Anotar datos de RDS:**
```
RDS Endpoint: _______________________________________________
Usuario: postgres (o el que configuraste)
Password: _______________________________________________
Database: anbdb
```

### 2.1 Inicializar Base de Datos (IMPORTANTE)

⚠️ **Este proyecto NO usa Alembic** - debes ejecutar el script `init.sql` para crear las tablas.

**Opciones para ejecutar init.sql:**

#### **Opción 1: Script Automatizado** (Recomendado - se ejecuta más tarde)

El script `init-database.sh` ya está incluido en `backend-instance/`. Lo ejecutarás después de crear la instancia Backend en el **Paso 4.3**.

#### **Opción 2: Desde tu máquina local** (Ahora mismo)

Si tienes PostgreSQL instalado localmente:

```bash
# Instalar cliente PostgreSQL (si no lo tienes)
# macOS: brew install postgresql
# Ubuntu/WSL: sudo apt install postgresql-client
# Windows: Descargar desde postgresql.org

# Ejecutar init.sql
psql -h anb-database.ctxmjxakbtby.us-east-1.rds.amazonaws.com \
     -U postgres \
     -d anbdb \
     -p 5432 \
     -f ./source/database/init.sql

# Te pedirá la password de RDS
```

#### **¿Qué crea el init.sql?**

```sql
✅ ENUM: video_status ('uploaded', 'processed')
✅ Tabla: players (jugadores - id, email, password, etc.)
✅ Tabla: videos (videos - id, player_id, title, status, urls, etc.)
✅ Tabla: votes (votos - id, player_id, video_id, etc.)
```

**📝 Nota:** Si decides esperar, ejecutarás esto en el Paso 4.3 desde la instancia Backend.

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

```


**Comandos rápidos:**

```bash
# Instalar NFS
sudo apt update && sudo apt install -y nfs-kernel-server

# Crear directorios
sudo mkdir /var/nfs/shared_folder -p

#Verificar la creacion del folder
ls -la /var/nfs/shared_folder

# Configurar exports
sudo nano /etc/exports

# Agregar (reemplaza con las IPs PRIVADAS de Backend y Worker):
/var/nfs/shared_folder *(rw,sync,no_subtree_check)

#Ajustar permisos al folder
sudo chown nobody:nogroup /var/nfs/shared_folder

# Aplicar
sudo exportfs -a
sudo systemctl restart nfs-kernel-server

```

**Anotar IP privada:**
```bash
hostname -I
# Ejemplo: 172.31.XXX.XXX
```

### 3.3 Verificación desde el Servidor NFS

**Verificar que NFS está escuchando:**

```bash
sudo netstat -tuln | grep 2049
# Deberías ver: tcp  0  0 0.0.0.0:2049  0.0.0.0:*  LISTEN
```

**Ver logs en caso de problemas:**

```bash
sudo journalctl -u nfs-kernel-server -f
```

**Verificar montajes:**

```bash
showmount -e localhost
# Deberías ver:
# Export list for localhost:
# /var/nfs/shared_folder/uploads 172.31.XXX.XXX,172.31.YYY.YYY
```
_____________________________________________

---

### Paso 4: Crear Instancia Backend (15 min)

### 4.1 Crear Instancia EC2

**En AWS Console > EC2 > Launch Instance:**

```
Name: anb-backend
AMI: Ubuntu Server 22.04 LTS
Instance type: t2.medium
Key pair: <tu-key>
Security group: anb-backend-sg
Storage: 20 GB (gp3)
```

### 4.2 Instalar Docker y Docker Compose

```bash
# Conectarse
ssh -i "your-key.pem" ubuntu@<BACKEND_PUBLIC_IP>

# Instalar Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu

# Cerrar sesión y volver a entrar para aplicar permisos
exit
ssh -i "your-key.pem" ubuntu@<BACKEND_PUBLIC_IP>

# Verificar
docker --version
docker-compose --version
```

### 4.3 Configurar y Desplegar Backend

📄 **Para los pasos detallados de configuración y despliegue, sigue la guía completa:**

➡️ **[backend-instance/DEPLOY.md](./backend-instance/DEPLOY.md)**

Esta guía incluye:
- Copiar archivos del proyecto
- Configurar variables de entorno (.env)
- Montar NFS
- **🗄️ Inicializar Base de Datos (ejecutar init.sql)** ← IMPORTANTE
- Desplegar servicios con Docker Compose
- Verificar endpoints y health checks
- Troubleshooting

**⚠️ RECORDATORIO:** Si no ejecutaste el `init.sql` en el Paso 2.1, deberás hacerlo en el Paso 5 del DEPLOY.md usando el script `init-database.sh`.

**Tiempo estimado:** 45-60 minutos

---

## Paso 5: Crear Instancia Worker (30 min)

### 5.1 Crear Instancia EC2

**En AWS Console > EC2 > Launch Instance:**

```
Name: anb-worker
AMI: Ubuntu Server 22.04 LTS
Instance type: t2.large (para procesamiento de video)
Key pair: <tu-key>
Security group: anb-worker-sg
Storage: 20 GB (gp3)
```

### 5.2 Instalar Docker y Docker Compose

```bash
# Conectarse
ssh -i "your-key.pem" ubuntu@<WORKER_PUBLIC_IP>

# Instalar Docker
sudo apt update
sudo apt install -y docker.io docker-compose redis-tools
sudo usermod -aG docker ubuntu

# Cerrar sesión y volver a entrar
exit
ssh -i "your-key.pem" ubuntu@<WORKER_PUBLIC_IP>

# Verificar
docker --version
docker-compose --version
```

**Anotar IP:**
```
WORKER_PUBLIC_IP: _____________________________________________
WORKER_PRIVATE_IP (hostname -I): _________________________________
```

### 5.3 Configurar y Desplegar Worker

📄 **Para los pasos detallados de configuración y despliegue, sigue la guía completa:**

➡️ **[worker-instance/DEPLOY.md](./worker-instance/DEPLOY.md)**

Esta guía incluye:
- Copiar archivos del proyecto
- Preparar assets de video (logo, intro, outro)
- Configurar variables de entorno (.env)
- Verificar conectividad con Redis (Backend)
- Montar NFS
- Desplegar servicios con Docker Compose
- Verificar health checks y procesamiento
- Troubleshooting

**Tiempo estimado:** 60-75 minutos

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
- [ ] **Base de datos inicializada (init.sql ejecutado)** ← CRÍTICO
- [ ] NFS Server montado y exportando
- [ ] Backend desplegado y respondiendo en puerto 80
- [ ] Worker desplegado y procesando tareas
- [ ] Test end-to-end exitoso

---

## 🗄️ Referencia Rápida: Inicializar Base de Datos

Si olvidaste ejecutar el `init.sql` o necesitas hacerlo nuevamente:

### **Opción 1: Desde instancia Backend (Recomendado)**

```bash
# Conectar a la instancia Backend
ssh -i "your-key.pem" ubuntu@<BACKEND_PUBLIC_IP>

# Ir a la carpeta de deployment
cd ~/anb-backend/source/deployment/backend-instance

# Ejecutar script automatizado
chmod +x init-database.sh
./init-database.sh
```

### **Opción 2: Manual desde Backend**

```bash
# Conectar a Backend
ssh -i "your-key.pem" ubuntu@<BACKEND_PUBLIC_IP>

# Instalar postgresql-client
sudo apt install -y postgresql-client

# Ejecutar init.sql (reemplaza con tus valores)
PGPASSWORD='TU_PASSWORD' psql \
  -h anb-database.ctxmjxakbtby.us-east-1.rds.amazonaws.com \
  -U postgres \
  -d anbdb \
  -p 5432 \
  -f ~/anb-backend/source/database/init.sql
```

### **Opción 3: Desde tu máquina local**

```bash
# En tu máquina local (requiere postgresql-client instalado)
psql -h <RDS_ENDPOINT> \
     -U postgres \
     -d anbdb \
     -p 5432 \
     -f ./source/database/init.sql
```

### **Verificar que se crearon las tablas:**

```bash
PGPASSWORD='TU_PASSWORD' psql \
  -h <RDS_ENDPOINT> \
  -U postgres \
  -d anbdb \
  -c "\dt"

# Deberías ver:
#  players | videos | votes
```

---

## 🐛 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| **Backend: relation "players" does not exist** | ❌ No ejecutaste `init.sql` - Ver sección "Referencia Rápida" arriba |
| Backend no conecta a RDS | Verificar SG `anb-rds-sg` permite puerto 5432 desde `anb-backend-sg` |
| Worker no ve Redis | Usar IP **PRIVADA** del Backend en `REDIS_URL` del `.env` |
| NFS mount failed | Verificar SG `anb-nfs-sg` puerto 2049 desde las instancias |
| Worker no procesa | Verificar assets en `/app/assets` del contenedor: `docker exec -it anb-worker ls /app/assets` |
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
