# Configuración de IAM Role para S3 (AWS Academy)

Este documento explica cómo configurar el acceso a S3 usando IAM Role (LabRole) en AWS Academy, eliminando la necesidad de credenciales manuales.

## Tabla de Contenidos
- [¿Por qué usar IAM Role?](#por-qué-usar-iam-role)
- [Opción 1: IAM Role (Recomendado)](#opción-1-iam-role-recomendado)
- [Opción 2: Credenciales Manuales](#opción-2-credenciales-manuales)
- [Cómo funciona internamente](#cómo-funciona-internamente)

---

## ¿Por qué usar IAM Role?

### Ventajas de IAM Role vs Credenciales Manuales

| Aspecto | IAM Role (LabRole) | Credenciales Manuales |
|---------|-------------------|----------------------|
| **Seguridad** | ✅ No expone credenciales | ❌ Credenciales en .env |
| **Mantenimiento** | ✅ Automático | ❌ Requiere rotación manual |
| **Setup** | ✅ Solo asignar role en EC2 | ❌ Ejecutar setup-s3.sh |
| **Producción** | ✅ Recomendado por AWS | ❌ No recomendado |
| **Expiración** | ✅ No expiran | ❌ AWS Academy expira cada 4h |

---

## Opción 1: IAM Role (Recomendado)

### Paso 1: Asignar LabRole a la instancia EC2

#### Durante la creación de la instancia:

1. **En AWS Console** → EC2 → Launch Instance
2. En la sección **"Advanced details"**
3. Buscar **"IAM instance profile"**
4. Seleccionar: **`LabInstanceProfile`** o **`LabRole`**

```
IAM instance profile: LabInstanceProfile
```

#### Para una instancia existente:

1. **EC2 Console** → Selecciona tu instancia
2. **Actions** → **Security** → **Modify IAM role**
3. Seleccionar: **`LabInstanceProfile`**
4. Click **"Update IAM role"**

### Paso 2: Configurar .env (Sin credenciales)

```bash
# ===== ALMACENAMIENTO S3 =====
FILE_STORAGE_TYPE=s3
S3_BUCKET_NAME=anb-rising-stars-bucket
AWS_REGION=us-east-1

# NO necesitas estas variables:
# AWS_ACCESS_KEY_ID=
# AWS_SECRET_ACCESS_KEY=
# AWS_SESSION_TOKEN=
```

### Paso 3: Crear el bucket S3 (Una sola vez)

```bash
# Desde AWS Console o CLI (si tienes AWS CLI local)
aws s3 mb s3://anb-rising-stars-bucket --region us-east-1

# Crear estructura de carpetas
aws s3api put-object --bucket anb-rising-stars-bucket --key original/
aws s3api put-object --bucket anb-rising-stars-bucket --key processed/
```

O usar la consola de AWS S3:
1. S3 Console → Create bucket
2. Bucket name: `anb-rising-stars-bucket`
3. Region: `us-east-1`
4. Create bucket

### Paso 4: Levantar Docker (NO necesitas setup-s3.sh)

```bash
cd /path/to/deployment/backend-instance

# Directamente levantar Docker Compose
docker-compose up -d
```

**✅ Listo! El código automáticamente usará el IAM Role**

Los logs mostrarán:
```
☁️ S3Storage inicializado con IAM Role: bucket=anb-rising-stars-bucket, region=us-east-1
```

---

## Opción 2: Credenciales Manuales

Solo usar esta opción si:
- Desarrollas localmente (fuera de EC2)
- No puedes asignar IAM Role a la instancia

### Paso 1: Obtener credenciales de AWS Academy

1. **AWS Academy Learner Lab** → Click "AWS Details"
2. Click **"Show"** en "AWS CLI"
3. Copiar las credenciales:

```bash
[default]
aws_access_key_id=ASIAIOSFODNN7EXAMPLE
aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
aws_session_token=FwoGZXIvYXdzEBQaD...
```

### Paso 2: Configurar .env

```bash
# ===== ALMACENAMIENTO S3 =====
FILE_STORAGE_TYPE=s3
S3_BUCKET_NAME=anb-rising-stars-bucket
AWS_REGION=us-east-1

# Credenciales de AWS Academy
AWS_ACCESS_KEY_ID=ASIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_SESSION_TOKEN=FwoGZXIvYXdzEBQaD...
```

### Paso 3: Ejecutar setup-s3.sh

```bash
cd /path/to/deployment/backend-instance
./setup-s3.sh
```

Este script:
- Valida las credenciales
- Instala AWS CLI
- Configura `~/.aws/credentials`
- Crea el bucket S3 si no existe

### Paso 4: Levantar Docker

```bash
docker-compose up -d
```

Los logs mostrarán:
```
☁️ S3Storage inicializado con credenciales explícitas: bucket=anb-rising-stars-bucket, region=us-east-1
```

---

## Cómo funciona internamente

### Cadena de credenciales de boto3

El SDK de AWS (boto3) busca credenciales en este orden:

```
1. Parámetros explícitos → aws_access_key_id, aws_secret_access_key (si están en .env)
2. IAM Role (Instance Profile) → Automático si está asignado a EC2
3. Variables de entorno → AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
4. Archivo ~/.aws/credentials → Creado por setup-s3.sh
```

### Código modificado (Backend y Worker)

```python
# backend/app/infrastructure/external_services/s3_file_storage.py
class S3FileStorage:
    def __init__(self, bucket_name: str, region: str = "us-east-1",
                 access_key: str = None, secret_key: str = None,
                 session_token: str = None):

        if access_key and secret_key:
            # Opción 1: Credenciales explícitas (AWS Academy)
            self.s3_client = boto3.client(
                's3',
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token
            )
        else:
            # Opción 2: IAM Role (automático) ✅
            self.s3_client = boto3.client('s3', region_name=region)
```

### Flujo de decisión

```mermaid
graph TD
    A[Iniciar aplicación] --> B{¿Hay AWS_ACCESS_KEY_ID<br/>en .env?}
    B -->|Sí| C[Usar credenciales explícitas]
    B -->|No| D{¿Instancia tiene<br/>IAM Role?}
    D -->|Sí| E[Usar IAM Role ✅]
    D -->|No| F[Usar ~/.aws/credentials]
    F -->|No existe| G[ERROR: Sin credenciales]
```

---

## Verificación

### Verificar que IAM Role está asignado

**Desde la instancia EC2:**

```bash
# Debe retornar información del role
curl http://169.xxx.xxx.xxx/latest/meta-data/iam/security-credentials/

# Debe retornar credenciales temporales
curl http://169.xxx.xxx.xxx/latest/meta-data/iam/security-credentials/LabRole
```

**Respuesta esperada:**
```json
{
  "Code" : "Success",
  "LastUpdated" : "2025-01-09T12:00:00Z",
  "Type" : "AWS-HMAC",
  "AccessKeyId" : "ASIAIOSFODNN7EXAMPLE",
  "SecretAccessKey" : "wJalrXUt...",
  "Token" : "FwoGZXIv...",
  "Expiration" : "2025-01-09T18:00:00Z"
}
```

### Verificar acceso a S3

**Desde el contenedor Docker:**

```bash
# Entrar al contenedor
docker exec -it anb-backend bash

# Intentar listar el bucket (debe funcionar)
python -c "import boto3; print(boto3.client('s3').list_buckets())"
```

---

## Troubleshooting

### Error: "Unable to locate credentials"

**Causa:** No hay credenciales ni IAM Role configurado

**Solución:**
1. Verificar que IAM Role está asignado (ver arriba)
2. O configurar credenciales en .env y ejecutar setup-s3.sh

### Error: "Access Denied"

**Causa:** LabRole no tiene permisos de S3

**Solución:** En AWS Academy, LabRole debería tener permisos completos. Verificar:
```bash
aws iam get-role --role-name LabRole
```

### Error: "Session token expired"

**Causa:** Las credenciales manuales de AWS Academy expiraron (cada 4 horas)

**Solución:**
1. Usar IAM Role (no expira) ✅
2. O renovar credenciales en AWS Academy y actualizar .env

---

## ARN del IAM Role

```
arn:aws:iam::682027153051:role/LabRole
```

Este role tiene los permisos necesarios para:
- S3 (lectura/escritura)
- SQS (envío/recepción de mensajes)
- CloudWatch Logs
- EC2 Instance Metadata

---

## Resumen de Comandos

### Con IAM Role (Recomendado)

```bash
# 1. Asignar LabRole en AWS Console → EC2 → IAM instance profile

# 2. Configurar .env (sin credenciales)
FILE_STORAGE_TYPE=s3
S3_BUCKET_NAME=anb-rising-stars-bucket

# 3. Levantar Docker
docker-compose up -d
```

### Con Credenciales Manuales

```bash
# 1. Configurar .env (con credenciales de AWS Academy)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...

# 2. Ejecutar setup
./setup-s3.sh

# 3. Levantar Docker
docker-compose up -d
```

---

**Recomendación:** Usar IAM Role para producción y testing. Solo usar credenciales manuales para desarrollo local.
