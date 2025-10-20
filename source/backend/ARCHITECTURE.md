# 🏗️ Arquitectura DDD - ANB Rising Stars Showcase API

## 📋 Resumen

Esta API está implementada siguiendo los principios de **Domain-Driven Design (DDD)** y patrones de arquitectura limpia, lo que permite:

- ✅ **Separación clara de responsabilidades**
- ✅ **Fácil cambio de implementaciones** (ej: cambiar de almacenamiento local a S3)
- ✅ **Testabilidad mejorada**
- ✅ **Mantenibilidad y escalabilidad**
- ✅ **Inversión de dependencias**

## 🏛️ Estructura de Capas

```
app/
├── domain/                    # 🎯 Capa de Dominio
│   ├── entities/             # Entidades de negocio
│   │   ├── player.py         # Entidad Player
│   │   ├── video.py          # Entidad Video
│   │   └── vote.py           # Entidad Vote
│   ├── value_objects/        # Objetos de valor
│   │   ├── email.py          # Value Object Email
│   │   └── password.py       # Value Object Password
│   └── repositories/         # Interfaces de repositorios
│       ├── player_repository.py
│       ├── video_repository.py
│       └── vote_repository.py
├── services/                 # 🔧 Servicios de Aplicación
│   ├── player_service.py     # Servicio de jugadores
│   └── video_service.py      # Servicio de videos
├── dtos/                     # Data Transfer Objects
│   ├── player_dtos.py        # DTOs de jugadores
│   └── video_dtos.py         # DTOs de videos
├── infrastructure/           # 🔌 Capa de Infraestructura
│   ├── database/             # Configuración de BD
│   │   ├── database.py
│   │   └── models.py         # Modelos SQLAlchemy
│   ├── external_services/    # Servicios externos
│   │   ├── jwt_auth_service.py
│   │   ├── local_file_storage.py
│   │   ├── s3_file_storage.py
│   │   └── celery_client.py
│   └── repositories/         # Implementaciones de repositorios
│       ├── player_repository.py
│       ├── video_repository.py
│       └── vote_repository.py
├── shared/                   # 🔄 Capa Compartida
│   ├── interfaces/           # Interfaces compartidas
│   │   ├── authentication.py
│   │   ├── file_storage.py
│   │   └── task_queue.py
│   ├── exceptions/           # Excepciones del dominio
│   │   ├── player_exceptions.py
│   │   └── video_exceptions.py
│   ├── dependencies/         # Dependencias de FastAPI
│   │   └── auth_dependencies.py
│   └── container.py          # Contenedor de dependencias
├── config/                   # ⚙️ Configuración
│   ├── settings.py           # Configuración de la aplicación
│   └── container_config.py   # Configuración del contenedor
└── routers/                  # 🌐 Capa de Presentación
    ├── auth.py               # Endpoints de autenticación
    ├── videos.py             # Endpoints de videos
    └── public.py             # Endpoints públicos
```

## 🎯 Principios Aplicados

### 1. **Inversión de Dependencias**
```python
# ❌ Antes: Dependencia directa
class VideoService:
    def __init__(self):
        self.file_storage = LocalFileStorage()  # Acoplado

# ✅ Ahora: Dependencia de interfaz
class VideoService:
    def __init__(self, file_storage: FileStorageInterface):
        self.file_storage = file_storage  # Desacoplado
```

### 2. **Separación de Responsabilidades**
- **Domain**: Lógica de negocio pura
- **Application**: Casos de uso y orquestación
- **Infrastructure**: Implementaciones técnicas
- **Presentation**: Controllers y DTOs

### 3. **Interfaces para Abstracción**
```python
# Interface para almacenamiento de archivos
class FileStorageInterface(ABC):
    @abstractmethod
    async def save_file(self, file: UploadFile, filename: str) -> str:
        pass

# Implementación local
class LocalFileStorage(FileStorageInterface):
    async def save_file(self, file: UploadFile, filename: str) -> str:
        # Implementación local...

# Implementación S3
class S3FileStorage(FileStorageInterface):
    async def save_file(self, file: UploadFile, filename: str) -> str:
        # Implementación S3...
```

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

### Cambiar de Email Console a SendGrid

**1. Configurar variables de entorno:**
```bash
export EMAIL_SERVICE_TYPE=sendgrid
export SENDGRID_API_KEY=your_api_key
```

**2. El código NO cambia:**
```python
# El servicio sigue usando la misma interfaz
email_service = container.get(EmailServiceInterface)  # Automáticamente SendGrid
```

## 🧪 Testing Mejorado

### Mocking de Dependencias
```python
# Test con mock
def test_upload_video():
    mock_file_storage = Mock(spec=FileStorageInterface)
    mock_file_storage.save_file.return_value = "path/to/file"
    
    video_service = VideoService(
        file_storage=mock_file_storage,
        # ... otras dependencias
    )
    
    # Test sin dependencias reales
    result = await video_service.upload_video(...)
    assert result.filename == "expected_filename"
```

## 📦 Inyección de Dependencias

### Configuración del Contenedor
```python
# app/config/container_config.py
def configure_container():
    # Almacenamiento de archivos
    if settings.FILE_STORAGE_TYPE == FileStorageType.LOCAL:
        container.register_singleton(FileStorageInterface, LocalFileStorage)
    elif settings.FILE_STORAGE_TYPE == FileStorageType.S3:
        container.register_singleton(FileStorageInterface, S3FileStorage)
    
    # Repositorios
    container.register_singleton(PlayerRepositoryInterface, PlayerRepository)
    container.register_singleton(VideoRepositoryInterface, VideoRepository)
```

### Uso en Routers
```python
# app/routers/auth.py
def get_player_service() -> PlayerService:
    return container.get_player_service()

@router.post("/signup", response_model=PlayerResponseDTO)
async def signup(
    player_data: PlayerCreateDTO,
    player_service: PlayerService = Depends(get_player_service)
):
    # Lógica del endpoint...
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


## 📚 Referencias

- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Dependency Injection](https://martinfowler.com/articles/injection.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
