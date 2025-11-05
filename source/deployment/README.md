# 📚 Documentación de Despliegue - AWS EC2

## ANB Rising Stars Showcase - Arquitectura Distribuida

Esta carpeta contiene toda la documentación necesaria para desplegar el proyecto ANB Rising Stars en AWS EC2 con una arquitectura de microservicios distribuidos.

---

## 🚀 Empezar Ahora

### **Para desplegar paso a paso, ve a:**

➡️ **[GET_STARTED.md](./GET_STARTED.md)** - Guía completa de instalación desde cero

Esta es la guía principal que te llevará paso a paso desde la creación de Security Groups hasta tener toda la aplicación funcionando.

**Tiempo estimado:** 2.5 - 3 horas

---

## 📁 Estructura de Archivos

```
deployment/
├── README.md                    # Este archivo (índice general)
├── GET_STARTED.md              # 🚀 GUÍA PRINCIPAL - Empieza aquí
├── ARCHITECTURE.md             # Diagramas detallados de arquitectura
├── SECURITY_GROUPS.md          # Configuración de Security Groups
├── NFS_SERVER_SETUP.md         # Configuración del servidor NFS
│
├── backend-instance/           # Configuración para instancia Backend
│   ├── DEPLOY.md              # Guía de despliegue Backend
│   ├── docker-compose.yml     # Nginx + Redis + Backend
│   ├── nginx.conf             # Configuración Nginx
│   ├── .env.example           # Variables de entorno
│   └── setup-nfs-mount.sh     # Script montaje NFS
│
└── worker-instance/            # Configuración para instancia Worker
    ├── DEPLOY.md              # Guía de despliegue Worker
    ├── docker-compose.yml     # Celery Worker
    ├── .env.example           # Variables de entorno
    ├── setup-nfs-mount.sh     # Script montaje NFS
    └── assets/                # Logo, intro, outro (agregar aquí)
```

---

## 🏗️ Arquitectura del Sistema

### Arquitectura con NFS (Opción 1)
```
Internet → Backend EC2 (Nginx + FastAPI + Redis) → RDS PostgreSQL
              ↓                    ↓
         NFS Server  ←────── Worker EC2 (Celery + FFmpeg)
```

### Arquitectura con S3 (Opción 2)
```
Internet → Backend EC2 (Nginx + FastAPI + Redis) → RDS PostgreSQL
              ↓                    ↓
           AWS S3   ←────── Worker EC2 (Celery + FFmpeg)
```

### Componentes:

| Instancia | Servicios | Puertos | Tipo EC2 |
|-----------|-----------|---------|----------|
| **Backend** | Nginx, FastAPI, Redis | 80, 8000, 6379 | t2.medium |
| **Worker** | Celery, FFmpeg, Health API | 8001 | t2.large |
| **NFS Server** (opcional) | NFS | 2049, 111 | t2.small + 50GB EBS |
| **S3 Bucket** (opcional) | Almacenamiento de objetos | - | - |
| **RDS** | PostgreSQL | 5432 | db.t3.micro |

---

## 📖 Guías Especializadas

### Guía Principal
- **[GET_STARTED.md](./GET_STARTED.md)** - Guía paso a paso completa

### Documentación Técnica
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Diagramas detallados y flujo de datos
- **[SECURITY_GROUPS.md](./SECURITY_GROUPS.md)** - Configuración de firewall AWS
- **[NFS_SERVER_SETUP.md](./NFS_SERVER_SETUP.md)** - Servidor de almacenamiento compartido

### Configuración por Instancia
- **[backend-instance/DEPLOY.md](./backend-instance/DEPLOY.md)** - Despliegue del Backend
- **[worker-instance/DEPLOY.md](./worker-instance/DEPLOY.md)** - Despliegue del Worker

---

## 💾 Configuración de Almacenamiento

El sistema soporta **dos opciones de almacenamiento** para videos (original y procesados):

### Opción 1: NFS (Network File System)
**Recomendado para:** Desarrollo, testing, o ambientes con infraestructura on-premise.

**Ventajas:**
- ✅ Acceso más rápido (sin latencia de red a internet)
- ✅ Menor complejidad de configuración
- ✅ Sin costos de transferencia de datos
- ✅ Compartido entre Backend y Worker

**Desventajas:**
- ❌ Requiere gestión manual del servidor NFS
- ❌ Escalabilidad limitada
- ❌ Requiere una instancia EC2 adicional

**Pasos para configurar NFS:**
1. Crear servidor NFS (ver [NFS_SERVER_SETUP.md](./NFS_SERVER_SETUP.md))
2. En Backend: `FILE_STORAGE_TYPE=local` en `.env`
3. En Worker: `STORAGE_TYPE=local` en `.env`
4. Ejecutar `./setup-nfs-mount.sh` en ambas instancias
5. Mantener volumen activo en `docker-compose.yml`

### Opción 2: AWS S3
**Recomendado para:** Producción, alta disponibilidad, escalabilidad.

**Ventajas:**
- ✅ Escalabilidad ilimitada
- ✅ Alta disponibilidad (99.99%)
- ✅ No requiere gestión de servidores
- ✅ Costos basados en uso
- ✅ Versionamiento y lifecycle policies
- ✅ Integración con CloudFront (CDN)

**Desventajas:**
- ❌ Latencia de red para descargas/uploads
- ❌ Costos de transferencia de datos
- ❌ Mayor complejidad de configuración inicial

**Pasos para configurar S3:**
1. Crear bucket S3 en AWS
2. Crear usuario IAM con permisos S3
3. En Backend: `FILE_STORAGE_TYPE=s3` + configurar credenciales AWS en `.env`
4. En Worker: `STORAGE_TYPE=s3` + configurar credenciales AWS en `.env`
5. Ejecutar `./setup-s3.sh` en ambas instancias
6. Comentar volumen NFS en `docker-compose.yml`

**Archivos de configuración:**
- Backend: [backend-instance/.env.example](./backend-instance/.env.example)
- Worker: [worker-instance/.env.example](./worker-instance/.env.example)

**Scripts de setup:**
- Backend NFS: [backend-instance/setup-nfs-mount.sh](./backend-instance/setup-nfs-mount.sh)
- Backend S3: [backend-instance/setup-s3.sh](./backend-instance/setup-s3.sh)
- Worker NFS: [worker-instance/setup-nfs-mount.sh](./worker-instance/setup-nfs-mount.sh)
- Worker S3: [worker-instance/setup-s3.sh](./worker-instance/setup-s3.sh)

---

## 🎯 Orden de Despliegue Recomendado

### Con NFS (Opción 1)

1. **Crear Security Groups** (15 min) → [GET_STARTED.md#paso-1](./GET_STARTED.md#paso-1-crear-security-groups-15-min)
2. **Crear RDS PostgreSQL** (30 min) → [GET_STARTED.md#paso-2](./GET_STARTED.md#paso-2-crear-rds-postgresql-30-min)
3. **Configurar Servidor NFS** (45 min) → [GET_STARTED.md#paso-3](./GET_STARTED.md#paso-3-crear-y-configurar-servidor-nfs-45-min)
4. **Desplegar Backend** (60 min) → [GET_STARTED.md#paso-4](./GET_STARTED.md#paso-4-crear-instancia-backend-15-min)
5. **Desplegar Worker** (45 min) → [GET_STARTED.md#paso-5](./GET_STARTED.md#paso-5-crear-instancia-worker-30-min)
6. **Verificar End-to-End** (15 min) → [GET_STARTED.md#paso-6](./GET_STARTED.md#paso-6-verificación-end-to-end-15-min)

**Tiempo total:** 3-4 horas

### Con S3 (Opción 2)

1. **Crear Security Groups** (15 min) → [GET_STARTED.md#paso-1](./GET_STARTED.md#paso-1-crear-security-groups-15-min)
2. **Crear RDS PostgreSQL** (30 min) → [GET_STARTED.md#paso-2](./GET_STARTED.md#paso-2-crear-rds-postgresql-30-min)
3. **Crear Bucket S3 y usuario IAM** (20 min)
   - Crear bucket en S3 con nombre único
   - Crear usuario IAM con permisos: `AmazonS3FullAccess`
   - Guardar Access Key ID y Secret Access Key
4. **Desplegar Backend** (60 min) → [GET_STARTED.md#paso-4](./GET_STARTED.md#paso-4-crear-instancia-backend-15-min)
   - Configurar `FILE_STORAGE_TYPE=s3` en `.env`
   - Ejecutar `./setup-s3.sh` en lugar de `./setup-nfs-mount.sh`
   - Comentar volumen NFS en `docker-compose.yml`
5. **Desplegar Worker** (45 min) → [GET_STARTED.md#paso-5](./GET_STARTED.md#paso-5-crear-instancia-worker-30-min)
   - Configurar `STORAGE_TYPE=s3` en `.env`
   - Ejecutar `./setup-s3.sh` en lugar de `./setup-nfs-mount.sh`
   - Comentar volumen NFS en `docker-compose.yml`
6. **Verificar End-to-End** (15 min) → [GET_STARTED.md#paso-6](./GET_STARTED.md#paso-6-verificación-end-to-end-15-min)

**Tiempo total:** 2.5-3 horas (sin servidor NFS)

---

## 🔧 Tecnologías Utilizadas

### Backend
- FastAPI (Python 3.11)
- Nginx (Alpine)
- Redis 7
- PostgreSQL 15 (RDS)
- Docker & Docker Compose

### Worker
- Celery (Python 3.11)
- FFmpeg
- Redis (broker)
- NFS Client

### Infraestructura AWS
- EC2 (Ubuntu 22.04 LTS)
- RDS PostgreSQL
- VPC & Security Groups
- EBS Volumes

---
---

## 🐛 Troubleshooting Rápido

| Problema | Dónde buscar |
|----------|--------------|
| Backend no inicia | [backend-instance/DEPLOY.md](./backend-instance/DEPLOY.md#troubleshooting) |
| Worker no procesa videos | [worker-instance/DEPLOY.md](./worker-instance/DEPLOY.md#troubleshooting) |
| NFS mount failed | [NFS_SERVER_SETUP.md](./NFS_SERVER_SETUP.md#troubleshooting) |
| Security Groups | [SECURITY_GROUPS.md](./SECURITY_GROUPS.md#troubleshooting) |

---

## 📞 Soporte

Para problemas o dudas:
1. Revisa los logs: `docker-compose logs -f`
2. Verifica health checks
3. Consulta la sección de Troubleshooting de cada guía
4. Revisa [ARCHITECTURE.md](./ARCHITECTURE.md) para entender el flujo

---

## 🚀 ¡Empieza Ahora!

➡️ **[Ir a GET_STARTED.md](./GET_STARTED.md)**

---

**Última actualización:** Octubre 2025
**Versión:** 1.0
