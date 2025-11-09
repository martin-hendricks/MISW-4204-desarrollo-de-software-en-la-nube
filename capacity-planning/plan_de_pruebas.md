# Plan de Análisis de Capacidad - ANB Rising Stars Showcase

## 1. Objetivos

### Objetivo General
Ejecutar escenarios de prueba que permitan medir la capacidad máxima que pueden soportar los componentes del sistema ANB Rising Stars Showcase, simulando el acceso, la carga, el estrés y la utilización de la aplicación para determinar los límites operacionales y proporcionar recomendaciones de escalamiento.

### Objetivos Específicos
1. **Capacidad de la Capa Web**: Determinar el número máximo de usuarios concurrentes y RPS que la API puede soportar cumpliendo SLOs establecidos
2. **Rendimiento del Worker**: Medir el throughput de procesamiento de videos (videos/minuto) bajo diferentes configuraciones
3. **Identificación de Cuellos de Botella**: Identificar los componentes que limitan el rendimiento del sistema
4. **Análisis de Escalabilidad**: Evaluar la capacidad del sistema para crecer y manejar picos de carga
5. **Validación de SLOs**: Verificar que el sistema cumple con los Service Level Objectives definidos

## 2. Descripción General

El sistema ANB Rising Stars Showcase es una aplicación de procesamiento de videos que permite a los usuarios subir videos de baloncesto, procesarlos con intro/outro, y participar en un sistema de votación. La arquitectura basada en AWS incluye:

- **Capa Web (FastAPI)**: API REST para autenticación, gestión de videos y votación
- **Capa de Procesamiento (Celery Workers)**: Procesamiento asíncrono de videos con FFmpeg
- **Base de Datos (PostgreSQL)**: Almacenamiento de datos de usuarios, videos y votos
- **Cola de Mensajes (AWS SQS)**: Gestión de tareas de procesamiento asíncrono con Dead Letter Queue
- **Almacenamiento de Archivos (AWS S3)**: Almacenamiento escalable de videos originales y procesados
- **Monitoreo (AWS CloudWatch)**: Métricas, logs y alertas del sistema usando Embedded Metric Format

Este plan de pruebas se enfoca en medir la capacidad de estos componentes bajo diferentes escenarios de carga para proporcionar datos cuantitativos sobre el rendimiento del sistema.

## 3. Tipos de Pruebas a Realizar

### 3.1 Pruebas de Capacidad
- **Objetivo**: Determinar el número máximo de usuarios concurrentes que soporta la capa web
- **Enfoque**: Escalamiento gradual de usuarios hasta encontrar el punto de saturación

### 3.2 Pruebas de Carga
- **Objetivo**: Evaluar el comportamiento del sistema bajo carga esperada de producción
- **Enfoque**: Carga sostenida al 80% de la capacidad máxima identificada

### 3.3 Pruebas de Estrés
- **Objetivo**: Determinar el comportamiento del sistema bajo carga extrema
- **Enfoque**: Carga por encima de los límites normales para identificar puntos de falla

### 3.4 Pruebas de Escalabilidad
- **Objetivo**: Evaluar la capacidad del worker para procesar videos bajo diferentes configuraciones
- **Enfoque**: Variación de concurrencia y tamaños de archivo

### 3.5 Pruebas de Picos de Estrés
- **Objetivo**: Verificar la capacidad de recuperación ante picos repentinos de carga
- **Enfoque**: Incrementos súbitos de usuarios concurrentes

## 4. Escenarios de Prueba

### Escenario 1: Capacidad de la Capa Web (Usuarios Concurrentes)

#### 4.1.1 Estrategia de Implementación
- **Desacoplamiento del Worker**: Los endpoints de carga devuelven 202 y redirigen a un mock de cola que acepta mensajes en memoria
- **Simulación de Carga Real**: Uso de archivos de video reales para simular condiciones de producción
- **Modo de Prueba**: Activación de `TEST_MODE=true` para deshabilitar el procesamiento real

#### 4.1.2 Escenarios de Prueba

**Prueba de Sanidad (Smoke Test)**
- **Usuarios**: 5 usuarios concurrentes
- **Duración**: 1 minuto
- **Objetivo**: Validar que el sistema responde correctamente y la telemetría está activa
- **Comando**: `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"`

**Prueba de Escalamiento (Ramp-up)**
- **Estrategia**: Iniciar en 0 usuarios y aumentar gradualmente hasta X usuarios en 3 minutos, mantener 5 minutos
- **Niveles de Prueba**: 100 → 200 → 300 → 400 → 500 usuarios (se saturo maquina en 300 usuarios)
- **Objetivo**: Encontrar la capacidad máxima sin degradación significativa
- **Comando**: `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_X_users_results.jtl -Jusers=X"`

**Prueba Sostenida**
- **Usuarios**: 80% de la capacidad máxima encontrada (cap maxima 145 usuarios, se realizo prueba con 116 usuarios)
- **Duración**: 5 minutos
- **Objetivo**: Confirmar estabilidad del sistema bajo carga sostenida
- **Comando**: `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/sustained_test.jmx -l /scripts/sustained_X_users_results.jtl -Jusers=X"`

#### 4.1.3 Endpoints a Probar
- `POST /auth/login` - Autenticación
- `POST /videos/upload` - Subida de videos
- `GET /videos` - Lista de videos del usuario
- `GET /public/videos` - Videos públicos
- `POST /public/videos/{video_id}/vote` - Votación

### Escenario 2: Rendimiento de la Capa Worker (Videos/Minuto)

#### 4.2.1 Estrategia de Implementación
- **Bypass de la Web**: Inyección directa de mensajes en la cola SQS
- **Payloads Realistas**: Uso de archivos de video de diferentes tamaños (50MB) almacenados en S3
- **Configuraciones Variables**: 1, 2, 4 procesos/hilos por nodo

#### 4.2.2 Escenarios de Prueba

**Pruebas de Saturación**
- **Objetivo**: Encontrar el punto de quiebre del sistema
- **Estrategia**: Aumentar progresivamente la cantidad de tareas en la cola
- **Comandos**:
  ```bash
  # Carga
  docker exec producer python producer.py --num-videos 20 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
  ```

#### 4.2.3 Configuraciones de Prueba
- **Tamaños de Video**: 50MB
- **Concurrencia de Worker**: 1, 2, 4 procesos/hilos por nodo
- **Tiempo de Espera**: 600 segundos máximo por lote

## 5. Criterios de Aceptación

### 5.1 Criterios de Éxito para Capa Web
- **Latencia P95**: ≤ 1 segundo para todos los endpoints
- **Tasa de Errores**: ≤ 5% (4xx evitables/5xx)
- **Disponibilidad**: Sin resets/timeouts anómalos
- **Throughput**: RPS sostenido a capacidad máxima
- **Recuperación**: El sistema debe recuperarse después de picos de carga

### 5.2 Criterios de Éxito para Worker
- **Throughput**: Videos procesados por minuto medible y estable
- **Estabilidad**: La cola no debe crecer sin control (tendencia ~0)
- **Tiempo de Procesamiento**: Tiempo medio de servicio por video
- **Escalabilidad**: Mejora del throughput con mayor concurrencia

### 5.3 Criterios de Fallo
- **Degradación de Latencia**: P95 > 1 segundo
- **Alta Tasa de Errores**: > 5% de errores
- **Saturación de Recursos**: CPU > 90% sostenido
- **Pérdida de Datos**: Tareas perdidas o no procesadas
- **Inestabilidad**: Crashes o reinicios inesperados

## 6. Datos de Prueba

### 6.1 Usuarios de Prueba
- **Usuarios de Autenticación**: 500+ usuarios pre-registrados
- **Tokens JWT**: Tokens válidos para cada usuario de prueba
- **Datos de Perfil**: Nombres, emails, ciudades, países

### 6.2 Archivos de Video
- **Tamaño**: 50MB (dummy_file_50mb.mp4)
- **Formato**: MP4 estándar
- **Duración**: 2-5 minutos de video de prueba

### 6.3 Datos de Configuración
- **Configuración de Base de Datos**: PostgreSQL con datos de prueba
- **Configuración de SQS**: Colas de tareas configuradas (video_processing y DLQ)
- **Configuración de S3**: Buckets configurados con permisos apropiados (original/, processed/, temp/)

## 7. Iteraciones

### 7.1 Estrategia de Iteraciones
- **Mínimo de Iteraciones**: 3 por escenario para análisis rápido
- **Iteraciones Recomendadas**: 5-7 por escenario para mayor confiabilidad
- **Intervalo entre Iteraciones**: 10-15 minutos para estabilización del sistema
- **Análisis de Datos Atípicos**: Identificación y exclusión de outliers

### 7.2 Plan de Ejecución
1. **Iteración 1-3**: Pruebas de sanidad y escalamiento inicial
2. **Iteración 4-5**: Pruebas de capacidad máxima
3. **Iteración 6-7**: Pruebas sostenidas y de recuperación

## 8. Configuración del Sistema

### 8.1 Arquitectura del Sistema

Los diagramas de arquitectura actualizados muestran la migración completa a servicios AWS nativos, con diferentes niveles de abstracción y detalle del sistema:

**[Ver Diagramas de Arquitectura →](../docs/Entrega_3/diagramas_arquitectura.md)**

### 8.2 Infraestructura de Pruebas
- **Sistema Operativo**: Ubuntu Server 24.04.3 LTS (Docker containers)
- **CPU**: 2 cores
- **Memoria RAM**: 2 GB
- **Almacenamiento**: 50 GB
- **Red**: Conexión estable para evitar interferencias

### 8.3 Software de Soporte
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **JMeter**: 5.4+ (para pruebas de carga web)
- **PostgreSQL**: 13+ (para base de datos)
- **FFmpeg**: 4.4+ (para procesamiento de video)
- **CloudWatch Agent**: Para publicación de métricas EMF

### 8.4 Servicios AWS Utilizados
- **AWS SQS**: Colas de mensajes con long polling (20s) y Dead Letter Queue
- **AWS S3**: Almacenamiento de objetos para videos
- **AWS CloudWatch**:
  - Métricas usando Embedded Metric Format (EMF)
  - Logs centralizados con awslogs driver
  - Dashboards personalizados
  - Alarmas configurables

### 8.5 Configuración de Monitoreo
- **CloudWatch Metrics**: Recolección automática usando EMF
- **CloudWatch Dashboards**: Visualización en tiempo real de:
  - **Métricas de Aplicación**: Latencia (P50, P95, P99), throughput, errores
  - **Métricas de Sistema**: CPU, memoria, I/O, red
  - **Métricas de Negocio**: Videos procesados, tiempo de procesamiento
- **CloudWatch Logs**: Agregación de logs de todos los contenedores
- **CloudWatch Alarms**: Alertas automáticas para condiciones anómalas

## 9. Herramientas para la Prueba

### 9.1 Generación de Carga
- **JMeter 5.4+**: Para pruebas de la capa web
  - Configuración de usuarios concurrentes
  - Simulación de comportamiento real de usuarios
  - Generación de reportes detallados

### 9.2 Procesamiento Asíncrono
- **Script Producer (Python)**: Para pruebas del worker
  - Inyección directa de tareas en SQS
  - Configuración de parámetros de prueba
  - Monitoreo de progreso mediante CloudWatch

### 9.3 Observabilidad
- **AWS CloudWatch**: Recolección, almacenamiento y visualización de métricas
  - Embedded Metric Format (EMF) para métricas de aplicación
  - CloudWatch Logs Insights para análisis de logs
  - CloudWatch Dashboards para visualización
  - CloudWatch Alarms para alertas automáticas
- **SQS Monitoring**: Métricas de cola (mensajes visibles, en vuelo, edad)

### 9.4 Análisis de Resultados
- **JMeter Reports**: Análisis de resultados de carga web
- **CloudWatch Dashboards**: Monitoreo en tiempo real con métricas personalizadas
- **CloudWatch Logs**: Análisis de errores y comportamiento de aplicación
- **CloudWatch Insights**: Consultas y análisis avanzado de logs

## 10. Métricas

### 10.1 Métricas de Rendimiento Web
- **Respuestas por Segundo (RPS)**: Throughput de la API
- **Latencia**: Tiempo de respuesta de endpoints
  - P50 (mediana)
  - P95 (percentil 95)
  - P99 (percentil 99)
- **Tasa de Errores**: Porcentaje de respuestas con error
- **Usuarios Concurrentes**: Número máximo soportado

### 10.2 Métricas de Procesamiento
- **Throughput**: Videos procesados por minuto
- **Tiempo de Procesamiento**: Tiempo medio por video
- **Tamaño de Cola**: Número de tareas pendientes
- **Tasa de Éxito**: Porcentaje de tareas completadas exitosamente

### 10.3 Métricas de Sistema
- **CPU**: Uso de procesador por componente (ProcessCPU, SystemCPU)
- **Memoria**: Consumo de RAM por servicio (ProcessMemoryMB, ProcessMemoryPercent)
- **I/O**: Operaciones de disco y red
- **Conectividad**: Latencia de red entre componentes
- **SQS**: Mensajes visibles, mensajes en vuelo, edad del mensaje más antiguo
- **S3**: Latencia de operaciones GET/PUT, tamaño de bucket

### 10.4 Métricas de Negocio
- **Tiempo de Subida**: Tiempo para subir un video
- **Tiempo de Procesamiento**: Tiempo total de procesamiento
- **Disponibilidad**: Tiempo de actividad del sistema
- **Escalabilidad**: Capacidad de crecimiento

## 11. Consideraciones Específicas de AWS

### 11.1 SQS (Simple Queue Service)
- **Long Polling**: Configurado con 20 segundos para reducir costos
- **Visibility Timeout**: 3600 segundos (1 hora) para procesamiento de videos
- **Dead Letter Queue**: Configurada para mensajes fallidos después de 3 reintentos
- **Limitaciones**:
  - Máximo 120,000 mensajes en vuelo
  - Tamaño máximo de mensaje: 256 KB
  - Latencia eventual (no tiempo real)

### 11.2 S3 (Simple Storage Service)
- **Estructura de Prefijos**:
  - `original/` - Videos subidos por usuarios
  - `processed/` - Videos procesados con intro/outro
  - `temp/` - Archivos temporales de procesamiento
- **Presigned URLs**: Válidas por 1 hora para acceso temporal seguro
- **Consideraciones de Rendimiento**:
  - Latencia de transferencia depende del tamaño del archivo
  - Recomendado: Multipart upload para archivos >100MB
  - Throughput: ~5,500 GET/s y ~3,500 PUT/s por prefijo

### 11.3 CloudWatch
- **Embedded Metric Format (EMF)**: Métricas publicadas como JSON en stdout
- **Namespaces**:
  - `ANB/Backend` - Métricas de la API
  - `ANB/Worker` - Métricas del procesador de videos
- **Dimensiones Automáticas**: InstanceId, AvailabilityZone, InstanceType detectados via IMDS v2
- **Retención de Métricas**: 15 meses por defecto
- **Costos**: Basado en número de métricas personalizadas y llamadas a API

## 12. Riesgos y Limitaciones

### 12.1 Limitaciones de Infraestructura
- **Recursos de Hardware**: Limitaciones significativas del entorno de pruebas (2 cores, 4GB RAM, 25GB almacenamiento)
- **Red**: Latencia de red puede afectar resultados (especialmente para transferencias S3)
- **Datos de Prueba**: Uso de datos sintéticos vs. datos reales
- **Configuración**: Diferencias entre entorno de pruebas y producción
- **AWS Academy**: Credenciales temporales con tiempo de expiración (session tokens)

### 12.2 Riesgos de Pruebas
- **Saturación de Recursos**: Posible impacto en el sistema host
- **Costos AWS**: Uso de servicios AWS puede generar costos (S3 storage, data transfer, CloudWatch metrics)
- **Límites de Servicio**: Posible alcance de límites de SQS o S3 durante pruebas de estrés
- **Tiempo de Ejecución**: Pruebas pueden tomar varias horas
- **Interferencias**: Otros procesos en el sistema host
- **Expiración de Credenciales**: AWS Academy session tokens pueden expirar durante pruebas largas

### 12.3 Mitigaciones
- **Ambiente Aislado**: Uso de contenedores Docker para aislamiento
- **Monitoreo Continuo**: Supervisión de recursos y costos durante las pruebas
- **Datos Sintéticos**: Uso de datos de prueba generados (dummy_file_50mb.mp4)
- **Planificación**: Ejecución en horarios de bajo uso del sistema
- **AWS Budget Alerts**: Configurar alarmas de presupuesto en CloudWatch
- **Renovación de Credenciales**: Script para renovar session tokens antes de expiración
- **Límites de Servicio**: Solicitar incremento de límites antes de pruebas si es necesario

## 13. Resultados Esperados

### 13.1 Capacidad de la Capa Web
- **Usuarios Concurrentes Máximos**: 300-500 usuarios
- **RPS Sostenido**: 200-400 requests por segundo
- **Latencia P95**: < 1 segundo
- **Tasa de Errores**: < 2%

### 13.2 Rendimiento del Worker
- **Throughput Base**: 12-15 videos/minuto (4 workers)
- **Escalabilidad**: Mejora lineal con más workers
- **Tiempo de Procesamiento**: 4-5 segundos por video (50MB) + latencia S3 GET/PUT
- **Estabilidad**: Cola SQS estable sin crecimiento descontrolado
- **Visibilidad en SQS**: Mensajes procesados dentro del timeout de 1 hora

### 13.3 Cuellos de Botella Potenciales
- **Base de Datos**: Posible limitación en consultas concurrentes
- **SQS**: Latencia de polling y visibilidad de mensajes
- **S3**: Latencia de transferencia para archivos grandes (GET/PUT)
- **CPU**: Procesamiento de video con FFmpeg
- **Memoria**: Buffer de video durante procesamiento y descarga desde S3
- **Red**: Ancho de banda para transferencias S3

## 14. Recomendaciones de Escalamiento

### 14.1 Escalamiento Horizontal (Recomendado para AWS)
- **API Gateway**: Múltiples instancias EC2 con Application Load Balancer
- **Workers**: Auto Scaling Group basado en métricas de SQS (ApproximateNumberOfMessagesVisible)
- **Base de Datos**: Amazon RDS con Read Replicas para consultas de solo lectura
- **SQS**: Escalamiento automático, sin límite de mensajes
- **S3**: Escalamiento automático, almacenamiento ilimitado

### 14.2 Escalamiento Vertical
- **CPU**: Aumentar a 4-8 cores para mejor procesamiento de video (tipos EC2: c5.xlarge, c5.2xlarge)
- **Memoria**: Aumentar a 8-16GB para buffers de video y concurrencia (tipos EC2: m5.large, m5.xlarge)
- **Red**: Instancias con Enhanced Networking para mejor throughput S3
- **Almacenamiento Local**: SSD de alto rendimiento para archivos temporales (tipos EC2 con NVMe)

### 14.3 Optimizaciones de AWS
- **S3 Transfer Acceleration**: Mejorar velocidad de uploads/downloads
- **S3 Intelligent Tiering**: Optimizar costos de almacenamiento
- **SQS Long Polling**: Ya implementado (20s) para reducir costos
- **CloudWatch Alarms**: Configurar alertas basadas en métricas (CPUUtilization, QueueDepth)
- **VPC Endpoints**: Reducir latencia y costos de transferencia S3/SQS
- **ElastiCache**: Implementar caché para consultas frecuentes (opcional)

### 14.4 Optimizaciones de Código
- **Multipart Upload**: Para videos grandes en S3 (>100MB)
- **Streaming de Video**: Procesamiento por chunks para reducir memoria
- **Presigned URLs**: Ya implementado para acceso temporal seguro (1h expiry)
- **Retry Logic**: Ya implementado (exponential backoff, DLQ)
- **Compresión**: Optimizar parámetros de FFmpeg

### 14.5 Arquitectura de Producción
- **Multi-AZ**: Desplegar en múltiples Availability Zones
- **Application Load Balancer**: Distribución de tráfico con health checks
- **Auto Scaling Groups**: Escalamiento automático basado en métricas
- **RDS Multi-AZ**: Alta disponibilidad de base de datos
- **CloudWatch Dashboards**: Monitoreo unificado del sistema
- **AWS Systems Manager**: Gestión de configuración y secretos

## 15. Conclusión

Este plan de análisis de capacidad proporciona una metodología estructurada para evaluar el rendimiento del sistema ANB Rising Stars Showcase basado en AWS. Los resultados obtenidos permitirán:

1. **Identificar límites operacionales** del sistema actual
2. **Proporcionar datos cuantitativos** para decisiones de escalamiento
3. **Detectar cuellos de botella** antes de que afecten la producción
4. **Validar SLOs** y objetivos de rendimiento
5. **Generar recomendaciones** específicas para optimización
6. **Evaluar el rendimiento de servicios AWS** (SQS, S3, CloudWatch)
7. **Optimizar costos** de servicios AWS basándose en métricas reales

### Beneficios de la Arquitectura AWS

La migración a servicios AWS nativos proporciona:

- **Escalabilidad Automática**: SQS y S3 escalan automáticamente sin intervención
- **Alta Disponibilidad**: Servicios administrados con SLA del 99.9%
- **Observabilidad Integrada**: CloudWatch proporciona métricas y logs unificados
- **Resiliencia**: Dead Letter Queue para manejo de fallos
- **Costos Optimizados**: Pago por uso con posibilidad de optimización (Long Polling, S3 Tiering)

La ejecución de este plan es fundamental para garantizar que el sistema pueda manejar la carga esperada en producción y proporcionar una base sólida para el crecimiento futuro de la aplicación en la nube.
