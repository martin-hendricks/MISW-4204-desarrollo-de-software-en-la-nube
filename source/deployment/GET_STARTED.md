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

# Montar (o usar la ruta que ya tenga tu compañero)
sudo mkdir -p /var/nfs/shared_folder
sudo mount /dev/xvdf /var/nfs/shared_folder

# Crear directorios
sudo mkdir -p /var/nfs/shared_folder/uploads/{original,processed,temp}
sudo chmod -R 777 /var/nfs/shared_folder/uploads

# Configurar exports
sudo nano /etc/exports
# Agregar (reemplaza con las IPs PRIVADAS de Backend y Worker):
/var/nfs/shared_folder/uploads 172.31.XXX.XXX(rw,sync,no_subtree_check,no_root_squash) 172.31.YYY.YYY(rw,sync,no_subtree_check,no_root_squash)

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
# Ejemplo: 172.31.XXX.XXX
```
_____________________________________________
```

---

## Paso 4: Crear Instancia Backend (15 min)

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
- Desplegar servicios con Docker Compose
- Ejecutar migraciones de base de datos
- Verificar endpoints y health checks
- Troubleshooting

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
- [ ] NFS Server montado y exportando
- [ ] Backend desplegado y respondiendo en puerto 80
- [ ] Worker desplegado y procesando tareas
- [ ] Test end-to-end exitoso

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
