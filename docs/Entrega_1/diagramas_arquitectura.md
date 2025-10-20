# Diagramas de Arquitectura - ANB Rising Stars Showcase

Este documento presenta los diagramas de arquitectura del sistema ANB Rising Stars Showcase, mostrando diferentes niveles de abstraccion y detalle de los componentes y sus interacciones.

## 1. Diagrama de Contexto

El diagrama de contexto muestra la vision de mas alto nivel del sistema, identificando a los actores principales y sus interacciones con la plataforma ANB Rising Stars Showcase.

<img width="704" height="591" alt="Contexto" src="https://github.com/user-attachments/assets/8fd93a1d-916d-455f-b36e-af250f66b010" />

**Actores principales:**
- **Jugadores**: Usuarios que se registran, suben videos de sus habilidades y consultan su estado
- **Publico General**: Usuarios que visualizan videos y votan por sus jugadores favoritos
- **Administradores**: Personal de ANB que gestiona el sistema

## 2. Diagrama de Contenedores

El diagrama de contenedores descompone el sistema en contenedores de alto nivel (aplicaciones, bases de datos, servicios), mostrando como se comunican entre si.

<img width="1102" height="1288" alt="c2-contenedores" src="https://github.com/user-attachments/assets/e9e2e0fb-3a25-4790-9603-2d269d7fc06e" />

**Contenedores principales:**
## Descripcion de Componentes

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


## 3. Diagrama de Componentes

El diagrama de componentes muestra la estructura interna del Backend API, detallando los modulos y capas que lo componen siguiendo los principios de Domain-Driven Design (DDD).

<img width="1721" height="689" alt="C3-componentes" src="https://github.com/user-attachments/assets/11557da0-3c6f-4b5e-ada9-0c18bddc103b" />

**Capas principales:**
- **Routers**: Definicion de endpoints de la API REST
- **Services**: Logica de negocio y casos de uso
- **Domain**: Entidades, value objects y repositorios (interfaces)
- **Infrastructure**: Implementaciones concretas (base de datos, servicios externos)
- **DTOs**: Objetos de transferencia de datos para comunicacion con clientes

## 4. Diagrama de Entidad-Relacion

El diagrama ER muestra el modelo de datos relacional de la base de datos PostgreSQL, incluyendo las entidades principales y sus relaciones.

<img width="306" height="610" alt="ER" src="https://github.com/user-attachments/assets/93d91a88-9f04-4348-948a-3a1c3c475462" />

**Entidades principales:**
- **Players**: Informacion de jugadores registrados
- **Videos**: Metadata de videos subidos
- **Votes**: Registro de votos por video

## 5. Diagrama de Flujo

El diagrama de flujo ilustra el proceso completo desde que un jugador sube un video hasta que este es procesado y esta disponible para votacion. El flujo se divide en tres etapas principales:

<img width="1625" height="961" alt="Diagrama de Flujo" src="https://github.com/user-attachments/assets/7e8b8800-d5f3-4aba-aab9-6eb2dd05a769" />

### Etapa de Carga
1. El jugador se autentica en el sistema
2. Sube el video a traves del API
3. El sistema guarda el video original y registra la metadata en la base de datos
4. Se publica una tarea de procesamiento en RabbitMQ
5. Se retorna un task_id al jugador

### Etapa de Procesamiento Asincrono
1. El Worker consume la tarea desde RabbitMQ
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

## Referencias

- [Documentacion Tecnica Completa](../../source/README.md)
- [Backend API Documentation](../../source/backend/README.md)
- [Performance Testing Guide](../../source/performance-testing/README.md)