# Documentacion - Entrega 5

Este directorio contiene todos los archivos entregables de la Cuarta entrega del proyecto ANB Rising Stars Showcase, incluyendo diagramas de arquitectura AWS, documentacion tecnica de servicios cloud y reportes de las pruebas de rendimiento realizadas en la nube.

## Resumen

Esta entrega representa la **migración de instancias desplegadas en EC2 a instancias desplegadas en ECS EC2**, implementando una arquitectura cloud-native que reemplaza los servicios EC2 por servicios administrados ECS AWS.

### Servicios AWS Implementados

**Componentes Usados:**
- ✅ **Instancias EC2 → AWS ECS EC"**: Uso de Elastick Container Services 
- ✅ **Grupos de Auto Scaling**: Compute escalable para ECS

**Componentes Configurados en AWS:**
- ✅ **Autoscaling → Amazon Grupos de Auto Scaling**: Servicio para escalar la capa bakcned y worker en función del procesamiento del CPU y de memoria Ram

## Contenido de la Entrega

### 📄 Codigo Fuente del Backend para subir en la instancia de AWS
**Ubicacion:** `source/deployment/backend-instance/`

Contiene los archivos necesarios para el despliegue del backend en instancias EC2 de AWS, con integración a servicios AWS nativos (SQS, S3, CloudWatch).

**Componentes incluidos:**
- `DEPLOY.md` - Instrucciones completas de despliegue del backend
- `docker-compose.yml` - Configuracion de contenedores Docker para el backend
- `init-database.sh` - Script de inicializacion de base de datos PostgreSQL
- `nginx.conf` - Configuracion del servidor Nginx como API Gateway
- `setup-s3.sh` - Script de configuracion de buckets S3 para almacenamiento de videos
- `.env.example` - Plantilla de variables de entorno (incluye SQS, S3, CloudWatch)

**Servicios AWS integrados:**
- AWS SQS para cola de mensajes asíncrona
- AWS S3 para almacenamiento de videos (original/, processed/)
- AWS CloudWatch para métricas y logs usando EMF

**[Ver documentacion tecnica completa →](../../source/deployment/backend-instance/DEPLOY.md)**

### 📄 Codigo Fuente del Worker para subir en la instancia de AWS
**Ubicacion:** `source/deployment/worker-instance/`

Contiene los archivos necesarios para el despliegue del worker de procesamiento de videos en instancias EC2 de AWS, con integración completa a servicios AWS.

**Componentes incluidos:**
- `DEPLOY.md` - Instrucciones completas de despliegue del worker
- `docker-compose.yml` - Configuracion de contenedores Docker para el worker
- `setup-s3.sh` - Script de configuracion de acceso a buckets S3
- `.env.example` - Plantilla de variables de entorno (incluye SQS, S3, CloudWatch)

**Servicios AWS integrados:**
- AWS SQS para consumo de mensajes de procesamiento (con DLQ)
- AWS S3 para descarga y upload de videos procesados
- AWS CloudWatch para métricas de procesamiento y monitoreo
- FFmpeg para procesamiento de video con intro/outro

**[Ver documentacion tecnica completa →](../../source/deployment/worker-instance/DEPLOY.md)**

### 🔧 Configuracion de AWS SQS (Message Queue)
**Ubicacion:** `source/deployment/sqs-setup/`

Scripts y documentación para configurar AWS SQS como message broker, reemplazando Redis para permitir escalamiento horizontal del sistema.

**Componentes incluidos:**
- `README.md` - Guía completa de configuración de SQS
- `setup-sqs.sh` - Script para crear colas SQS (principal y DLQ)
- `setup-iam.sh` - Script para configurar permisos IAM
- `cleanup-sqs.sh` - Script para limpiar recursos SQS

**Configuración de colas:**
- **Cola principal**: `anb-video-processing-queue`
  - Long polling: 20 segundos (reducción de costos)
  - Visibility timeout: 3600 segundos (1 hora)
  - Retention: 4 días
- **Dead Letter Queue**: `anb-video-processing-dlq`
  - Max receives: 3 reintentos
  - Retention: 14 días

**[Ver guía de configuración completa →](../../source/deployment/sqs-setup/README.md)**

### 🧪 Codigo Fuente de las Pruebas de Rendimiento y Carga para subir en la instancia de AWS
**Ubicacion:** `source/deployment/performance-instance/`

Contiene los archivos necesarios para el despliegue en las instancias de aws,tambien encontrara las instrucciones de ejecucion.

**Componentes incluidos:**
- `DEPLOY.md` - Instrucciones de despliegue de herramientas de prueba
- `docker-compose.yml` - Configuracion de contenedores Docker
- `README.md` - Documentacion del sistema de pruebas

**[Ver documentacion tecnica completa →](../../source/deployment/performance-instance/DEPLOY.md)**

### 📊 Diagramas de Arquitectura AWS
**Ubicacion:** `docs/Entrega_4/diagramas_arquitectura.md`

Los diagramas de arquitectura actualizados muestran la migración completa a servicios AWS nativos, con diferentes niveles de abstracción y detalle del sistema:

**[Ver Diagramas de Arquitectura →](diagramas_arquitectura.md)**

### 📦 Plan de Pruebas de Capacidad en AWS
**Ubicacion:** `capacity-planning/plan_de_pruebas.md`

Contiene el análisis detallado de capacidad de la aplicación en arquitectura AWS.

**[Ver plan de pruebas de capacidad →](../../capacity-planning/plan_de_pruebas.md)**

### 📦 Resultados de Pruebas de Capacidad en AWS
**Ubicacion:** `capacity-planning/pruebas_de_carga_entrega4.md`

Contiene el análisis detallado de capacidad de la aplicación ejecutado sobre la infraestructura AWS.

**[Ver resultados de pruebas de capacidad →](../../capacity-planning/pruebas_de_carga_entrega5.md)**

### ⚡ Configuración de ECS Completa AWS
### 1. Amazon Machine Images (AMI)

Se crearon AMIs personalizadas de las instancias backend configuradas.

#### AMI Actual en Uso
- **AMI ID:** `ami-0ef9256fa3819b8ba`
- **Nombre:** ECS Instance - anb-ecs
- **Región:** us-east-1

#### Contenido del AMI

Las AMIs incluyen:

**Sistema Operativo:**
- Amazon Linux 2 (optimizado para ECS)
- Kernel 5.10+
- Arquitectura: x86_64

**Software Pre-instalado:**
- ✅ Docker Engine
- ✅ Docker Compose
- ✅ Amazon ECS Container Agent
- ✅ AWS CLI
- ✅ CloudWatch Agent

**Imágenes Docker Pre-cargadas:**
```
anb-backend:latest         (468 MB) - Backend FastAPI
anb-worker:latest          (322 MB) - Worker Celery
amazon/amazon-ecs-agent:latest - ECS Agent
amazon/amazon-ecs-pause:0.1.0 - Contenedor de pausa
```

**Variables de Entorno Configuradas:**
- `ECS_CLUSTER=anb-ecs`
- `ECS_ENABLE_TASK_IAM_ROLE=true`
- `ECS_ENABLE_TASK_IAM_ROLE_NETWORK_HOST=true`
- `ECS_AVAILABLE_LOGGING_DRIVERS=["json-file","awslogs"]`

**Scripts de Inicialización Automática:**
- `/etc/ecs/ecs.config` - Configuración del ECS Agent
- User Data Script para registro en el cluster

#### Configuración del ECS Agent

Archivo `/etc/ecs/ecs.config`:
```bash
ECS_CLUSTER=anb-ecs
ECS_ENABLE_TASK_IAM_ROLE=true
ECS_ENABLE_CONTAINER_METADATA=true
ECS_ENABLE_TASK_CPU_MEM_LIMIT=true
ECS_AVAILABLE_LOGGING_DRIVERS=["json-file","awslogs"]
ECS_RESERVED_MEMORY=256
```

---

### 2. Plantillas de Lanzamiento (Launch Templates)

Creadas a partir de las AMIs personalizadas con configuración específica para ECS.

#### Detalles del Launch Template

- **Launch Template ID:** `lt-02bac2bb86820f5d6`
- **Nombre:** `ECSLaunchTemplate_V9vmr579s48a`
- **Versión Actual:** 9 (latest)
- **Estado:** Active

#### Especificaciones Configuradas

**Tipo de Instancia:**
- **Tipo:** `t3.medium`
- **vCPUs:** 2
- **RAM:** 4 GB (3827 MB disponibles para ECS)
- **Network Performance:** Up to 5 Gigabit
- **EBS Optimized:** No
- **CPU Credits:** Burstable (Standard mode)

**Características t3.medium:**
| Recurso | Especificación |
|---------|----------------|
| vCPUs | 2 |
| RAM | 4 GB |
| Baseline CPU | 20% constante |
| Burst CPU | 100% (usando créditos) |
| Network | Up to 5 Gbps |
| Storage | EBS-only |

**AMI:**
- **Imagen:** ami-0ef9256fa3819b8ba (ECS-optimized Amazon Linux 2)

**IAM Role:**
- **Role:** `LabInstanceProfile`
- **ARN:** `arn:aws:iam::782745535150:instance-profile/LabInstanceProfile`
- **Permisos incluidos:**
  - Amazon ECS Task Execution Role
  - Acceso a SQS (lectura/escritura)
  - Acceso a S3 (lectura/escritura en anb-videos-bucket-2025e2)
  - CloudWatch Logs (escritura)
  - CloudWatch Metrics (publicación)
  - ECR (pull de imágenes - si se usa)

**Security Groups:**
```json
[
  {
    "GroupId": "sg-000a4861aafccdd0c",
    "GroupName": "anb-rds-sg"
  },
  {
    "GroupId": "sg-0a527a0524e636a12",
    "GroupName": "anb-worker-sg"
  },
  {
    "GroupId": "sg-0f6762402785079ed",
    "GroupName": "anb-backend-sg"
  }
]
```

**Reglas del Security Group Principal (anb-backend-sg):**
| Puerto | Protocolo | Origen | Descripción |
|--------|-----------|--------|-------------|
| 22 | TCP | 0.0.0.0/0 | SSH para administración |
| 80 | TCP | 0.0.0.0/0 | HTTP directo |
| 80 | TCP | sg-061bb7ba9cf2e4b3c | HTTP desde ALB |
| 8000 | TCP | 0.0.0.0/0 | API Backend |
| 8000 | TCP | sg-061bb7ba9cf2e4b3c | Tráfico desde ALB |

**Storage:**
- **Volume Type:** EBS General Purpose SSD (gp2)
- **Size:** 30 GB (default)
- **Delete on Termination:** Yes

<img width="1369" height="650" alt="Captura de pantalla 2025-11-30 194628" src="https://github.com/user-attachments/assets/2c356638-73fd-4b5f-ba70-1df6c4b70504" />
<img width="1342" height="607" alt="Captura de pantalla 2025-11-30 194658" src="https://github.com/user-attachments/assets/bdd01e04-138a-4f8e-8847-431ab5f822a7" />
<img width="1353" height="659" alt="Captura de pantalla 2025-11-30 194707" src="https://github.com/user-attachments/assets/7b728aea-4f5d-45ba-b7dd-f8bd2c19be2b" />

---

### 🔀 Grupo de Auto Scaling (Auto Scaling Group)

Configuración del grupo de Auto Scaling integrado con ECS Capacity Provider.

#### Configuración del Grupo

- **Nombre:** `Infra-ECS-Cluster-anb-ecs-f5673c3b-ECSAutoScalingGroup-wPHedB2xudv0`
- **ARN:** `arn:aws:autoscaling:us-east-1:782745535150:autoScalingGroup:1019f4e8-1856-4865-98fb-b7466c8e0e3b`
- **Estado:** Active
- **Creado:** 2025-11-22 16:28:00 UTC

#### Capacidades

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| **Capacidad Deseada** | 1 instancia | Número objetivo de instancias |
| **Capacidad Mínima** | 1 instancia | Mínimo para garantizar disponibilidad |
| **Capacidad Máxima** | 6 instancias | Máximo para control de costos |

**Justificación de la configuración:**
- **Mínimo 1:** Garantiza que siempre hay al menos una instancia disponible
- **Deseada 1:** Configuración actual para testing/desarrollo
- **Máximo 6:** Permite escalar hasta 6 instancias (12 vCPUs, 24 GB RAM total)

#### Zonas de Disponibilidad

**Multi-AZ para Alta Disponibilidad:**
```json
{
  "AvailabilityZones": ["us-east-1a", "us-east-1b"],
  "VPCZoneIdentifier": "subnet-0e3fb3103add58769,subnet-06a2f7e099d3be111"
}
```

| AZ | Subnet ID | Tipo |
|----|-----------|------|
| us-east-1a | subnet-06a2f7e099d3be111 | Pública |
| us-east-1b | subnet-0e3fb3103add58769 | Pública |

**Estrategia de Distribución:**
- `CapacityDistributionStrategy: balanced-best-effort`
- Distribuye instancias equitativamente entre AZs
- Si una AZ falla, las instancias continúan en la otra

#### Health Checks

```json
{
  "HealthCheckType": "EC2",
  "HealthCheckGracePeriod": 300
}
```

- **Tipo:** EC2 (verifica estado de la instancia)
- **Grace Period:** 300 segundos (5 minutos) antes de marcar instancia como unhealthy
- **No usa ELB health checks** (manejado por ECS)

<img width="1064" height="545" alt="Captura de pantalla 2025-11-30 195220" src="https://github.com/user-attachments/assets/4b21ae62-6c79-46d5-bf78-d715526780d4" />

---

### 🎥 Video de Sustentacion
**Ubicacion:** `sustentacion/Entrega_5/`

Contiene el video de sustentación del proyecto para la quinta entrega, donde se presenta la migración completa a AWS, la arquitectura cloud-native implementada y una demostración del funcionamiento del sistema con servicios AWS.

**[Ver informacion del video de sustentacion →](https://github.com/martin-hendricks/MISW-4204-desarrollo-de-software-en-la-nube/tree/main/sustentacion/Entrega_5)**

### 📈 Resultados de SonarCloud

Contiene el analisis estatico de calidad de codigo realizado con SonarCloud, una plataforma de inspeccion continua que evalua la calidad del codigo fuente. Incluye:
- Metricas de calidad de codigo (bugs, vulnerabilidades, code smells)
- Analisis de cobertura de pruebas
- Evaluacion de duplicacion de codigo
- Calificacion general del proyecto (Quality Gate)
- Recomendaciones para mejoras de calidad

**Metricas evaluadas:**
- Reliability (Confiabilidad)
- Security (Seguridad)
- Maintainability (Mantenibilidad)
- Coverage (Cobertura de pruebas)
- Duplications (Duplicacion de codigo)

<img width="2304" height="1668" alt="image (25)" src="https://github.com/user-attachments/assets/4258b83a-aa11-4183-80e9-29a3211d4fe3" />


**Curso**: MISW-4204 Desarrollo de Software en la Nube
**Numero de Equipo**: 2
**Universidad**: Universidad de los Andes
**Entrega**: 3 - Migración a AWS Cloud
