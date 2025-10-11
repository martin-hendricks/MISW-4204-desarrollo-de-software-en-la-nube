# ANB Rising Stars Showcase API

API REST para la plataforma ANB Rising Stars Showcase - Gestión de videos de habilidades de baloncesto.

## 🏀 Descripción

Esta API permite a los jugadores de baloncesto:
- Registrarse y autenticarse en la plataforma
- Subir videos de sus mejores jugadas
- Votar por videos de otros jugadores
- Ver rankings dinámicos por ciudad

## 🚀 Tecnologías

- **FastAPI** - Framework web moderno y rápido
- **PostgreSQL** - Base de datos relacional
- **SQLAlchemy** - ORM para Python
- **Celery** - Procesamiento asíncrono de tareas
- **Redis** - Broker de mensajes para Celery
- **JWT** - Autenticación basada en tokens
- **Pydantic** - Validación de datos
- **Alembic** - Migraciones de base de datos

## 📁 Estructura del Proyecto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Aplicación principal FastAPI
│   ├── auth.py                 # Lógica de autenticación JWT
│   ├── file_storage.py         # Gestión de archivos locales
│   ├── celery_app.py           # Configuración de Celery
│   ├── tasks.py                # Tareas asíncronas
│   ├── crud.py                 # Operaciones CRUD
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py         # Configuración de base de datos
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py           # Modelos SQLAlchemy
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py          # Esquemas Pydantic
│   └── routers/
│       ├── __init__.py
│       ├── auth.py             # Endpoints de autenticación
│       ├── videos.py           # Endpoints de gestión de videos
│       └── public.py           # Endpoints públicos (votación, rankings)
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Configuración de pruebas
│   ├── test_auth.py
│   ├── test_videos.py
│   └── test_public.py
├── uploads/                    # Carpeta para archivos subidos
├── alembic/                    # Migraciones de base de datos
├── requirements.txt
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
   export DATABASE_URL="postgresql://postgres:password@localhost:5432/anb_rising_stars"
   export REDIS_URL="redis://localhost:6379/0"
   export SECRET_KEY="your-secret-key-here"
   ```

5. **Configurar base de datos**
   ```bash
   # Crear base de datos PostgreSQL
   createdb anb_rising_stars
   
   # Ejecutar migraciones
   alembic upgrade head
   ```

6. **Ejecutar la aplicación**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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

### Gestión de Videos
- `POST /api/videos/upload` - Subida de videos
- `GET /api/videos/` - Listar videos del usuario
- `GET /api/videos/{video_id}` - Obtener video específico
- `DELETE /api/videos/{video_id}` - Eliminar video

### Endpoints Públicos
- `GET /api/public/videos` - Listar videos para votación
- `POST /api/public/videos/{video_id}/vote` - Votar por video
- `GET /api/public/rankings` - Obtener rankings

## 🔄 Procesamiento Asíncrono

Para el procesamiento de videos, ejecuta el worker de Celery:

```bash
celery -A app.celery_app worker --loglevel=info
```

## 🐳 Docker

```bash
# Construir imagen
docker build -t anb-rising-stars-api .

# Ejecutar contenedor
docker run -p 8000:8000 anb-rising-stars-api
```

## 📝 Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `DATABASE_URL` | URL de conexión a PostgreSQL | `postgresql://postgres:password@localhost:5432/anb_rising_stars` |
| `REDIS_URL` | URL de conexión a Redis | `redis://localhost:6379/0` |
| `SECRET_KEY` | Clave secreta para JWT | `your-secret-key-here` |

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.
