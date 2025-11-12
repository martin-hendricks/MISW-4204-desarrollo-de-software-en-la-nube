# Infraestructura Terraform - ANB Rising Stars

Este proyecto de Terraform crea la infraestructura completa en AWS para la aplicación ANB Rising Stars.

## Componentes Creados

- **VPC** con subnets públicas y privadas en 2 zonas de disponibilidad
- **Application Load Balancer** (ELB) con Target Group
- **Auto Scaling Group** para backend (min: 1, max: 3, desired: 1)
  - Política de escalado por RequestCountPerTarget (40 requests/instancia)
  - Política de escalado por CPU (50%)
- **Instancias EC2**:
  - `performance`: t3.small
  - `worker`: t3.small
- **RDS PostgreSQL** (db.t3.micro) con inicialización automática
- **SQS Queues**:
  - `anb-nube-video-processing-queue` (cola principal)
  - `anb-nube-video-processing-dlq` (Dead Letter Queue)
- **S3 Bucket**: `anb-videos-bucket-25` con folders `original/` y `processed/`
- **Key Pair**: `clavemac` para acceso SSH a todas las instancias
- **IAM**: Asignación de `LabRole` a todas las instancias

## Requisitos Previos

1. **Terraform** instalado (versión >= 1.0)
2. **AWS CLI** instalado (opcional, para verificación)
3. **PostgreSQL client** instalado localmente (para inicialización de RDS):
   ```bash
   # macOS
   brew install postgresql
   
   # Ubuntu/Debian
   sudo apt install postgresql-client
   ```
4. **Credenciales de AWS Academy**:
   - Access Key ID
   - Secret Access Key
   - Session Token (si es necesario)

## Configuración

### Paso 1: Configurar Variables

Copia el archivo de ejemplo y completa con tus valores:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edita `terraform.tfvars` con tus credenciales:

```hcl
aws_region = "us-east-1"
aws_access_key_id     = "TU_ACCESS_KEY_ID"
aws_secret_access_key = "TU_SECRET_ACCESS_KEY"
aws_session_token     = "TU_SESSION_TOKEN"  # Solo si es necesario
rds_password = "root1234"
allowed_ssh_cidr = "TU_IP/32"  # Ejemplo: "203.0.113.1/32"
```

**⚠️ IMPORTANTE**: 
- `terraform.tfvars` está en `.gitignore` y no se subirá al repositorio
- Cambia `allowed_ssh_cidr` a tu IP específica para mayor seguridad
- No compartas tus credenciales

### Paso 2: Obtener Credenciales de AWS Academy

1. Inicia sesión en AWS Academy
2. Ve a "AWS Details" o "Account Details"
3. Copia:
   - AWS Access Key ID
   - AWS Secret Access Key
   - AWS Session Token (si está disponible)

### Paso 3: Verificar que LabRole Existe

El plan asume que `LabRole` ya existe en tu cuenta de AWS Academy. Si no existe, deberás crearlo manualmente o ajustar el código.

## Uso

### Inicializar Terraform

```bash
cd terraform
terraform init
```

### Validar la Configuración

```bash
terraform validate
```

### Ver el Plan de Ejecución

```bash
terraform plan
```

Este comando mostrará todos los recursos que se crearán. Revisa cuidadosamente antes de continuar.

### Aplicar la Configuración

```bash
terraform apply
```

Terraform te pedirá confirmación. Escribe `yes` para continuar.

**⏱️ Tiempo estimado**: 15-20 minutos (principalmente por RDS)

### Ver Outputs

Después de aplicar, puedes ver los outputs importantes:

```bash
terraform output
```

O ver un output específico:

```bash
terraform output elb_dns_name
terraform output rds_endpoint
```

## Acceso SSH a las Instancias

Después de aplicar, se generará un archivo `clavemac.pem` en el directorio `terraform/`. Úsalo para conectarte:

```bash
# Performance instance
ssh -i clavemac.pem ubuntu@<PERFORMANCE_PUBLIC_IP>

# Worker instance
ssh -i clavemac.pem ubuntu@<WORKER_PUBLIC_IP>

# Backend instances (desde el ASG)
ssh -i clavemac.pem ubuntu@<BACKEND_PRIVATE_IP>
```

**Nota**: Las instancias del ASG están en subnets privadas, así que necesitarás conectarte a través de una instancia en subnet pública o usar un bastion host.

## Inicialización de RDS

La inicialización de RDS se ejecuta automáticamente después de crear la instancia usando el archivo `../source/database/init.sql`.

**Requisitos**:
- PostgreSQL client instalado localmente
- El archivo `init.sql` debe estar en `../source/database/init.sql` (relativo al directorio terraform)

Si la inicialización falla, puedes ejecutarla manualmente:

```bash
PGPASSWORD='root1234' psql \
  -h <RDS_ENDPOINT> \
  -U postgres \
  -d anbdb \
  -f ../source/database/init.sql
```

## Destruir la Infraestructura

⚠️ **ADVERTENCIA**: Esto eliminará TODOS los recursos creados.

```bash
terraform destroy
```

## Variables Disponibles

| Variable | Descripción | Default | Requerido |
|----------|-------------|---------|-----------|
| `aws_region` | Región de AWS | `us-east-1` | No |
| `aws_access_key_id` | AWS Access Key ID | - | Sí |
| `aws_secret_access_key` | AWS Secret Access Key | - | Sí |
| `aws_session_token` | AWS Session Token (AWS Academy) | `""` | No |
| `rds_password` | Password de RDS PostgreSQL | `root1234` | No |
| `allowed_ssh_cidr` | CIDR permitido para SSH | `0.0.0.0/0` | No |

## Outputs Disponibles

- `elb_dns_name`: DNS del Load Balancer
- `rds_endpoint`: Endpoint completo de RDS (con puerto)
- `rds_address`: Dirección de RDS (sin puerto)
- `rds_port`: Puerto de RDS
- `sqs_main_queue_url`: URL de la cola principal SQS
- `sqs_dlq_url`: URL de la Dead Letter Queue
- `s3_bucket_name`: Nombre del bucket S3
- `performance_instance_id`: ID de la instancia performance
- `performance_instance_public_ip`: IP pública de performance
- `worker_instance_id`: ID de la instancia worker
- `worker_instance_public_ip`: IP pública de worker
- `key_pair_name`: Nombre del key pair
- `private_key_path`: Ruta al archivo de clave privada

## Troubleshooting

### Error: "LabRole not found"
- Verifica que el rol `LabRole` existe en tu cuenta de AWS Academy
- Si no existe, créalo manualmente o ajusta el código en `iam.tf`

### Error: "Failed to initialize RDS"
- Verifica que tienes PostgreSQL client instalado
- Verifica que el archivo `init.sql` existe en `../source/database/init.sql`
- Verifica que el security group de RDS permite conexiones desde tu IP

### Error: "Key pair already exists"
- Si el key pair `clavemac` ya existe, elimínalo manualmente desde AWS Console o ajusta el nombre en `keypair.tf`

### Error: "Bucket name already exists"
- El nombre del bucket S3 debe ser único globalmente. Cambia el nombre en `s3.tf` si es necesario.

## Notas Importantes

1. **Free Tier**: Los recursos están configurados para usar la capa gratuita cuando es posible:
   - EC2: t3.small (no está en free tier, pero es el mínimo requerido)
   - RDS: db.t3.micro (free tier elegible)

2. **Costos**: Aunque muchos recursos están en free tier, algunos pueden generar costos:
   - NAT Gateway: ~$0.045/hora + transferencia de datos
   - Application Load Balancer: ~$0.0225/hora + LCU
   - Considera eliminar NAT Gateway si no es necesario

3. **Seguridad**: 
   - Cambia `allowed_ssh_cidr` a tu IP específica
   - No subas `terraform.tfvars` al repositorio
   - Rota las credenciales regularmente

4. **AWS Academy**: 
   - Las credenciales pueden expirar. Si `terraform apply` falla con errores de autenticación, renueva las credenciales.

## Siguiente Paso

Después de crear la infraestructura:

1. Actualiza la AMI en el Launch Template con tu AMI personalizada
2. Configura las instancias con tu aplicación
3. Configura el backend para usar el RDS endpoint y las colas SQS
4. Configura el worker para consumir de SQS y escribir a S3

