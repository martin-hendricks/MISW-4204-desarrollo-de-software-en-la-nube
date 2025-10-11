# Servicio de Autenticación - FastAPI

Microservicio independiente de autenticación implementado con FastAPI que maneja registro, login, verificación de tokens JWT y gestión de usuarios.

## Especificación del API REST

El servicio implementa los siguientes endpoints según la especificación oficial:

| Endpoint | Método | Descripción | Autenticación | Notas |
|----------|--------|-------------|---------------|-------|
| `/api/auth/signup` | POST | Registro de nuevos usuarios en la plataforma | No | Valida email único y confirmación de contraseña |
| `/api/auth/login` | POST | Autenticación de usuarios y generación de token JWT | No | Devuelve token JWT válido para autenticación posterior |

## Características

- 🔐 Autenticación JWT con tokens seguros
- 👤 Registro y gestión de usuarios
- 🔒 Verificación de tokens para otros servicios
- 🚀 API RESTful con FastAPI
- 🐳 Contenedorizado con Docker
- 📚 Documentación automática con Swagger/OpenAPI

## Estructura del Proyecto

```
auth-service/
├── main.py                 # Aplicación principal FastAPI
├── requirements.txt        # Dependencias Python
├── Dockerfile             # Imagen Docker
├── models/
│   ├── __init__.py
│   └── user.py            # Modelos Pydantic para usuarios
├── routers/
│   ├── __init__.py
│   ├── auth.py            # Endpoints de autenticación
│   └── users.py           # Endpoints de usuarios
├── services/
│   ├── __init__.py
│   ├── auth_service.py    # Lógica de negocio de auth
│   └── jwt_service.py     # Manejo de tokens JWT
└── middleware/
    ├── __init__.py
    └── auth_middleware.py  # Middleware de autenticación
```

## Endpoints Disponibles

### Autenticación
- `POST /auth/register` - Registrar nuevo usuario
- `POST /auth/login` - Iniciar sesión
- `POST /auth/verify-token` - Verificar token JWT
- `POST /auth/refresh-token` - Renovar token JWT

### Usuarios
- `GET /users/me` - Obtener perfil del usuario actual
- `GET /users/{user_id}` - Obtener usuario por ID

### Sistema
- `GET /` - Información del servicio
- `GET /health` - Health check

## Uso

### 1. Registro de Usuario (Signup)

```bash
curl -X POST "http://localhost:8001/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "password1": "StrongPass123",
    "password2": "StrongPass123",
    "city": "Bogotá",
    "country": "Colombia"
  }'
```

Respuesta (HTTP 201):
```json
{
  "id": 1,
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "city": "Bogotá",
  "country": "Colombia",
  "is_active": true,
  "created_at": "2025-10-11T15:30:00.123456",
  "updated_at": null
}
```

### Códigos de Respuesta para Registro:
- **201**: Usuario creado exitosamente
- **400**: Error de validación (email duplicado, contraseñas no coinciden)

### 2. Iniciar Sesión (Login)

```bash
curl -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "StrongPass123"
  }'
```

Respuesta exitosa (HTTP 200):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Códigos de Respuesta para Login:
- **200**: Autenticación exitosa, retorna token JWT
- **401**: Credenciales incorrectas (email no existe o contraseña incorrecta)

### 3. Usar Token en Requests Autenticadas

Una vez obtenido el token JWT, debe incluirse en todas las solicitudes autenticadas:

```bash
curl -X GET "http://localhost:8001/api/users/me" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGci..."
```

### 4. Control de Sesiones JWT

El sistema implementa control de sesiones basado en tokens JWT con:

- **Expiración automática**: Los tokens expiran en 3600 segundos (1 hora)
- **Verificación de firma**: Cada token es validado criptográficamente
- **Información de usuario**: El token contiene email y user_id del usuario
- **Renovación**: Usar endpoint `/auth/refresh-token` para renovar tokens

#### Verificar Token:
```bash
curl -X POST "http://localhost:8001/api/auth/verify-token" \
  -H "Authorization: Bearer your-jwt-token"
```

#### Renovar Token:
```bash
curl -X POST "http://localhost:8001/api/auth/refresh-token" \
  -H "Authorization: Bearer your-current-token"
```

## Integración con Backend Principal

El backend principal puede verificar tokens usando:

```python
from auth_middleware import auth_middleware
from fastapi import Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/protected-endpoint")
async def protected_route(
    current_user: dict = Depends(
        lambda creds=Depends(security): auth_middleware.get_current_user(creds)
    )
):
    return {"message": "Acceso autorizado", "user": current_user}
```

## Variables de Entorno

- `JWT_SECRET_KEY`: Clave secreta para JWT (CAMBIAR EN PRODUCCIÓN)
- `DATABASE_URL`: URL de conexión a PostgreSQL
- `PORT`: Puerto del servicio (default: 8001)

## Ejecución Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servicio
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Scripts de Prueba

El servicio incluye varios scripts para validar la funcionalidad:

```bash
# Flujo completo de registro y login
python test_auth.py

# Validaciones de errores (contraseñas no coincidentes, email duplicado)
python test_validation_errors.py

# Pruebas específicas del sistema de login
python test_login.py
```

## Ejecución con Docker

```bash
# Construir imagen
docker build -t auth-service .

# Ejecutar contenedor
docker run -p 8001:8001 -e JWT_SECRET_KEY=mi-clave-secreta auth-service
```

## Documentación API

Una vez ejecutando el servicio, la documentación interactiva está disponible en:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Seguridad

- Contraseñas hasheadas con bcrypt
- Tokens JWT con expiración configurable
- Validación de datos con Pydantic
- CORS configurado apropiadamente

## Próximas Mejoras

- [ ] Integración con base de datos PostgreSQL real
- [ ] Refresh tokens con rotación
- [ ] Rate limiting para endpoints
- [ ] Roles y permisos de usuario
- [ ] Autenticación OAuth2 (Google, GitHub)
- [ ] Logs estructurados
- [ ] Métricas de Prometheus