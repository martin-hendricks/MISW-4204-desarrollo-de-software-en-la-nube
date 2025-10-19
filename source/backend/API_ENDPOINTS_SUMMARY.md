# Resumen de Endpoints - ANB Rising Stars Showcase API

Este documento resume todos los endpoints de la API y sus respuestas según la colección de Postman.

## ✅ Estado de Implementación

### 1. Autenticación

#### POST `/auth/signup`
**Estado:** ✅ Implementado correctamente

**Request Body:**
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "password1": "StrongPass123",
    "password2": "StrongPass123",
    "city": "Bogotá",
    "country": "Colombia"
}
```

**Response (201 Created):**
```json
{
    "message": "Usuario creado exitosamente."
}
```

**Códigos de respuesta:**
- `201 Created`: Usuario creado exitosamente
- `400 Bad Request`: Error de validación (email duplicado, contraseñas no coinciden)

---

#### POST `/auth/login`
**Estado:** ✅ Implementado correctamente

**Request Body:**
```json
{
    "email": "john.doe@example.com",
    "password": "StrongPass123"
}
```

**Response (200 OK):**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
}
```

**Códigos de respuesta:**
- `200 OK`: Autenticación exitosa, retorna el token
- `401 Unauthorized`: Credenciales inválidas

---

#### GET `/auth/me`
**Estado:** ✅ Implementado correctamente
**Autenticación:** Requerida (Bearer Token)

**Response (200 OK):**
```json
{
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "city": "Bogotá",
    "country": "Colombia",
    "username": "john.doe",
    "is_active": true,
    "created_at": "2025-01-15T10:30:00Z"
}
```

**Códigos de respuesta:**
- `200 OK`: Información del usuario obtenida
- `401 Unauthorized`: Token inválido o expirado
- `404 Not Found`: Usuario no encontrado

---

### 2. Gestión de Videos

#### POST `/videos/upload`
**Estado:** ✅ Implementado correctamente
**Autenticación:** Requerida (Bearer Token)

**Request Body (form-data):**
- `video_file`: archivo MP4 (máximo 100MB)
- `title`: string

**Response (202 Accepted):**
```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Video subido correctamente. Procesamiento en curso."
}
```

**Códigos de respuesta:**
- `202 Accepted`: Video subido exitosamente, tarea de procesamiento creada
- `400 Bad Request`: Error en el archivo (tipo o tamaño inválido)
- `401 Unauthorized`: Falta de autenticación

---

#### GET `/videos`
**Estado:** ✅ Implementado correctamente
**Autenticación:** Requerida (Bearer Token)

**Response (200 OK):**
```json
[
    {
        "video_id": 123,
        "title": "Mi mejor jugada de 3 puntos",
        "status": "processed",
        "uploaded_at": "2025-03-10T14:30:00Z",
        "processed_at": "2025-03-10T14:35:00Z",
        "processed_url": "uploads/processed/123.mp4"
    },
    {
        "video_id": 456,
        "title": "Habilidades de dribleo",
        "status": "uploaded",
        "uploaded_at": "2025-03-11T10:15:00Z",
        "processed_at": null,
        "processed_url": null
    }
]
```

**Propiedades verificadas:**
- ✅ `video_id`
- ✅ `title`
- ✅ `status`
- ✅ `uploaded_at`
- ✅ `processed_at`
- ✅ `processed_url`

**Códigos de respuesta:**
- `200 OK`: Lista de videos obtenida
- `401 Unauthorized`: Falta de autenticación

---

#### GET `/videos/{video_id}`
**Estado:** ✅ Implementado correctamente
**Autenticación:** Requerida (Bearer Token)

**Response (200 OK):**
```json
{
    "video_id": 123,
    "title": "Mi mejor jugada de 3 puntos",
    "status": "processed",
    "votes": 42,
    "original_url": "uploads/original/123.mp4",
    "processed_url": "uploads/processed/123.mp4",
    "uploaded_at": "2025-03-10T14:30:00Z",
    "processed_at": "2025-03-10T14:35:00Z"
}
```

**Propiedades verificadas:**
- ✅ `video_id`
- ✅ `title`
- ✅ `status`
- ✅ `votes`
- ✅ `original_url`
- ✅ `processed_url`
- ✅ `uploaded_at`
- ✅ `processed_at`

**Códigos de respuesta:**
- `200 OK`: Detalle del video obtenido
- `401 Unauthorized`: Usuario no autenticado
- `403 Forbidden`: El usuario no es el propietario del video
- `404 Not Found`: El video no existe

---

#### DELETE `/videos/{video_id}`
**Estado:** ✅ Implementado correctamente
**Autenticación:** Requerida (Bearer Token)

**Response (200 OK):**
```json
{
    "message": "El video ha sido eliminado exitosamente."
}
```

**Códigos de respuesta:**
- `200 OK`: Video eliminado correctamente
- `400 Bad Request`: El video no puede ser eliminado porque no cumple las condiciones
- `401 Unauthorized`: Usuario no autenticado
- `403 Forbidden`: El usuario no es el propietario
- `404 Not Found`: El video no existe

---

### 3. Endpoints Públicos

#### GET `/public/videos`
**Estado:** ✅ Implementado correctamente
**Autenticación:** No requerida

**Response (200 OK):**
```json
[
    {
        "video_id": 123,
        "title": "Mi mejor jugada de 3 puntos",
        "status": "processed",
        "uploaded_at": "2025-03-10T14:30:00Z",
        "processed_at": "2025-03-10T14:35:00Z",
        "processed_url": "uploads/processed/123.mp4"
    }
]
```

**Nota:** Solo retorna videos en estado `processed`.

**Códigos de respuesta:**
- `200 OK`: Lista de videos públicos obtenida

---

#### POST `/public/videos/{video_id}/vote`
**Estado:** ✅ Implementado correctamente
**Autenticación:** Requerida (Bearer Token)

**Response (200 OK):**
```json
{
    "message": "Voto registrado exitosamente."
}
```

**Códigos de respuesta:**
- `200 OK`: Voto registrado exitosamente
- `400 Bad Request`: Ya has votado por este video / No puedes votar por tu propio video
- `401 Unauthorized`: Falta de autenticación
- `404 Not Found`: Video no encontrado

---

#### GET `/public/rankings?city=Bogotá`
**Estado:** ✅ Implementado correctamente
**Autenticación:** No requerida

**Query Parameters:**
- `city` (opcional): Filtrar ranking por ciudad

**Response (200 OK):**
```json
[
    {
        "player_id": 1,
        "username": "john.doe",
        "city": "Bogotá",
        "votes": 150
    },
    {
        "player_id": 2,
        "username": "jane.doe",
        "city": "Bogotá",
        "votes": 120
    }
]
```

**Propiedades verificadas:**
- ✅ `player_id`
- ✅ `username`
- ✅ `city`
- ✅ `votes`

**Códigos de respuesta:**
- `200 OK`: Lista de rankings obtenida
- `400 Bad Request`: Parámetro inválido en la consulta

---

## 📋 Checklist de Validación

### Autenticación
- [x] Signup retorna mensaje correcto
- [x] Login retorna access_token
- [x] JWT funcional

### Gestión de Videos
- [x] Upload retorna task_id
- [x] Get My Videos retorna array con propiedades correctas
- [x] Get Specific Video retorna objeto con todas las propiedades
- [x] Delete retorna mensaje de confirmación
- [x] Códigos de error correctos (400, 401, 403, 404)

### Endpoints Públicos
- [x] List Videos retorna array de videos procesados
- [x] Vote retorna mensaje de confirmación
- [x] Rankings retorna array con estructura correcta
- [x] Rankings soporta filtro por ciudad

---

### 4. Endpoints del Sistema

#### GET `/`
**Estado:** ✅ Implementado correctamente
**Autenticación:** No requerida

**Response (200 OK):**
```json
{
    "message": "ANB Rising Stars Showcase API",
    "version": "1.0.0",
    "architecture": "DDD + Clean Architecture",
    "docs": "/docs",
    "file_storage": "local"
}
```

---

#### GET `/health`
**Estado:** ✅ Implementado correctamente
**Autenticación:** No requerida

**Response (200 OK):**
```json
{
    "status": "healthy",
    "service": "backend",
    "architecture": "DDD",
    "file_storage": "local"
}
```

---

#### GET `/config`
**Estado:** ✅ Implementado correctamente
**Autenticación:** No requerida

**Response (200 OK):**
```json
{
    "file_storage_type": "local",
    "database_url": "localhost:5432/anb_rising_stars",
    "redis_url": "localhost:6379/0"
}
```

---

## 🚀 Base URL

- **Desarrollo:** `http://localhost:8000`
- **Producción:** TBD

---

## 🔑 Autenticación

Los endpoints que requieren autenticación esperan un token JWT en el header:

```
Authorization: Bearer <token>
```

El token se obtiene del endpoint `/auth/login` y debe incluirse en todas las peticiones protegidas.

---

## 📊 Estados de Video

- `uploaded`: Video subido, pendiente de procesamiento
- `processed`: Video procesado y disponible para votación

---

## 🧪 Estado de Testing

- ✅ **37/37 tests pasando** (100% de éxito)
- ✅ Tests de autenticación (7/7)
- ✅ Tests de videos (10/10)
- ✅ Tests públicos (10/10)
- ✅ Tests básicos (5/5)
- ✅ Tests simples (5/5)

---

## ✅ Conclusión

Todos los endpoints están **implementados y alineados** con las especificaciones actuales. La API está completamente funcional y lista para uso en desarrollo y testing.

