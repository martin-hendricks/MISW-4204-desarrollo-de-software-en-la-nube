# Guía de Despliegue - Instancia Backend

## Resumen
Esta instancia EC2 contiene:
- ✅ Nginx (API Gateway) - Puerto 80
- ✅ Redis (Message Broker) - Puerto 6379
- ✅ Backend API (FastAPI) - Puerto 8000

---

## Requisitos Previos

### 1. Instancia EC2 configurada
- ✅ Ubuntu Server 22.04 LTS
- ✅ Tipo: t2.medium o superior
- ✅ Docker y Docker Compose instalados
- ✅ Security Group configurado (ver abajo)

### 2. Servicios externos creados
- ✅ Servidor NFS configurado y ejecutándose
- ✅ RDS PostgreSQL creado y accesible
- ⏳ Worker (se desplegará después)

### 3. Información que necesitas tener a mano
- IP privada del servidor NFS
- Endpoint de RDS PostgreSQL
- Usuario y contraseña de RDS
- Nombre de la base de datos en RDS

---

## Security Group - Backend Instance

### Inbound Rules

| Type | Protocol | Port | Source | Description |
|------|----------|------|--------|-------------|
| SSH | TCP | 22 | Your IP | Administración SSH |
| HTTP | TCP | 80 | 0.0.0.0/0 | Nginx - Acceso público |
| Custom TCP | TCP | 8000 | Your IP | Backend API (debug) |
| Custom TCP | TCP | 6379 | Worker SG | Redis para Worker |

### Outbound Rules
- All traffic (default)

---

## Pasos de Despliegue

### Paso 1: Conectarse a la instancia

```bash
ssh -i "your-key.pem" ubuntu@<BACKEND_PUBLIC_IP>
```

### Paso 2: Clonar/Copiar los archivos del proyecto

```bash
# Crear directorio de trabajo
mkdir -p ~/anb-backend
cd ~/anb-backend

# Opción A: Clonar repositorio (si está en GitHub)
git clone <your-repo-url> .
cd source/deployment/backend-instance

# Opción B: Copiar archivos manualmente usando SCP desde tu máquina local
# Desde tu máquina local:
# scp -i "your-key.pem" -r ./source/deployment/backend-instance ubuntu@<BACKEND_PUBLIC_IP>:~/anb-backend/
# scp -i "your-key.pem" -r ./source/backend ubuntu@<BACKEND_PUBLIC_IP>:~/anb-backend/
```

### Paso 3: Configurar variables de entorno

```bash
cd ~/anb-backend/deployment/backend-instance

# Copiar archivo de ejemplo
cp .env.example .env

# Editar con tus valores reales
nano .env
```

**Variables que DEBES cambiar:**

```bash
# RDS Database
DATABASE_URL=postgresql://admin:YourPassword@anb-db.xxx.us-east-1.rds.amazonaws.com:5432/anbdb

# JWT Secret (generar uno aleatorio)
SECRET_KEY=tu-clave-secreta-super-segura-minimo-32-caracteres

# Base Path (IP pública de esta instancia)
BASE_PATH=http://54.123.45.67/api/videos
```

### Paso 4: Configurar montaje NFS

```bash
# Editar el script con la IP del servidor NFS
nano setup-nfs-mount.sh

# Cambiar esta línea:
# NFS_SERVER_IP="REPLACE_WITH_NFS_PRIVATE_IP"
# Por ejemplo:
# NFS_SERVER_IP="172.31.10.10"

# Dar permisos de ejecución
chmod +x setup-nfs-mount.sh

# Ejecutar el script
./setup-nfs-mount.sh
```

**Verificar que NFS está montado:**

```bash
df -h | grep nfs
ls -la /mnt/nfs_uploads
```

Deberías ver:

```
172.31.10.10:/mnt/nfs_share/uploads  50G  1.2G   46G   3% /mnt/nfs_uploads

drwxrwxrwx 5 root root 4096 Jan 15 10:30 .
drwxr-xr-x 3 root root 4096 Jan 15 10:25 ..
drwxrwxrwx 2 root root 4096 Jan 15 10:30 original
drwxrwxrwx 2 root root 4096 Jan 15 10:30 processed
drwxrwxrwx 2 root root 4096 Jan 15 10:30 temp
```

### Paso 5: Construir y levantar los servicios

```bash
cd ~/anb-backend/deployment/backend-instance

# Construir las imágenes
docker-compose build

# Levantar los servicios en segundo plano
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Paso 6: Verificar que los servicios están corriendo

```bash
# Ver estado de contenedores
docker-compose ps

# Deberías ver:
# NAME                IMAGE                    STATUS
# anb-nginx           nginx:alpine             Up (healthy)
# anb-redis           redis:7-alpine           Up (healthy)
# anb-backend         backend-instance-backend Up (healthy)
```

### Paso 7: Ejecutar migraciones de base de datos

```bash
# Entrar al contenedor del backend
docker exec -it anb-backend bash

# Ejecutar migraciones de Alembic
alembic upgrade head

# Salir del contenedor
exit
```

### Paso 8: Verificar endpoints

```bash
# Health check de Nginx
curl http://localhost/health
# Debería retornar: {"status":"healthy","service":"nginx"}

# Health check de Backend
curl http://localhost:8000/health
# Debería retornar información de salud del backend

# Verificar Redis
docker exec -it anb-redis redis-cli ping
# Debería retornar: PONG
```

### Paso 9: Acceso desde tu máquina local

```bash
# Reemplaza <BACKEND_PUBLIC_IP> con la IP pública de tu instancia

# Health check
curl http://<BACKEND_PUBLIC_IP>/health

# Swagger Docs
# Abrir en navegador: http://<BACKEND_PUBLIC_IP>/docs
```

---

## Comandos Útiles

### Ver logs

```bash
# Todos los servicios
docker-compose logs -f

# Solo backend
docker-compose logs -f backend

# Solo nginx
docker-compose logs -f nginx

# Solo redis
docker-compose logs -f redis
```

### Reiniciar servicios

```bash
# Todos los servicios
docker-compose restart

# Solo backend
docker-compose restart backend
```

### Detener servicios

```bash
# Detener
docker-compose stop

# Detener y eliminar contenedores
docker-compose down

# Detener, eliminar contenedores Y volúmenes
docker-compose down -v
```

### Rebuild después de cambios en código

```bash
# Rebuild y restart
docker-compose up -d --build
```

### Monitorear recursos

```bash
# Uso de CPU y memoria de contenedores
docker stats

# Espacio en disco
df -h

# Espacio usado por Docker
docker system df
```

---

## Troubleshooting

### Error: "Cannot connect to database"

```bash
# Verificar que RDS es alcanzable
telnet <RDS_ENDPOINT> 5432

# Verificar Security Group de RDS permite conexión desde esta instancia
# Verificar credenciales en .env
```

### Error: "NFS mount failed"

```bash
# Verificar que servidor NFS está corriendo
ping <NFS_PRIVATE_IP>

# Verificar exports en servidor NFS
showmount -e <NFS_PRIVATE_IP>

# Ver logs del sistema
sudo journalctl -xe | grep mount

# Intentar montar manualmente
sudo mount -t nfs <NFS_IP>:/mnt/nfs_share/uploads /mnt/nfs_uploads
```

### Error: "Redis connection refused"

```bash
# Verificar que Redis está corriendo
docker-compose ps redis

# Ver logs de Redis
docker-compose logs redis

# Probar conexión
docker exec -it anb-redis redis-cli ping
```

### Backend no responde

```bash
# Ver logs del backend
docker-compose logs backend

# Verificar variables de entorno
docker exec -it anb-backend env | grep DATABASE_URL

# Reiniciar backend
docker-compose restart backend
```

### Nginx 502 Bad Gateway

```bash
# Verificar que backend está corriendo
docker-compose ps backend

# Ver logs de nginx
docker-compose logs nginx

# Verificar configuración de nginx
docker exec -it anb-nginx nginx -t
```

---

## Monitoreo Continuo

### Logs en tiempo real
```bash
# Mantener terminal abierta monitoreando logs
docker-compose logs -f --tail=100
```

### Health checks automáticos
Los contenedores tienen health checks configurados. Verifica con:

```bash
docker-compose ps
```

---

## Backup y Rollback

### Crear snapshot del volumen Redis

```bash
# Exportar datos de Redis
docker exec anb-redis redis-cli SAVE

# Copiar dump.rdb desde el contenedor
docker cp anb-redis:/data/dump.rdb ~/redis-backup-$(date +%F).rdb
```

### Rollback a versión anterior

```bash
# Si tienes versión anterior en git
git checkout <previous-commit>
docker-compose up -d --build
```

---

## Siguientes Pasos

Una vez que el Backend esté funcionando correctamente:

1. ✅ Backend desplegado y funcionando
2. ⏭️ Desplegar instancia Worker
3. ⏭️ Probar flujo completo de upload y procesamiento
4. ⏭️ Configurar monitoreo y alertas
5. ⏭️ Configurar backups automáticos

---

## Comandos Rápidos de Referencia

```bash
# Montaje NFS
./setup-nfs-mount.sh

# Levantar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar salud
docker-compose ps
curl http://localhost/health

# Migraciones
docker exec -it anb-backend alembic upgrade head

# Reiniciar
docker-compose restart

# Detener
docker-compose down
```
