# Documentacion - Entrega 3

Este directorio contiene todos los archivos entregables de la Tercera entrega del proyecto ANB Rising Stars Showcase, incluyendo diagramas de arquitectura AWS, documentacion tecnica de servicios cloud y reportes de las pruebas de rendimiento realizadas en la nube.

## 🎯 Resumen Ejecutivo

Esta entrega representa la **migración completa del sistema ANB Rising Stars a AWS Cloud**, implementando una arquitectura cloud-native que reemplaza los servicios locales por servicios administrados de AWS.

### Servicios AWS Implementados

**Componentes Migrados:**
- ✅ **Redis → AWS SQS**: Message queue con DLQ y long polling
- ✅ **NFS/Local → AWS S3**: Almacenamiento escalable de videos
- ✅ **Prometheus/Grafana → CloudWatch**: Monitoreo unificado con EMF
- ✅ **PostgreSQL Local → Amazon RDS**: Base de datos administrada
- ✅ **Docker Local → Amazon EC2**: Compute escalable

**Componentes Configurados en AWS:**
- ✅ **Autoscaling → Amazon Grupos de Auto Scaling**: Servicio para escalar la capa web en función de los usuarios concurrentes
- ✅ **Load Balancer → Amazon ALB**: Distribución de la carga entre las instancias que exponen el API REST.

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
**Ubicacion:** `docs/Entrega_3/diagramas_arquitectura.md`

Los diagramas de arquitectura actualizados muestran la migración completa a servicios AWS nativos, con diferentes niveles de abstracción y detalle del sistema:

**[Ver Diagramas de Arquitectura →](diagramas_arquitectura.md)**

### 📦 Plan de Pruebas de Capacidad en AWS
**Ubicacion:** `capacity-planning/plan_de_pruebas.md`

Contiene el análisis detallado de capacidad de la aplicación en arquitectura AWS.

**[Ver plan de pruebas de capacidad →](../../capacity-planning/plan_de_pruebas.md)**

### 📦 Resultados de Pruebas de Capacidad en AWS
**Ubicacion:** `capacity-planning/pruebas_de_carga_entrega3.md`

Contiene el análisis detallado de capacidad de la aplicación ejecutado sobre la infraestructura AWS.

**[Ver resultados de pruebas de capacidad →](../../capacity-planning/pruebas_de_carga_entrega3.md)**

### ⚡ Configuración de Auto Scaling Groups en AWS
**Servicio:** Amazon EC2 Auto Scaling

Configuración de escalamiento automático para la capa web del sistema, permitiendo ajustar dinámicamente el número de instancias backend según la demanda de usuarios concurrentes.

#### Componentes del Auto Scaling

**1. Amazon Machine Images (AMI)**
- Se crearon AMIs personalizadas de las instancias backend configuradas
- Las AMIs incluyen:
  - Sistema operativo Ubuntu Server 24.04.3 LTS
  - Docker y Docker Compose instalados
  - Código de la aplicación backend
  - Configuración de servicios (Nginx, FastAPI)
  - Variables de entorno para AWS (SQS, S3, CloudWatch)
  - Scripts de inicialización automática

**2. Plantillas de Lanzamiento (Launch Templates)**
- Creadas a partir de las AMIs personalizadas
- Especificaciones configuradas:
  - **Tipo de instancia**: t2.small (2 vCPUs, 2 GB RAM)
  - **AMI**: Imagen personalizada del backend
  - **IAM Role**: LabRole para acceso a SQS, S3 y CloudWatch

**3. Grupo de Auto Scaling (Auto Scaling Group)**
- Configuración del grupo:
  - **Capacidad deseada**: 2 instancias (mínimo para alta disponibilidad)
  - **Capacidad mínima**: 1 instancia
  - **Capacidad máxima**: 5 instancias
  - **Zonas de disponibilidad**: Multi-AZ (us-east-1a, us-east-1b)

**4. Políticas de Escalado (Scaling Policies)**

**Política 1 - Escalado por Tráfico de Red Entrante:**
- **Métrica**: NetworkIn (bytes recibidos)
- **Umbral**: > 40 peticiones por instancia
- **Acción**: Agregar 1 instancia
- **Cooldown**: 300 segundos
- **Objetivo**: Manejar picos de tráfico HTTP

**Política 2 - Escalado por Uso de CPU:**
- **Métrica**: CPUUtilization
- **Umbral máximo**: > 70%
- **Acción de escalado hacia arriba**: Agregar 1 instancia
- **Umbral mínimo**: < 30%
- **Acción de escalado hacia abajo**: Remover 1 instancia
- **Cooldown**: 300 segundos
- **Objetivo**: Optimizar uso de recursos

---

### 🔀 Configuración de Application Load Balancer (ALB)
**Servicio:** Elastic Load Balancing (ELB)

Configuración de balanceador de carga de aplicación para distribuir el tráfico HTTP/HTTPS entre las instancias backend del Auto Scaling Group.

#### Componentes del Load Balancer

**1. Application Load Balancer (ALB)**
- **Nombre**: anb-backend-alb
- **Esquema**: Internet-facing (público)
- **Tipo**: Application Load Balancer (capa 7)
- **Protocolo**: HTTP (puerto 80) / HTTPS (puerto 443)
- **Zonas de disponibilidad**: us-east-1a, us-east-1b (Multi-AZ)
- **Security Group**: Permite tráfico HTTP/HTTPS desde internet (0.0.0.0/0)

**2. Target Group (Grupo de Destino)**
- **Nombre**: anb-backend-targets
- **Tipo de destino**: Instancias EC2
- **Protocolo**: HTTP
- **Puerto**: 80 (Nginx)
- **VPC**: VPC del proyecto

**Configuración de Health Checks:**
- **Ruta de verificación**: `/api/health` (endpoint de salud del backend)
- **Protocolo**: HTTP
- **Intervalo**: 30 segundos
- **Timeout**: 5 segundos
- **Umbral saludable**: 2 comprobaciones consecutivas exitosas
- **Umbral no saludable**: 2 comprobaciones consecutivas fallidas
- **Códigos de éxito**: 200 OK

**3. Registro de Instancias**
- Las instancias del Auto Scaling Group se registran automáticamente en el Target Group
- El ALB monitorea continuamente la salud de cada instancia
- Solo se envía tráfico a instancias "healthy"
- Instancias "unhealthy" son removidas automáticamente del pool

**4. Reglas de Enrutamiento (Listener Rules)**
- **Listener HTTP (puerto 80)**:
  - Recibe todas las solicitudes HTTP entrantes
  - Redirige el tráfico al Target Group `anb-backend-targets`
  - Distribuye carga usando algoritmo Round Robin
  - Sticky Sessions habilitadas (basadas en cookies)


---

### 🎥 Video de Sustentacion
**Ubicacion:** `sustentacion/Entrega_3/`

Contiene el video de sustentación del proyecto para la tercera entrega, donde se presenta la migración completa a AWS, la arquitectura cloud-native implementada y una demostración del funcionamiento del sistema con servicios AWS.

**[Ver informacion del video de sustentacion →]()**

**Curso**: MISW-4204 Desarrollo de Software en la Nube
**Numero de Equipo**: 2
**Universidad**: Universidad de los Andes
**Entrega**: 3 - Migración a AWS Cloud
