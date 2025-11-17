# Diagramas de Arquitectura - ANB Rising Stars Showcase - AWS

Este documento presenta el diagrama de arquitectura del sistema ANB Rising Stars Showcase, actualizado de acuerdo a las instancias levantasdas en AWS mostrando diferentes niveles de abstraccion y detalle de los componentes y sus interacciones.

## 1. Diagrama de Componentes

El diagrama de componentes muestra la estructura interna del Backend API, detallando los modulos y capas que lo componen.   

<img width="1400" height="1440" alt="image" src="https://github.com/user-attachments/assets/659a6132-b95d-45e9-8ba3-a05446f488df" />

## 2. Diagrama de Despliegue

El diagrama de despliegue muestra la estructura de despliegue para cada componente.

<img width="3216" height="2370" alt="image (26)" src="https://github.com/user-attachments/assets/835f48f7-de3f-408c-93ef-cba491dbec64" />


**Capas principales:**
- **Routers**: Definicion de endpoints de la API REST
- **Services**: Logica de negocio y casos de uso
- **Domain**: Entidades, value objects y repositorios (interfaces)
- **Infrastructure**: Implementaciones concretas (base de datos, servicios externos)
- **DTOs**: Objetos de transferencia de datos para comunicacion con clientes


### Etapa de Carga
1. El jugador se autentica en el sistema
2. Sube el video a traves del API
3. El sistema guarda el video original y registra la metadata en la base de datos
4. Se publica una tarea de procesamiento en RabbitMQ
5. Se retorna un task_id al jugador

### Etapa de Procesamiento Asincrono
1. El Worker consume la tarea desde redes
2. Descarga el video original del almacenamiento
3. Procesa el video con FFmpeg:
   - Recorta a maximo 30 segundos
   - Ajusta resolucion y formato
   - Agrega marca de agua de ANB
   - Elimina audio
4. Guarda el video procesado en el almacenamiento
5. Actualiza el estado del video a "procesado" en la base de datos

### Etapa de Consulta y Entrega
1. El publico consulta los videos disponibles
2. El sistema retorna los videos procesados
3. Los usuarios pueden visualizar y votar por los videos
4. Se actualiza el ranking dinamicamente


## Patrones de Diseño Implementados en Arquitectura AWS

Basándose en el diagrama de componentes AWS, el sistema implementa los siguientes patrones arquitectónicos cloud-native:

### 1. Load Balancer Pattern (Elastic Load Balancer)
**Componente**: Elastic Load Balancer (ELB)

**Función**:
- Actúa como **punto de entrada único** para todo el tráfico HTTP/HTTPS del sistema
- Distribuye las solicitudes entrantes entre múltiples instancias backend de forma equitativa
- Implementa algoritmo **Round Robin** para balanceo de carga

**Beneficios**:
- ✅ **Alta disponibilidad**: Si una instancia falla, el tráfico se redirige automáticamente a instancias saludables
- ✅ **Escalabilidad horizontal**: Soporta múltiples instancias backend sin cambios en la aplicación
- ✅ **Health Checks**: Monitoreo continuo del endpoint `/api/health` para detectar instancias no saludables
- ✅ **Sticky Sessions**: Mantiene la sesión del usuario en la misma instancia para consistencia

**Implementación AWS**:
- Application Load Balancer (capa 7 - HTTP/HTTPS)
- Target Group para agrupar instancias backend
- Listener HTTP en puerto 80

---

### 2. Auto Scaling Pattern (Escalamiento Automático)
**Componente**: Auto Scaling Group

**Función**:
- **Escala automáticamente** el número de instancias backend según la demanda de usuarios concurrentes
- Gestiona el ciclo de vida de las instancias EC2 (lanzamiento, terminación, reemplazo)
- Garantiza capacidad mínima (1 instancia) y limita capacidad máxima (5 instancias)

**Políticas de Escalado Implementadas**:

1. **Escalado por Tráfico de Red (NetworkIn)**:
   - Umbral: > 40 peticiones por instancia
   - Acción: Agregar 1 instancia
   - Cooldown: 300 segundos

2. **Escalado por CPU (CPUUtilization)**:
   - Escalar hacia arriba: CPU > 70% → +1 instancia
   - Escalar hacia abajo: CPU < 30% → -1 instancia
   - Cooldown: 300 segundos

**Beneficios**:
- ✅ **Elasticidad**: Ajuste dinámico de recursos según demanda real
- ✅ **Optimización de costos**: Reduce instancias en periodos de baja demanda
- ✅ **Resiliencia**: Reemplazo automático de instancias fallidas
- ✅ **Multi-AZ**: Distribución en múltiples zonas de disponibilidad (us-east-1a, us-east-1b)

**Implementación AWS**:
- AMIs personalizadas con backend preconfigurado
- Launch Templates con especificaciones t2.small
- Auto Scaling Group con políticas de escalado basadas en métricas CloudWatch

---

### 3. Target Group Pattern (Agrupación de Destinos)
**Componente**: Target Group

**Función**:
- **Agrupa las instancias backend** que forman parte del pool de servidores
- Permite al Load Balancer enrutar solicitudes HTTP a las instancias disponibles
- Gestiona el registro y desregistro automático de instancias del Auto Scaling Group

**Configuración**:
- Protocolo: HTTP en puerto 80 (Nginx)
- Health Check: `GET /api/health` cada 30 segundos
- Umbral saludable: 2 checks consecutivos exitosos (200 OK)
- Umbral no saludable: 2 checks consecutivos fallidos

**Beneficios**:
- ✅ **Integración con Auto Scaling**: Las nuevas instancias se registran automáticamente
- ✅ **Monitoreo continuo**: Health checks detectan instancias problemáticas
- ✅ **Aislamiento de fallos**: Instancias "unhealthy" no reciben tráfico
- ✅ **Zero Downtime**: El tráfico solo se envía a instancias saludables

---

### 4. Message Queue Pattern (Cola de Mensajes Asíncrona)
**Componente**: AWS SQS (Simple Queue Service)

**Función**:
- **Desacopla productores (Backend)** de consumidores (Workers) mediante cola de mensajes
- El Backend publica tareas de procesamiento de video en la cola SQS
- Los Workers consumen tareas de forma asíncrona e independiente
- Permite procesamiento asíncrono y escalabilidad horizontal

**Configuración SQS**:
- **Cola principal**: `anb-video-processing-queue`
  - Long polling: 20 segundos (reduce costos de API)
  - Visibility timeout: 3600 segundos (1 hora para procesamiento)
  - Retention: 4 días
- **Dead Letter Queue**: `anb-video-processing-dlq`
  - Max receives: 3 reintentos antes de enviar a DLQ
  - Retention: 14 días

**Beneficios**:
- ✅ **Desacoplamiento**: Backend y Workers operan independientemente
- ✅ **Escalabilidad**: Múltiples Workers pueden consumir de la misma cola
- ✅ **Tolerancia a fallos**: DLQ captura mensajes fallidos para análisis
- ✅ **Balanceo automático**: SQS distribuye mensajes equitativamente entre Workers
- ✅ **Persistencia**: Mensajes se retienen incluso si no hay Workers disponibles

**Flujo de mensajes**:
```
Backend → publica tareas → SQS Queue → consume tareas → Worker
                              ↓
                    (si falla 3 veces)
                              ↓
                     Dead Letter Queue
```

---

### 5. Worker Pattern (Procesamiento Asíncrono Distribuido)
**Componente**: Worker (Celery + FFmpeg)

**Función**:
- **Workers especializados** en tareas pesadas de procesamiento de video
- Consumen mensajes de la cola SQS de forma asíncrona
- Múltiples workers pueden procesar videos en paralelo sin interferir entre sí
- Cada worker es independiente y puede escalar horizontalmente

**Procesamiento de Video**:
1. Consume mensaje de SQS con `video_id`
2. Descarga video original desde S3 (`original/{video_id}.mp4`)
3. Procesa video con FFmpeg:
   - Recorta a máximo 30 segundos
   - Ajusta resolución y formato
   - Agrega intro/outro con marca de agua ANB
   - Elimina audio
4. Sube video procesado a S3 (`processed/{video_id}.mp4`)
5. Actualiza estado en base de datos PostgreSQL
6. Envía métricas a CloudWatch (tiempo de procesamiento, éxito/fallo)

**Beneficios**:
- ✅ **Paralelismo**: Múltiples videos se procesan simultáneamente
- ✅ **Escalabilidad**: Más workers = mayor throughput de procesamiento
- ✅ **Aislamiento**: Cada worker opera independientemente
- ✅ **Retry Logic**: Reintentos automáticos con exponential backoff

---

### 6. Object Storage Pattern (Almacenamiento de Objetos)
**Componente**: AWS S3 (Simple Storage Service)

**Función**:
- **Almacenamiento escalable** de videos originales y procesados
- El Backend escribe videos subidos por usuarios a S3
- Los Workers leen videos originales y escriben videos procesados a S3
- Estructura de prefijos organiza videos por etapa del procesamiento

**Estructura de S3 Bucket**:
```
anb-videos-bucket/
├── original/
│   ├── {video_id_1}.mp4  (videos subidos por usuarios)
│   ├── {video_id_2}.mp4
│   └── ...
├── processed/
│   ├── {video_id_1}.mp4  (videos con intro/outro)
│   ├── {video_id_2}.mp4
│   └── ...
└── temp/
    └── (archivos temporales de procesamiento)
```

**Beneficios**:
- ✅ **Escalabilidad ilimitada**: S3 escala automáticamente sin límites
- ✅ **Durabilidad**: 99.999999999% (11 nueves) de durabilidad
- ✅ **Alta disponibilidad**: 99.9% SLA
- ✅ **Presigned URLs**: Acceso temporal seguro a videos (1 hora de expiración)
- ✅ **Costos optimizados**: Pago por uso, sin capacidad pre-provisionada

**Operaciones**:
- **Backend**: `PUT /original/{video_id}.mp4` (upload de videos)
- **Worker**: `GET /original/{video_id}.mp4` → Procesar → `PUT /processed/{video_id}.mp4`

---

### 7. Observability Pattern (Monitoreo y Métricas)
**Componente**: AWS CloudWatch

**Función**:
- **Monitoreo centralizado** de métricas del sistema
- Backend y Workers envían métricas usando **Embedded Metric Format (EMF)**
- Métricas se publican como JSON estructurado en stdout
- CloudWatch Agent parsea y publica métricas automáticamente

**Métricas Monitoreadas**:

**Backend (Namespace: ANB/Backend)**:
- `RequestCount`: Total de solicitudes HTTP
- `RequestDuration`: Latencia de endpoints (P50, P95, P99)
- `ErrorCount`: Errores HTTP (4xx, 5xx)
- `ProcessCPU`, `ProcessMemoryMB`: Uso de recursos por proceso

**Worker (Namespace: ANB/Worker)**:
- `TaskCount`: Total de tareas procesadas
- `TaskDuration`: Tiempo de procesamiento por video (P50, P95, P99)
- `TaskFailure`, `TaskRetry`: Tareas fallidas y reintentadas
- `ProcessCPU`, `ProcessMemoryMB`: Uso de recursos

**Auto Scaling & Load Balancer**:
- `HealthyHostCount`, `UnHealthyHostCount`: Instancias saludables en Target Group
- `TargetResponseTime`: Tiempo de respuesta promedio de instancias
- `RequestCount`: Solicitudes procesadas por el ALB

**SQS**:
- `ApproximateNumberOfMessagesVisible`: Mensajes pendientes en cola
- `ApproximateAgeOfOldestMessage`: Edad del mensaje más antiguo

**Beneficios**:
- ✅ **Visibilidad completa**: Métricas de todos los componentes en un solo lugar
- ✅ **Dashboards personalizados**: Visualización en tiempo real
- ✅ **Alarmas automáticas**: Notificaciones cuando métricas superan umbrales
- ✅ **Logs centralizados**: CloudWatch Logs con driver awslogs
- ✅ **Análisis avanzado**: CloudWatch Logs Insights para consultas

---

### 8. Repository Pattern (Abstracción de Acceso a Datos)
**Componente**: Backend - Domain Layer

**Función**:
- El backend usa **repositorios** para abstraer el acceso a datos
- Interfaces de repositorio en la capa Domain
- Implementaciones concretas en la capa Infrastructure
- Facilita testing (mocks) y cambios de base de datos

**Repositorios Implementados**:
- `UserRepository`: Gestión de usuarios y autenticación
- `VideoRepository`: Metadata de videos (estado, URLs S3, timestamps)
- `VoteRepository`: Sistema de votación de videos

**Beneficios**:
- ✅ **Separación de concerns**: Lógica de negocio independiente de persistencia
- ✅ **Testabilidad**: Fácil crear mocks para unit tests
- ✅ **Flexibilidad**: Cambio de base de datos sin afectar lógica de negocio
- ✅ **Clean Architecture**: Dependencias apuntan hacia el dominio

---

## Resumen de Patrones AWS Cloud-Native

La arquitectura implementa una combinación de patrones que garantizan:

| Patrón | Componente AWS | Beneficio Principal |
|--------|---------------|---------------------|
| **Load Balancer** | Elastic Load Balancer | Alta disponibilidad y distribución de carga |
| **Auto Scaling** | Auto Scaling Group | Elasticidad y optimización de costos |
| **Target Group** | Target Group | Gestión automática de instancias saludables |
| **Message Queue** | SQS + DLQ | Desacoplamiento y procesamiento asíncrono |
| **Worker** | EC2 Workers + Celery | Procesamiento paralelo distribuido |
| **Object Storage** | S3 | Almacenamiento escalable e ilimitado |
| **Observability** | CloudWatch | Monitoreo centralizado y alertas |
| **Repository** | Backend Domain Layer | Abstracción de persistencia |

Estos patrones en conjunto crean una arquitectura **cloud-native, escalable, resiliente y observable**, aprovechando los servicios administrados de AWS para reducir la carga operacional y mejorar la confiabilidad del sistema.

## Referencias

- [Documentacion Tecnica Completa](../../source/README.md)
- [Backend API Documentation](../../source/backend/README.md)
- [Performance Testing Guide](../../source/performance-testing/README.md)
