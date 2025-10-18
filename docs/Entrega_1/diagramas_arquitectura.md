# Diagrama de Arquitectura - ANB Rising Stars Showcase

Este documento presenta el diagrama de arquitectura del sistema ANB Rising Stars Showcase, mostrando los componentes principales y sus interacciones.

## Arquitectura de Microservicios

El sistema esta construido siguiendo una arquitectura de microservicios con comunicacion asincrona entre componentes.

### Diagrama de Componentes

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │
│    (NGINX)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐         ┌──────────────┐
│   Backend API   │────────▶│  PostgreSQL  │
│   (FastAPI)     │         │   Database   │
└────────┬────────┘         └──────────────┘
         │
         │ (Publica tareas)
         ▼
┌─────────────────┐
│    RabbitMQ     │
│ (Message Broker)│
└────────┬────────┘
         │
         │ (Consume tareas)
         ▼
┌─────────────────┐         ┌──────────────┐
│     Worker      │────────▶│ Almacenamiento│
│    (Celery)     │         │  de Videos   │
└─────────────────┘         └──────────────┘
```

## Descripcion de Componentes

### Cliente
El cliente representa cualquier aplicacion o navegador que consume la API REST. Se comunica con el sistema a traves del API Gateway.

### API Gateway (NGINX)
- **Proposito**: Punto de entrada unico al sistema
- **Funciones**:
  - Enrutamiento de peticiones HTTP
  - Balanceo de carga
  - Terminacion SSL/TLS
  - Proxy reverso
- **Tecnologia**: NGINX
- **Puerto**: 80 (HTTP)

### Backend API (FastAPI)
- **Proposito**: Nucleo de la logica de negocio
- **Funciones**:
  - Gestion de autenticacion y autorizacion (JWT)
  - CRUD de jugadores y videos
  - Sistema de votacion
  - Publicacion de tareas de procesamiento en RabbitMQ
  - Generacion de rankings
- **Tecnologia**: FastAPI (Python)
- **Patron de Arquitectura**: Domain-Driven Design (DDD)
- **Base de Datos**: PostgreSQL

### PostgreSQL Database
- **Proposito**: Almacenamiento persistente de datos
- **Datos Almacenados**:
  - Informacion de jugadores (usuarios)
  - Metadata de videos
  - Votos
  - Estado de procesamiento de videos
- **Tecnologia**: PostgreSQL 15
- **Puerto**: 5432

### RabbitMQ (Message Broker)
- **Proposito**: Cola de mensajes para procesamiento asincrono
- **Funciones**:
  - Desacoplar el backend del worker
  - Garantizar entrega de tareas de procesamiento
  - Permitir escalabilidad horizontal de workers
  - Persistencia de tareas pendientes
- **Tecnologia**: RabbitMQ
- **Puerto**: 5672 (AMQP), 15672 (Management Console)

### Worker (Celery)
- **Proposito**: Procesamiento asincrono de videos
- **Funciones**:
  - Consumir tareas desde RabbitMQ
  - Procesar videos (recortar, ajustar resolucion, marca de agua, eliminar audio)
  - Actualizar estado de videos en la base de datos
  - Guardar videos procesados en el almacenamiento
- **Tecnologia**: Celery + FFmpeg + Python
- **Caracteristicas**:
  - Procesamiento en background
  - Reintentos automaticos en caso de fallo
  - Escalable horizontalmente

### Almacenamiento de Videos
- **Proposito**: Guardar archivos de video originales y procesados
- **Opciones**:
  - **Local**: Sistema de archivos local (desarrollo)
  - **S3**: Amazon S3 (produccion)
- **Tipos de Videos**:
  - Videos originales subidos por jugadores
  - Videos procesados (30s, marca de agua ANB, sin audio)

## Flujo de Datos

### 1. Registro y Autenticacion
```
Cliente → API Gateway → Backend API → PostgreSQL
                            ↓
                    (Genera JWT Token)
                            ↓
Cliente ← API Gateway ← Backend API
```

### 2. Subida de Video
```
Cliente → API Gateway → Backend API → PostgreSQL (guarda metadata)
                            ↓
                    Almacenamiento (guarda video original)
                            ↓
                        RabbitMQ (publica tarea)
                            ↓
Cliente ← API Gateway ← Backend API (retorna task_id)
```

### 3. Procesamiento de Video (Asincrono)
```
RabbitMQ → Worker → Almacenamiento (lee video original)
              ↓
    (Procesa video con FFmpeg)
              ↓
         Almacenamiento (guarda video procesado)
              ↓
         PostgreSQL (actualiza estado a "procesado")
```

### 4. Votacion
```
Cliente → API Gateway → Backend API → PostgreSQL (registra voto)
                            ↓
Cliente ← API Gateway ← Backend API (confirma voto)
```

### 5. Consulta de Ranking
```
Cliente → API Gateway → Backend API → PostgreSQL (consulta votos)
                            ↓
Cliente ← API Gateway ← Backend API (retorna ranking)
```

## Ventajas de esta Arquitectura

### Escalabilidad
- **Escalabilidad Horizontal**: Se pueden agregar multiples workers para procesar videos en paralelo
- **Balanceo de Carga**: NGINX distribuye las peticiones entre multiples instancias del backend
- **Cola de Mensajes**: RabbitMQ permite manejar picos de carga sin perder tareas

### Resiliencia
- **Desacoplamiento**: El backend no se bloquea esperando el procesamiento de videos
- **Reintentos**: Las tareas fallidas se pueden reintentar automaticamente
- **Persistencia**: Las tareas quedan guardadas en RabbitMQ aunque el worker este caido

### Mantenibilidad
- **Separacion de Responsabilidades**: Cada componente tiene una funcion clara
- **Independencia**: Los componentes pueden actualizarse sin afectar a los demas
- **Observabilidad**: Cada componente genera logs independientes

### Performance
- **Procesamiento Asincrono**: Los usuarios no esperan que se procese el video
- **Cache**: NGINX puede cachear respuestas estaticas
- **Optimizacion de Recursos**: El procesamiento de video se hace en workers dedicados

## Patrones de Diseno Implementados

### 1. API Gateway Pattern
- NGINX actua como punto de entrada unico
- Centraliza autenticacion, logging y routing

### 2. Message Queue Pattern
- RabbitMQ desacopla productores (backend) de consumidores (workers)
- Permite procesamiento asincrono y escalabilidad

### 3. Worker Pattern
- Workers especializados en tareas pesadas (procesamiento de video)
- Multiples workers pueden procesar tareas en paralelo

### 4. Repository Pattern
- El backend usa repositorios para abstraer el acceso a datos
- Facilita testing y cambios de base de datos

## Tecnologias Utilizadas

| Componente | Tecnologia | Version |
|-----------|-----------|---------|
| API Gateway | NGINX | Latest |
| Backend API | FastAPI | 0.100+ |
| Base de Datos | PostgreSQL | 15 |
| Message Broker | RabbitMQ | 3.12+ |
| Worker | Celery + Python | 5.3+ |
| Procesamiento Video | FFmpeg | 6.0+ |
| Contenedores | Docker | 20.10+ |
| Orquestacion | Docker Compose | 2.0+ |

## Consideraciones de Seguridad

- **Autenticacion**: JWT tokens para autenticar usuarios
- **Autorizacion**: Solo los propietarios pueden acceder a sus videos
- **Validacion**: Validacion de tipos y tamanos de archivos
- **HTTPS**: El API Gateway puede configurarse con SSL/TLS
- **Secrets**: Variables de entorno para credenciales sensibles

## Referencias

- [Documentacion Tecnica Completa](../../source/README.md)
- [Backend API Documentation](../../source/backend/README.md)
- [Performance Testing Guide](../../source/performance-testing/README.md)