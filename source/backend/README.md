# ANB Rising Stars Showcase API

API REST para la plataforma ANB Rising Stars Showcase - Gestión de videos de habilidades de baloncesto.

## 🏀 Descripción

Esta API permite a los jugadores de baloncesto:
- Registrarse y autenticarse en la plataforma
- Subir videos de sus mejores jugadas
- Votar por videos de otros jugadores
- Ver rankings dinámicos por ciudad

## 🏛️ Arquitectura

Esta API está implementada siguiendo los principios de **Domain-Driven Design (DDD)** y **Clean Architecture**:

- ✅ **Separación clara de responsabilidades**
- ✅ **Fácil cambio de implementaciones** (ej: cambiar de almacenamiento local a S3)
- ✅ **Testabilidad mejorada**
- ✅ **Mantenibilidad y escalabilidad**
- ✅ **Inversión de dependencias**

## 🚀 Tecnologías

- **FastAPI** - Framework web moderno y rápido
- **PostgreSQL** - Base de datos relacional
- **SQLAlchemy** - ORM para Python
- **JWT** - Autenticación basada en tokens
- **Pydantic** - Validación de datos
- **Alembic** - Migraciones de base de datos
- **DDD + Clean Architecture** - Patrones arquitectónicos

## 📁 Estructura del Proyecto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Aplicación principal FastAPI
│   ├── domain/                 # 🎯 Capa de Dominio
│   │   ├── entities/           # Entidades de negocio
│   │   │   ├── player.py       # Entidad Player
│   │   │   ├── video.py        # Entidad Video
│   │   │   └── vote.py         # Entidad Vote
│   │   ├── value_objects/      # Objetos de valor
│   │   │   ├── email.py        # Value Object Email
│   │   │   └── password.py     # Value Object Password
│   │   └── repositories/       # Interfaces de repositorios
│   │       ├── player_repository.py
│   │       ├── video_repository.py
│   │       └── vote_repository.py
│   ├── services/               # 🔧 Servicios de Aplicación
│   │   ├── player_service.py   # Servicio de jugadores
│   │   └── video_service.py    # Servicio de videos
│   ├── dtos/                   # Data Transfer Objects
│   │   ├── player_dtos.py      # DTOs de jugadores
│   │   └── video_dtos.py       # DTOs de videos
│   ├── infrastructure/         # 🔌 Capa de Infraestructura
│   │   ├── database/           # Configuración de BD
│   │   │   ├── database.py
│   │   │   └── models.py       # Modelos SQLAlchemy
│   │   ├── external_services/  # Servicios externos
│   │   │   ├── jwt_auth_service.py
│   │   │   ├── local_file_storage.py
│   │   │   ├── s3_file_storage.py
│   │   │   └── celery_client.py
│   │   └── repositories/       # Implementaciones de repositorios
│   │       ├── player_repository.py
│   │       ├── video_repository.py
│   │       └── vote_repository.py
│   ├── shared/                 # 🔄 Capa Compartida
│   │   ├── interfaces/         # Interfaces compartidas
│   │   │   ├── authentication.py
│   │   │   ├── file_storage.py
│   │   │   └── task_queue.py
│   │   ├── exceptions/         # Excepciones del dominio
│   │   │   ├── player_exceptions.py
│   │   │   └── video_exceptions.py
│   │   ├── dependencies/       # Dependencias de FastAPI
│   │   │   └── auth_dependencies.py
│   │   └── container.py        # Contenedor de dependencias
│   ├── config/                 # ⚙️ Configuración
│   │   ├── settings.py         # Configuración de la aplicación
│   │   └── container_config.py # Configuración del contenedor
│   └── routers/                # 🌐 Capa de Presentación
│       ├── __init__.py
│       ├── auth.py             # Endpoints de autenticación
│       ├── videos.py           # Endpoints de videos
│       └── public.py           # Endpoints públicos
├── tests/                      # Pruebas
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_videos.py
│   ├── test_public.py
│   ├── test_basic.py
│   └── test_auth_simple.py
├── uploads/                    # Archivos subidos (local)
│   ├── original/               # Videos originales
│   └── processed/              # Videos procesados
├── alembic/                    # Migraciones de BD
├── requirements.txt
├── start.py                    # Script de inicio
├── migrate.py                  # Script de migraciones
├── app_test_main.py            # Aplicación para tests
└── README.md
```

## 🔧 Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/fileprocessing"
   export REDIS_URL="redis://localhost:6379/0"
   export SECRET_KEY="your-secret-key-here"
   export FILE_STORAGE_TYPE="local"  # o "s3"
   export EMAIL_SERVICE_TYPE="console"  # o "sendgrid"
   ```

5. **Configurar base de datos**
   ```bash
   # Crear base de datos PostgreSQL
   createdb anb_rising_stars
   
   # Ejecutar migraciones
   python migrate.py
   ```

6. **Ejecutar la aplicación**
   ```bash
   python start.py
   ```

## 🧪 Testing

```bash
# Ejecutar todas las pruebas
python3 -m pytest tests/ -v

# Ejecutar pruebas con cobertura
python3 -m pytest tests/ --cov=app

# Ejecutar pruebas específicas
python3 -m pytest tests/test_auth.py -v
python3 -m pytest tests/test_videos.py -v
python3 -m pytest tests/test_public.py -v

# Ejecutar pruebas básicas
python3 -m pytest tests/test_basic.py -v
```

### Estado de las Pruebas
- ✅ **37/37 tests pasando** (100% de éxito)
- ✅ Tests de autenticación (7/7)
- ✅ Tests de videos (10/10)
- ✅ Tests públicos (10/10)
- ✅ Tests básicos (5/5)
- ✅ Tests simples (5/5)

## 📚 Documentación de la API

Una vez que la aplicación esté ejecutándose, puedes acceder a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 Endpoints Principales

### Autenticación
- `POST /auth/signup` - Registro de jugadores
- `POST /auth/login` - Inicio de sesión
- `GET /auth/me` - Información del usuario actual

### Gestión de Videos
- `POST /videos/upload` - Subir video (requiere autenticación)
- `GET /videos` - Listar videos del usuario (requiere autenticación)
- `GET /videos/{video_id}` - Obtener video específico (requiere autenticación)
- `DELETE /videos/{video_id}` - Eliminar video (requiere autenticación)

### Endpoints Públicos
- `GET /public/videos` - Listar videos públicos para votación
- `POST /public/videos/{video_id}/vote` - Votar por video (requiere autenticación)
- `GET /public/rankings` - Obtener rankings de jugadores
- `GET /public/rankings?city=Ciudad` - Rankings filtrados por ciudad

### Endpoints del Sistema
- `GET /` - Información de la API
- `GET /health` - Health check
- `GET /config` - Configuración actual (desarrollo)

## 🔄 Cambio Fácil de Implementaciones

### Cambiar de Almacenamiento Local a S3

**1. Configurar variables de entorno:**
```bash
export FILE_STORAGE_TYPE=s3
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export S3_BUCKET_NAME=your_bucket
```

**2. El código NO cambia:**
```python
# El servicio sigue usando la misma interfaz
video_service = VideoService(
    file_storage=container.get(FileStorageInterface)  # Automáticamente S3
)
```


## 🎯 Beneficios de esta Arquitectura

### 1. **Flexibilidad**
- Cambiar implementaciones sin modificar código de negocio
- Fácil migración entre proveedores (local → S3 → Azure)
- Testing independiente de infraestructura

### 2. **Mantenibilidad**
- Código organizado por responsabilidades
- Fácil localización de funcionalidades
- Cambios aislados por capas

### 3. **Escalabilidad**
- Agregar nuevas funcionalidades sin afectar existentes
- Implementar nuevas interfaces fácilmente
- Separación clara de concerns

### 4. **Testabilidad**
- Mocking simple de dependencias
- Tests unitarios independientes
- Tests de integración por capas

## 📝 Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `DATABASE_URL` | URL de conexión a PostgreSQL | `postgresql://user:password@localhost:5432/fileprocessing` |
| `REDIS_URL` | URL de conexión a Redis | `redis://localhost:6379/0` |
| `SECRET_KEY` | Clave secreta para JWT | `your-secret-key-here` |
| `FILE_STORAGE_TYPE` | Tipo de almacenamiento | `local` |

## 🐳 Docker

```bash
# Construir imagen
docker build -t anb-rising-stars-api .

# Ejecutar contenedor
docker run -p 8000:8000 anb-rising-stars-api
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request


## 📚 Documentación Adicional

- [Arquitectura DDD](ARCHITECTURE.md) - Explicación detallada de la arquitectura
