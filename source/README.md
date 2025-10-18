# ANB Rising Stars Showcase - Codigo Fuente

Este directorio contiene todos los archivos fuente de la aplicacion ANB Rising Stars Showcase, incluyendo el backend API, worker de procesamiento de videos, configuracion de servicios y pruebas de rendimiento.

## Arquitectura del Sistema

La aplicacion esta construida siguiendo una arquitectura de microservicios con los siguientes componentes:

### Componentes Principales

- **Backend API** ([backend/](backend/README.md)): API REST desarrollada en FastAPI (Python) que gestiona la logica de negocio, autenticacion y persistencia de datos.
- **Worker** ([worker/](worker/)): Servicio de procesamiento asincrono de videos utilizando Celery para el procesamiento batch.
- **Base de Datos** ([database/](database/)): PostgreSQL para almacenamiento persistente de informacion de jugadores, videos y votaciones.
- **Message Broker**: RabbitMQ para la comunicacion asincrona entre servicios.
- **API Gateway** ([api-gateway/](api-gateway/)): NGINX como punto de entrada unico y balanceador de carga.
- **Almacenamiento**: Sistema de almacenamiento de archivos (S3 o local) para videos originales y procesados.
- **Performance Testing** ([performance-testing/](performance-testing/README.md)): Suite de pruebas de rendimiento y carga con JMeter, Prometheus y Grafana. Este componente no forma parte de la aplicacion en produccion, pero es esencial para evaluar la capacidad y escalabilidad del sistema.

### Diagrama de Arquitectura

Para ver el diagrama detallado de la arquitectura del sistema, los flujos de datos y la descripcion completa de cada componente, consulte:

**[Diagrama de Arquitectura Completo](../docs/Entrega_1/diagramas_arquitectura.md)**

## Tecnologias Utilizadas

### Backend
- **FastAPI**: Framework web moderno y de alto rendimiento para Python
- **SQLAlchemy**: ORM para interaccion con la base de datos PostgreSQL
- **Alembic**: Herramienta de migracion de base de datos
- **Pydantic**: Validacion de datos y configuracion basada en tipos
- **JWT (JSON Web Tokens)**: Autenticacion y autorizacion basada en tokens
- **Python 3.11+**: Lenguaje de programacion principal

### Procesamiento de Videos
- **Celery**: Sistema de cola de tareas distribuidas para procesamiento asincrono
- **FFmpeg**: Libreria de procesamiento y transformacion de videos
- **Pillow (PIL)**: Procesamiento de imagenes para marcas de agua
- **MoviePy**: Manipulacion y edicion de videos

### Infraestructura
- **Docker & Docker Compose**: Contenedorizacion y orquestacion de servicios
- **PostgreSQL 15**: Base de datos relacional
- **RabbitMQ**: Message broker para comunicacion asincrona
- **NGINX**: API Gateway, servidor web y balanceador de carga
- **Redis**: Cache y almacenamiento de sesiones (opcional)

### Performance Testing (Entorno Separado)
El directorio `performance-testing/` incluye un stack independiente de Docker Compose para pruebas de rendimiento:
- **Apache JMeter**: Herramienta de pruebas de carga y rendimiento de aplicaciones
- **Prometheus**: Sistema de monitoreo y base de datos de series temporales
- **Grafana**: Plataforma de visualizacion y analisis de metricas
- **Python**: Scripts personalizados para pruebas de rendimiento del worker

**Nota**: Las herramientas de performance testing se ejecutan en un entorno Docker separado y no forman parte del stack de produccion.

### Testing y Calidad
- **Pytest**: Framework de testing para Python
- **Coverage.py**: Medicion de cobertura de codigo

## Estructura de Directorios

```
source/
├── backend/                      # API REST en FastAPI
│   ├── app/                      # Codigo fuente de la aplicacion
│   │   ├── config/              # Configuracion de la aplicacion
│   │   ├── domain/              # Entidades y logica de dominio
│   │   │   ├── entities/        # Entidades del dominio
│   │   │   ├── repositories/    # Interfaces de repositorios
│   │   │   └── value_objects/   # Value Objects
│   │   ├── dtos/                # Data Transfer Objects
│   │   ├── infrastructure/      # Implementaciones de infraestructura
│   │   │   ├── database/        # Configuracion de base de datos
│   │   │   ├── external_services/ # Servicios externos
│   │   │   └── repositories/    # Implementacion de repositorios
│   │   ├── routers/             # Endpoints de la API
│   │   ├── services/            # Logica de negocio
│   │   └── shared/              # Codigo compartido
│   ├── tests/                   # Pruebas unitarias y de integracion
│   ├── alembic/                 # Migraciones de base de datos
│   ├── requirements.txt         # Dependencias de Python
│   ├── Dockerfile               # Imagen Docker del backend
│   └── README.md                # Documentacion del backend
│
├── worker/                       # Worker de procesamiento de videos
│   ├── tasks/                   # Tareas de Celery
│   ├── utils/                   # Utilidades para procesamiento
│   ├── tests/                   # Pruebas del worker
│   ├── assets/                  # Assets (logos, intro, outro)
│   ├── celery_app.py           # Configuracion de Celery
│   ├── requirements.txt         # Dependencias de Python
│   └── Dockerfile               # Imagen Docker del worker
│
├── api-gateway/                 # Configuracion de NGINX
│   ├── nginx.conf              # Configuracion principal
│   ├── default.conf            # Configuracion de sitios
│   └── Dockerfile              # Imagen Docker de NGINX
│
├── database/                    # Configuracion de base de datos
│   ├── init.sql                # Script de inicializacion
│   └── Dockerfile              # Imagen Docker de PostgreSQL
│
├── performance-testing/         # Pruebas de rendimiento (Docker separado)
│   ├── web-api-tests/          # Tests de JMeter para la API
│   │   └── scenarios/          # Escenarios de prueba
│   ├── worker-tests/           # Tests de rendimiento del worker
│   ├── grafana/                # Configuracion de Grafana
│   ├── prometheus/             # Configuracion de Prometheus
│   ├── docker-compose.testing.yml # Stack Docker para pruebas
│   └── README.md               # Documentacion de pruebas
│
├── docker-compose.yml           # Orquestacion de servicios
└── docker-compose.dev.yml       # Orquestacion de servicios (desarrollo)
```

## Requisitos Previos

### Software
- **Docker Desktop**: Version 20.10 o superior
- **Docker Compose**: Version 2.0 o superior

### Recursos del Sistema
- **S.O**: Ubuntu Server 24.04.3 LTS
- **RAM**: 4 GB
- **CPU**: 2 Cores
- **Almacenamiento**: 25 GB

## Instalacion y Configuracion

### 1. Configurar Variables de Entorno

El backend requiere configuracion especifica. Para detalles completos sobre la configuracion de variables de entorno, consulte:

**[backend/README.md](backend/README.md)** - Configuracion detallada del backend

Resumen rapido:
```bash
cd backend
cp config.env.example config.env
# Editar config.env con las variables necesarias
```

### 2. Levantar los Servicios

El archivo `docker-compose.yml` se encuentra en el directorio `source/`. Puede ejecutar los servicios de dos formas:

#### Opcion 1: Desde el directorio source
```bash
cd source
docker-compose up --build
```

#### Opcion 2: Desde el directorio raiz
```bash
docker-compose -f source/docker-compose.yml up --build
```


## Uso del Sistema

### Flujo de Trabajo Principal

1. **Registro de Jugador**: Un usuario se registra como jugador
2. **Autenticacion**: El jugador inicia sesion y obtiene un token JWT
3. **Subida de Video**: El jugador sube un video de sus habilidades
4. **Procesamiento Asincrono**:
   - El backend crea una tarea en RabbitMQ
   - El worker consume la tarea y procesa el video
   - El video se recorta, se ajusta la resolucion, se agrega marca de agua y se elimina el audio
   - El estado del video se actualiza a "procesado"
5. **Visualizacion y Votacion**: El publico puede ver los videos procesados y votar
6. **Ranking**: Se actualiza el ranking de jugadores segun los votos

### Endpoints Principales

- `POST /api/auth/register` - Registro de nuevo jugador
- `POST /api/auth/login` - Inicio de sesion
- `POST /api/videos/upload` - Subir video
- `GET /api/videos` - Listar videos procesados
- `GET /api/videos/processed/{video_id}` - Descargar video procesado
- `GET /api/videos/original/{video_id}` - Descargar video original
- `POST /api/videos/{id}/vote` - Votar por un video
- `GET /api/public/ranking` - Obtener ranking de jugadores

Para documentacion completa de los endpoints, ver:
- **[Coleccion de Postman](../collections/README.md)**

## Pruebas

### Ejecutar Pruebas Unitarias

#### Opcion 1: Desde el directorio source
```bash
# Backend
docker-compose exec backend pytest

# Con cobertura
docker-compose exec backend pytest --cov=app --cov-report=html

# Worker
docker-compose exec worker pytest
```

#### Opcion 2: Desde el directorio raiz
```bash
# Backend
docker-compose -f source/docker-compose.yml exec backend pytest

# Con cobertura
docker-compose -f source/docker-compose.yml exec backend pytest --cov=app --cov-report=html

# Worker
docker-compose -f source/docker-compose.yml exec worker pytest
```

### Ejecutar Pruebas de Rendimiento

Las pruebas de rendimiento se realizan con Apache JMeter en un stack Docker separado. Ver documentacion detallada en:

**[performance-testing/README.md](performance-testing/README.md)**

Tipos de pruebas disponibles:
- **Smoke Test**: Validacion basica con carga minima
- **Ramp-up Test**: Incremento gradual de usuarios
- **Sustained Test**: Carga sostenida por periodo prolongado
- **Worker Performance Test**: Rendimiento del procesamiento de videos

## Logs

Ver logs de los servicios:

#### Opcion 1: Desde el directorio source
```bash
# Todos los servicios
docker-compose logs -f

# Servicio especifico
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f rabbitmq
```

#### Opcion 2: Desde el directorio raiz
```bash
# Todos los servicios
docker-compose -f source/docker-compose.yml logs -f

# Servicio especifico
docker-compose -f source/docker-compose.yml logs -f backend
docker-compose -f source/docker-compose.yml logs -f worker
docker-compose -f source/docker-compose.yml logs -f rabbitmq
```

## Detener y Limpiar

#### Opcion 1: Desde el directorio source
```bash
# Detener servicios
docker-compose down

# Detener y eliminar volumenes (cuidado! elimina datos)
docker-compose down -v

# Limpiar imagenes huerfanas
docker image prune
```

#### Opcion 2: Desde el directorio raiz
```bash
# Detener servicios
docker-compose -f source/docker-compose.yml down

# Detener y eliminar volumenes (cuidado! elimina datos)
docker-compose -f source/docker-compose.yml down -v

# Limpiar imagenes huerfanas
docker image prune
```

## Troubleshooting

### El backend no se conecta a la base de datos

Verificar que el servicio de PostgreSQL este ejecutandose:

**Desde el directorio source:**
```bash
docker-compose ps database
docker-compose logs database
```

**Desde el directorio raiz:**
```bash
docker-compose -f source/docker-compose.yml ps database
docker-compose -f source/docker-compose.yml logs database
```

### El worker no procesa videos

Verificar la conexion con RabbitMQ:

**Desde el directorio source:**
```bash
docker-compose logs rabbitmq
docker-compose logs worker
```

**Desde el directorio raiz:**
```bash
docker-compose -f source/docker-compose.yml logs rabbitmq
docker-compose -f source/docker-compose.yml logs worker
```

Acceder a RabbitMQ Management Console para verificar las colas:
http://localhost:15672

### Videos no se almacenan correctamente

Verificar la configuracion de almacenamiento en `backend/config.env`:
- Si `STORAGE_TYPE=local`, verificar que el directorio de almacenamiento tenga permisos

## Licencia

Este proyecto es desarrollado como parte del curso MISW-4204 Desarrollo de Software en la Nube de la Universidad de los Andes.