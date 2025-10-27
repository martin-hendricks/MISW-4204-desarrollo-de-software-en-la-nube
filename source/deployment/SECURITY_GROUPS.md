# Configuración de Security Groups - AWS

## Resumen de la Arquitectura

```
Internet (0.0.0.0/0)
    │
    ↓ HTTP:80, SSH:22
┌────────────────────────┐
│  EC2 Backend Instance  │
│  - Nginx (80)          │
│  - Backend API (8000)  │
│  - Redis (6379)        │◄──────────┐
│  - Flower (5555)       │           │
└────────┬───────────────┘           │
         │                           │ Redis:6379
         │ NFS:2049                  │
         ↓                           │
┌────────────────────────┐           │
│   EC2 NFS Server       │           │
│   - NFS (2049)         │           │
│   - RPC (111)          │◄──────┐   │
└────────┬───────────────┘       │   │
         ↑                       │   │
         │ NFS:2049              │   │
         │                       │   │
┌────────────────────────┐       │   │
│  EC2 Worker Instance   │───────┘   │
│  - Celery Worker       │           │
│  - Health API (8001)   │───────────┘
└────────────────────────┘
         │
         │ PostgreSQL:5432
         ↓
┌────────────────────────┐
│   RDS PostgreSQL       │
│   - DB (5432)          │
└────────────────────────┘
```

---

## Security Group 1: Backend Instance

**Nombre:** `anb-backend-sg`

### Inbound Rules

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | Your IP / 0.0.0.0/0 | SSH access for administration |
| HTTP | TCP | 80 | 0.0.0.0/0 | Public access to Nginx |
| Custom TCP | TCP | 8000 | Your IP | Direct Backend API access (debug only) |
| Custom TCP | TCP | 5555 | Your IP | Flower monitoring UI |
| Custom TCP | TCP | 6379 | anb-worker-sg | Redis access from Worker |

### Outbound Rules

| Type | Protocol | Port Range | Destination | Description |
|------|----------|------------|-------------|-------------|
| All traffic | All | All | 0.0.0.0/0 | Allow all outbound (default) |

### Configuración AWS CLI

```bash
# Crear Security Group
aws ec2 create-security-group \
  --group-name anb-backend-sg \
  --description "Security group for ANB Backend instance (Nginx + Redis + API)"

# Obtener tu IP pública
MY_IP=$(curl -s ifconfig.me)

# Agregar reglas inbound
aws ec2 authorize-security-group-ingress \
  --group-name anb-backend-sg \
  --protocol tcp --port 22 --cidr $MY_IP/32

aws ec2 authorize-security-group-ingress \
  --group-name anb-backend-sg \
  --protocol tcp --port 80 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-name anb-backend-sg \
  --protocol tcp --port 8000 --cidr $MY_IP/32

aws ec2 authorize-security-group-ingress \
  --group-name anb-backend-sg \
  --protocol tcp --port 5555 --cidr $MY_IP/32

# Regla para Worker (agregar después de crear anb-worker-sg)
aws ec2 authorize-security-group-ingress \
  --group-name anb-backend-sg \
  --protocol tcp --port 6379 \
  --source-group anb-worker-sg
```

---

## Security Group 2: Worker Instance

**Nombre:** `anb-worker-sg`

### Inbound Rules

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | Your IP / 0.0.0.0/0 | SSH access for administration |
| Custom TCP | TCP | 8001 | Your IP | Health API access (debug) |
| Custom TCP | TCP | 8001 | anb-backend-sg | Health checks from Backend (optional) |

### Outbound Rules

| Type | Protocol | Port Range | Destination | Description |
|------|----------|------------|-------------|-------------|
| All traffic | All | All | 0.0.0.0/0 | Allow all outbound (default) |

**Nota:** El Worker necesita conectarse a:
- Backend (Redis): puerto 6379
- NFS Server: puerto 2049, 111
- RDS: puerto 5432

Esto se permite por la regla "All traffic" en Outbound.

### Configuración AWS CLI

```bash
# Crear Security Group
aws ec2 create-security-group \
  --group-name anb-worker-sg \
  --description "Security group for ANB Worker instance (Celery + FFmpeg)"

# Obtener tu IP pública
MY_IP=$(curl -s ifconfig.me)

# Agregar reglas inbound
aws ec2 authorize-security-group-ingress \
  --group-name anb-worker-sg \
  --protocol tcp --port 22 --cidr $MY_IP/32

aws ec2 authorize-security-group-ingress \
  --group-name anb-worker-sg \
  --protocol tcp --port 8001 --cidr $MY_IP/32

# Regla opcional para Backend
aws ec2 authorize-security-group-ingress \
  --group-name anb-worker-sg \
  --protocol tcp --port 8001 \
  --source-group anb-backend-sg
```

---

## Security Group 3: NFS Server

**Nombre:** `anb-nfs-sg`

### Inbound Rules

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| SSH | TCP | 22 | Your IP / 0.0.0.0/0 | SSH access for administration |
| NFS | TCP | 2049 | anb-backend-sg | NFS access from Backend |
| NFS | TCP | 2049 | anb-worker-sg | NFS access from Worker |
| Custom TCP | TCP | 111 | anb-backend-sg | RPC Portmapper from Backend |
| Custom TCP | TCP | 111 | anb-worker-sg | RPC Portmapper from Worker |
| Custom UDP | UDP | 111 | anb-backend-sg | RPC Portmapper UDP from Backend |
| Custom UDP | UDP | 111 | anb-worker-sg | RPC Portmapper UDP from Worker |

### Outbound Rules

| Type | Protocol | Port Range | Destination | Description |
|------|----------|------------|-------------|-------------|
| All traffic | All | All | 0.0.0.0/0 | Allow all outbound (default) |

### Configuración AWS CLI

```bash
# Crear Security Group
aws ec2 create-security-group \
  --group-name anb-nfs-sg \
  --description "Security group for ANB NFS Server"

# Obtener tu IP pública
MY_IP=$(curl -s ifconfig.me)

# Agregar reglas inbound
aws ec2 authorize-security-group-ingress \
  --group-name anb-nfs-sg \
  --protocol tcp --port 22 --cidr $MY_IP/32

# NFS desde Backend
aws ec2 authorize-security-group-ingress \
  --group-name anb-nfs-sg \
  --protocol tcp --port 2049 \
  --source-group anb-backend-sg

# NFS desde Worker
aws ec2 authorize-security-group-ingress \
  --group-name anb-nfs-sg \
  --protocol tcp --port 2049 \
  --source-group anb-worker-sg

# RPC Portmapper TCP desde Backend
aws ec2 authorize-security-group-ingress \
  --group-name anb-nfs-sg \
  --protocol tcp --port 111 \
  --source-group anb-backend-sg

# RPC Portmapper TCP desde Worker
aws ec2 authorize-security-group-ingress \
  --group-name anb-nfs-sg \
  --protocol tcp --port 111 \
  --source-group anb-worker-sg

# RPC Portmapper UDP desde Backend
aws ec2 authorize-security-group-ingress \
  --group-name anb-nfs-sg \
  --protocol udp --port 111 \
  --source-group anb-backend-sg

# RPC Portmapper UDP desde Worker
aws ec2 authorize-security-group-ingress \
  --group-name anb-nfs-sg \
  --protocol udp --port 111 \
  --source-group anb-worker-sg
```

---

## Security Group 4: RDS PostgreSQL

**Nombre:** `anb-rds-sg`

### Inbound Rules

| Type | Protocol | Port Range | Source | Description |
|------|----------|------------|--------|-------------|
| PostgreSQL | TCP | 5432 | anb-backend-sg | Database access from Backend |
| PostgreSQL | TCP | 5432 | anb-worker-sg | Database access from Worker |
| PostgreSQL | TCP | 5432 | Your IP | Direct DB access (optional, for debugging) |

### Outbound Rules

| Type | Protocol | Port Range | Destination | Description |
|------|----------|------------|-------------|-------------|
| All traffic | All | All | 0.0.0.0/0 | Allow all outbound (default) |

### Configuración AWS CLI

```bash
# Crear Security Group
aws ec2 create-security-group \
  --group-name anb-rds-sg \
  --description "Security group for ANB RDS PostgreSQL"

# Obtener tu IP pública
MY_IP=$(curl -s ifconfig.me)

# Agregar reglas inbound
aws ec2 authorize-security-group-ingress \
  --group-name anb-rds-sg \
  --protocol tcp --port 5432 \
  --source-group anb-backend-sg

aws ec2 authorize-security-group-ingress \
  --group-name anb-rds-sg \
  --protocol tcp --port 5432 \
  --source-group anb-worker-sg

# Opcional: Acceso directo para debugging (puedes eliminar en producción)
aws ec2 authorize-security-group-ingress \
  --group-name anb-rds-sg \
  --protocol tcp --port 5432 --cidr $MY_IP/32
```

---

## Resumen de Puertos por Servicio

### Backend Instance (anb-backend-sg)
- **22** (SSH): Administración
- **80** (HTTP): Nginx - Acceso público
- **8000** (Custom): Backend API - Debug
- **5555** (Custom): Flower - Monitoring
- **6379** (Custom): Redis - Desde Worker

### Worker Instance (anb-worker-sg)
- **22** (SSH): Administración
- **8001** (Custom): Health API

### NFS Server (anb-nfs-sg)
- **22** (SSH): Administración
- **2049** (NFS): NFS Server
- **111** (TCP/UDP): RPC Portmapper

### RDS PostgreSQL (anb-rds-sg)
- **5432** (PostgreSQL): Database

---

## Diagrama de Flujo de Tráfico

```
┌─────────────┐
│   Internet  │
└──────┬──────┘
       │
       │ :80 (HTTP)
       ↓
┌──────────────────┐
│  Backend EC2     │
│  anb-backend-sg  │
└────┬──────┬──────┘
     │      │
     │      │ :6379 (Redis)
     │      ↓
     │  ┌──────────────────┐
     │  │  Worker EC2      │
     │  │  anb-worker-sg   │
     │  └────┬──────┬──────┘
     │       │      │
     │       │      │ :5432 (PostgreSQL)
     │       │      ↓
     │ :2049 │  ┌──────────────────┐
     │ (NFS) │  │  RDS PostgreSQL  │
     │       │  │  anb-rds-sg      │
     │       │  └──────────────────┘
     │       │
     ↓       ↓ :2049 (NFS)
┌──────────────────┐
│  NFS Server EC2  │
│  anb-nfs-sg      │
└──────────────────┘
```

---

## Orden de Creación Recomendado

Para evitar errores de referencias circulares al crear los Security Groups:

1. **Crear todos los Security Groups vacíos primero:**
   ```bash
   aws ec2 create-security-group --group-name anb-backend-sg --description "Backend SG"
   aws ec2 create-security-group --group-name anb-worker-sg --description "Worker SG"
   aws ec2 create-security-group --group-name anb-nfs-sg --description "NFS SG"
   aws ec2 create-security-group --group-name anb-rds-sg --description "RDS SG"
   ```

2. **Agregar reglas que no dependen de otros SGs:**
   - SSH (puerto 22) desde tu IP
   - HTTP (puerto 80) público en Backend
   - Puertos de debug desde tu IP

3. **Agregar reglas que referencian otros SGs:**
   - Redis (6379) en Backend desde Worker
   - NFS (2049) en NFS Server desde Backend y Worker
   - PostgreSQL (5432) en RDS desde Backend y Worker

---

## Verificación de Conectividad

### Desde Backend a RDS:

```bash
# En instancia Backend
telnet <RDS_ENDPOINT> 5432
```

### Desde Backend a NFS:

```bash
# En instancia Backend
telnet <NFS_PRIVATE_IP> 2049
showmount -e <NFS_PRIVATE_IP>
```

### Desde Worker a Backend (Redis):

```bash
# En instancia Worker
telnet <BACKEND_PRIVATE_IP> 6379
redis-cli -h <BACKEND_PRIVATE_IP> ping
```

### Desde Worker a RDS:

```bash
# En instancia Worker
telnet <RDS_ENDPOINT> 5432
```

### Desde Worker a NFS:

```bash
# En instancia Worker
telnet <NFS_PRIVATE_IP> 2049
showmount -e <NFS_PRIVATE_IP>
```

---

## Troubleshooting

### Error: "Connection timed out"

1. Verificar que el Security Group de destino tiene la regla correcta
2. Verificar que estás usando la IP/SG correcto en la regla
3. Verificar que el servicio está corriendo en el puerto esperado
4. Verificar que estás en la misma VPC (si usas IPs privadas)

### Error: "Connection refused"

1. El Security Group está correcto
2. Pero el servicio no está corriendo en ese puerto
3. Verificar con: `netstat -tuln | grep <PORT>`

### Cambiar reglas después de la creación:

```bash
# Eliminar regla
aws ec2 revoke-security-group-ingress \
  --group-name anb-backend-sg \
  --protocol tcp --port 8000 --cidr 0.0.0.0/0

# Agregar nueva regla
aws ec2 authorize-security-group-ingress \
  --group-name anb-backend-sg \
  --protocol tcp --port 8000 --cidr <NEW_IP>/32
```

---

## Mejores Prácticas de Seguridad

### 1. Principio de Menor Privilegio
- ✅ Abre solo los puertos necesarios
- ✅ Restringe acceso SSH a tu IP
- ✅ No expongas puertos de debug (8000, 8001, 5555) a 0.0.0.0/0

### 2. Usa Referencias a Security Groups
- ✅ En lugar de IPs privadas, usa referencias a SGs
- ✅ Más flexible si cambias instancias
- ✅ Ejemplo: `--source-group anb-worker-sg`

### 3. Separa ambientes
- ✅ Usa tags para identificar ambiente: `Environment=production`
- ✅ Crea SGs separados para dev/staging/prod
- ✅ Nunca compartas SGs entre ambientes

### 4. Documentación
- ✅ Usa descripciones claras en cada regla
- ✅ Documenta el propósito de cada puerto
- ✅ Mantén este documento actualizado

### 5. Auditoría regular
- ✅ Revisa reglas cada mes
- ✅ Elimina reglas no usadas
- ✅ Verifica que no hay puertos abiertos a 0.0.0.0/0 innecesariamente

---

## Script Automatizado de Creación

Ver archivo: [create-security-groups.sh](./scripts/create-security-groups.sh)

```bash
#!/bin/bash
# Script completo para crear todos los Security Groups
# Ejecutar: ./create-security-groups.sh
```

---

## Referencias

- [AWS Security Groups Documentation](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
- [NFS Port Requirements](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/storage_administration_guide/nfs-serverconfig)
- [PostgreSQL Network Security](https://www.postgresql.org/docs/current/runtime-config-connection.html)
