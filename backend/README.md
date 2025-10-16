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
│   │   ├── value_objects/      # Objetos de valor
│   │   └── repositories/       # Interfaces de repositorios
│   ├── application/            # 🔧 Capa de Aplicación
│   │   ├── services/           # Servicios de aplicación
│   │   └── dtos/               # Data Transfer Objects
│   ├── infrastructure/         # 🔌 Capa de Infraestructura
│   │   ├── database/           # Configuración de BD
│   │   ├── external_services/  # Servicios externos
│   │   └── repositories/       # Implementaciones de repositorios
│   ├── shared/                 # 🔄 Capa Compartida
│   │   ├── interfaces/         # Interfaces compartidas
│   │   ├── exceptions/         # Excepciones del dominio
│   │   └── container.py        # Contenedor de dependencias
│   ├── config/                 # ⚙️ Configuración
│   │   ├── settings.py         # Configuración de la aplicación
│   │   └── container_config.py # Configuración del contenedor
│   ├── routers/                # 🌐 Capa de Presentación
│   │   ├── __init__.py
│   │   └── auth.py             # Endpoints de autenticación
│   └── db/                     # Base de datos
│       └── database.py         # Configuración de BD
├── tests/                      # Pruebas
├── uploads/                    # Archivos subidos (local)
├── alembic/                    # Migraciones de BD
├── requirements.txt
├── start.py                    # Script de inicio
├── migrate.py                  # Script de migraciones
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
pytest

# Ejecutar pruebas con cobertura
pytest --cov=app

# Ejecutar pruebas específicas
pytest tests/test_auth.py
```

## 📚 Documentación de la API

Una vez que la aplicación esté ejecutándose, puedes acceder a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔌 Endpoints Principales

### Autenticación
- `POST /api/auth/signup` - Registro de jugadores
- `POST /api/auth/login` - Inicio de sesión
- `GET /api/auth/me` - Información del usuario actual
- `PUT /api/auth/profile` - Actualizar perfil

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

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 📚 Documentación Adicional

- [Arquitectura DDD](ARCHITECTURE.md) - Explicación detallada de la arquitectura
- [Patrones de Diseño](docs/design-patterns.md) - Patrones implementados
- [Guía de Testing](docs/testing-guide.md) - Cómo hacer testing