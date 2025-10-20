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

El sistema ANB Rising Stars Showcase es una aplicación de procesamiento de videos que permite a los usuarios subir videos de baloncesto, procesarlos con intro/outro, y participar en un sistema de votación. La arquitectura incluye:

- **Capa Web (FastAPI)**: API REST para autenticación, gestión de videos y votación
- **Capa de Procesamiento (Celery Workers)**: Procesamiento asíncrono de videos con FFmpeg
- **Base de Datos (PostgreSQL)**: Almacenamiento de datos de usuarios, videos y votos
- **Cola de Tareas (Redis)**: Gestión de tareas de procesamiento
- **Almacenamiento de Archivos**: Sistema de archivos local para videos

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
- **Bypass de la Web**: Inyección directa de mensajes en la cola Redis
- **Payloads Realistas**: Uso de archivos de video de diferentes tamaños (50MB)
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
- **Configuración de Redis**: Cola de tareas configurada
- **Configuración de Almacenamiento**: Directorios de uploads configurados

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
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │   Backend API   │    │   PostgreSQL    │
│    (Nginx)      │◄──►│   (FastAPI)     │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Redis Queue   │◄──►│  Celery Workers │
                       │   (Task Queue)  │    │  (Video Proc.)  │
                       └─────────────────┘    └─────────────────┘
```

### 8.2 Infraestructura de Pruebas
- **Sistema Operativo**: Ubuntu Server 24.04.3 LTS (Docker containers)
- **CPU**: 2 cores
- **Memoria RAM**: 4 GB
- **Almacenamiento**: 25 GB
- **Red**: Conexión estable para evitar interferencias

### 8.3 Software de Soporte
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **JMeter**: 5.4+ (para pruebas de carga web)
- **Prometheus**: 2.30+ (para métricas)
- **Grafana**: 8.0+ (para visualización)
- **Redis**: 6.0+ (para cola de tareas)
- **PostgreSQL**: 13+ (para base de datos)

### 8.4 Configuración de Monitoreo
- **Prometheus**: Recolección de métricas del sistema
- **Grafana**: Dashboards para visualización en tiempo real
- **Métricas de Aplicación**: Latencia, throughput, errores
- **Métricas de Sistema**: CPU, memoria, I/O, red

## 9. Herramientas para la Prueba

### 9.1 Generación de Carga
- **JMeter 5.4+**: Para pruebas de la capa web
  - Configuración de usuarios concurrentes
  - Simulación de comportamiento real de usuarios
  - Generación de reportes detallados

### 9.2 Procesamiento Asíncrono
- **Script Producer (Python)**: Para pruebas del worker
  - Inyección directa de tareas en Redis
  - Configuración de parámetros de prueba
  - Monitoreo de progreso

### 9.3 Observabilidad
- **Prometheus**: Recolección y almacenamiento de métricas
- **Grafana**: Visualización y alertas
- **APM (OpenTelemetry)**: Trazabilidad de aplicaciones

### 9.4 Análisis de Resultados
- **JMeter Reports**: Análisis de resultados de carga web
- **Grafana Dashboards**: Monitoreo en tiempo real
- **Logs de Aplicación**: Análisis de errores y comportamiento

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
- **CPU**: Uso de procesador por componente
- **Memoria**: Consumo de RAM por servicio
- **I/O**: Operaciones de disco y red
- **Conectividad**: Latencia de red entre componentes

### 10.4 Métricas de Negocio
- **Tiempo de Subida**: Tiempo para subir un video
- **Tiempo de Procesamiento**: Tiempo total de procesamiento
- **Disponibilidad**: Tiempo de actividad del sistema
- **Escalabilidad**: Capacidad de crecimiento

## 11. Riesgos y Limitaciones

### 11.1 Limitaciones Identificadas
- **Recursos de Hardware**: Limitaciones significativas del entorno de pruebas (2 cores, 4GB RAM, 25GB almacenamiento)
- **Red**: Latencia de red puede afectar resultados
- **Datos de Prueba**: Uso de datos sintéticos vs. datos reales
- **Configuración**: Diferencias entre entorno de pruebas y producción

### 11.2 Riesgos de Pruebas
- **Saturación de Recursos**: Posible impacto en el sistema host
- **Datos de Prueba**: Necesidad de anonimización si se usan datos reales
- **Tiempo de Ejecución**: Pruebas pueden tomar varias horas
- **Interferencias**: Otros procesos en el sistema host

### 11.3 Mitigaciones
- **Ambiente Aislado**: Uso de contenedores Docker para aislamiento
- **Monitoreo Continuo**: Supervisión de recursos durante las pruebas
- **Datos Sintéticos**: Uso de datos de prueba generados
- **Planificación**: Ejecución en horarios de bajo uso del sistema

## 12. Resultados Esperados

### 12.1 Capacidad de la Capa Web
- **Usuarios Concurrentes Máximos**: 300-500 usuarios
- **RPS Sostenido**: 200-400 requests por segundo
- **Latencia P95**: < 1 segundo
- **Tasa de Errores**: < 2%

### 12.2 Rendimiento del Worker
- **Throughput Base**: 12-15 videos/minuto (4 workers)
- **Escalabilidad**: Mejora lineal con más workers
- **Tiempo de Procesamiento**: 4-5 segundos por video (50MB)
- **Estabilidad**: Cola estable sin crecimiento descontrolado

### 12.3 Cuellos de Botella Identificados
- **Base de Datos**: Posible limitación en consultas concurrentes
- **Almacenamiento**: I/O de disco para archivos grandes
- **CPU**: Procesamiento de video con FFmpeg
- **Memoria**: Buffer de video durante procesamiento

## 13. Recomendaciones de Escalamiento

### 13.1 Escalamiento Horizontal
- **API Gateway**: Múltiples instancias con load balancer
- **Workers**: Aumentar número de workers según demanda
- **Base de Datos**: Read replicas para consultas de solo lectura
- **Almacenamiento**: Distribución de archivos en múltiples nodos

### 13.2 Escalamiento Vertical (Recomendado para este entorno)
- **CPU**: Aumentar a 4-8 cores para mejor procesamiento de video
- **Memoria**: Aumentar a 8-16GB para buffers de video y concurrencia
- **Almacenamiento**: SSD de alto rendimiento (actualmente limitado a 25GB)
- **Red**: Mayor ancho de banda para transferencia de archivos

### 13.3 Optimizaciones de Código
- **Caché**: Implementar Redis para consultas frecuentes
- **Compresión**: Optimizar archivos de video
- **Procesamiento Asíncrono**: Mejorar la gestión de colas
- **Monitoreo**: Implementar alertas proactivas

### 13.4 Arquitectura de Producción
- **Microservicios**: Separación de responsabilidades
- **API Gateway**: Gestión centralizada de tráfico
- **Service Mesh**: Comunicación entre servicios
- **Observabilidad**: Monitoreo completo del sistema

## 14. Conclusión

Este plan de análisis de capacidad proporciona una metodología estructurada para evaluar el rendimiento del sistema ANB Rising Stars Showcase. Los resultados obtenidos permitirán:

1. **Identificar límites operacionales** del sistema actual
2. **Proporcionar datos cuantitativos** para decisiones de escalamiento
3. **Detectar cuellos de botella** antes de que afecten la producción
4. **Validar SLOs** y objetivos de rendimiento
5. **Generar recomendaciones** específicas para optimización

La ejecución de este plan es fundamental para garantizar que el sistema pueda manejar la carga esperada en producción y proporcionar una base sólida para el crecimiento futuro de la aplicación.
