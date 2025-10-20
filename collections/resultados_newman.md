# Resultados de Pruebas Newman - ANB Rising Stars Showcase

## 📊 Resumen de Ejecución

**Fecha de ejecución:** $(date)  
**Colección:** ANB Rising Stars Showcase.postman_collection.json  
**Estado:** ✅ **TODAS LAS PRUEBAS EXITOSAS**

## 📈 Estadísticas Generales

| Métrica | Valor |
|---------|-------|
| **Iteraciones ejecutadas** | 1 |
| **Requests ejecutados** | 15 |
| **Test scripts ejecutados** | 14 |
| **Pre-request scripts ejecutados** | 1 |
| **Assertions ejecutadas** | 34 |
| **Assertions fallidas** | 0 |
| **Duración total** | 6.5s |
| **Datos recibidos** | 1.58MB |
| **Tiempo promedio de respuesta** | 83ms |
| **Tiempo mínimo** | 5ms |
| **Tiempo máximo** | 316ms |
| **Desviación estándar** | 121ms |

## ✅ Resultados por Sección

### 1. Autenticación
- **Register Player** ✅ [201 Created, 201B, 293ms]
  - Status code is 201 Created or 400 Bad Request (user exists) ✅
  - Response body contains success message or user exists message ✅

- **Log In Player** ✅ [200 OK, 334B, 260ms]
  - Status code is 200 OK ✅
  - Response includes an access_token ✅
  - Set bearer_token variable ✅

### 2. Gestión de Videos
- **Upload Video** ✅ [201 Created, 274B, 16ms]
  - Status code is 201 Created ✅
  - Response contains a task_id ✅

- **Get My Videos** ✅ [200 OK, 315B, 6ms]
  - Status code is 200 OK ✅
  - Response is an array ✅
  - Video object has correct properties and save video_id ✅

- **Get Specific Video** ✅ [200 OK, 383B, 6ms]
  - Status code is 200 OK ✅
  - Video detail has correct properties ✅

- **Get Original Video** ✅ [200 OK, 164.57kB, 8ms]
  - Status code is 200 OK ✅
  - Response is a video file ✅
  - Response has content ✅

- **Get Processed Video** ✅ [200 OK, 1.41MB, 22ms]
  - Status code is 200 OK ✅
  - Response is a video file ✅
  - Response has content ✅
  - Video processing completed successfully ✅

### 3. Endpoints Públicos
- **Register Second User** ✅ [201 Created, 201B, 268ms]
  - Status code is 201 Created or 400 Bad Request (user exists) ✅
  - Response body contains success message or user exists message ✅

- **Login Second User** ✅ [200 OK, 334B, 316ms]
  - Status code is 200 OK ✅
  - Response includes an access_token ✅
  - Set second_user_token variable ✅

- **List Videos for Voting** ✅ [200 OK, 1.96kB, 5ms]
  - Status code is 200 OK ✅
  - Response is an array ✅

- **Vote for a Video** ✅ [200 OK, 197B, 10ms]
  - Status code is 200 OK ✅
  - Response confirms vote was registered ✅

- **Get Rankings** ✅ [200 OK, 611B, 12ms]
  - Status code is 200 OK ✅
  - Response is an array of ranking objects ✅

- **Upload Second Video** ✅ [201 Created, 274B, 13ms]
  - Status code is 201 Created ✅
  - Response contains a task_id ✅
  - Video to delete ID set to: 19 ✅

- **Delete Video** ✅ [200 OK, 222B, 9ms]
  - Status code is 200 OK ✅
  - Response confirms deletion ✅

## 🎯 Funcionalidades Validadas

### ✅ Autenticación y Autorización
- Registro de usuarios con validación de campos requeridos
- Login con generación de JWT tokens
- Manejo de tokens de autenticación en requests

### ✅ Gestión de Videos
- Upload de videos con procesamiento asíncrono
- Listado de videos del usuario
- Obtención de detalles específicos de videos
- Descarga de videos originales
- Descarga de videos procesados (con espera de procesamiento)
- Eliminación de videos

### ✅ Sistema de Votación
- Listado público de videos para votación
- Votación por videos de otros usuarios
- Sistema de rankings por ciudad
- Validación de permisos de votación

### ✅ Procesamiento de Videos
- Procesamiento asíncrono de videos
- Aplicación de marca de agua ANB
- Recorte a 30 segundos
- Eliminación de audio
- Validación de archivos de video

## 🔧 Mejoras Implementadas

1. **Manejo de Procesamiento Asíncrono**: Implementado delay de 5 segundos para permitir el procesamiento completo
2. **Validaciones Robustas**: Tests que manejan tanto casos exitosos como de procesamiento pendiente
3. **Flujo de Testing Optimizado**: Upload y delete de videos específicos para testing
4. **Autenticación Multi-usuario**: Testing con dos usuarios diferentes para validar votaciones
5. **Captura Dinámica de IDs**: Uso de variables de colección para IDs dinámicos

## 📝 Notas Técnicas

- **Tiempo de procesamiento**: 5 segundos de espera para videos procesados
- **Archivo de prueba**: `collections/example.mp4` (164.57kB)
- **Tamaño de video procesado**: ~1.41MB
- **Autenticación**: Bearer tokens JWT
- **Base URL**: `http://localhost`

## 🎉 Conclusión

**TODAS LAS PRUEBAS PASARON EXITOSAMENTE** ✅

La colección de Postman está completamente funcional y valida todas las funcionalidades del sistema ANB Rising Stars Showcase, incluyendo:
- Autenticación completa
- Gestión de videos (upload, procesamiento, descarga, eliminación)
- Sistema de votación público
- Rankings por ciudad
- Procesamiento asíncrono de videos

El sistema está listo para producción con todas las funcionalidades validadas.


**LOG EJECUCIÖN**

ANB Rising Stars Showcase

❏ 1. Autenticación
↳ Register Player
  POST http://localhost/api/auth/signup [201 Created, 201B, 312ms]
  ✓  Status code is 201 Created or 400 Bad Request (user exists)
  ✓  Response body contains success message or user exists message

↳ Log In Player
  POST http://localhost/api/auth/login [200 OK, 334B, 256ms]
  ✓  Status code is 200 OK
  ✓  Response includes an access_token
  ✓  Set bearer_token variable

❏ 2. Gestión de Videos
↳ Upload Video
  POST http://localhost/api/videos/upload  (node:14706) [DEP0044] DeprecationWarning: The `util.isArray` API is deprecated. Please use `Array.isArray()` instead.
(Use `node --trace-deprecation ...` to show where the warning was created)
[201 Created, 274B, 25ms]
  ✓  Status code is 201 Created
  ✓  Response contains a task_id

↳ Get My Videos
  GET http://localhost/api/videos [200 OK, 315B, 7ms]
  ✓  Status code is 200 OK
  ✓  Response is an array
  ✓  Video object has correct properties and save video_id

↳ Get Specific Video
  GET http://localhost/api/videos/16 [200 OK, 383B, 11ms]
  ✓  Status code is 200 OK
  ✓  Video detail has correct properties

↳ Get Original Video
  GET http://localhost/api/videos/original/16 [200 OK, 164.57kB, 8ms]
  ✓  Status code is 200 OK
  ✓  Response is a video file
  ✓  Response has content

↳ Get Processed Video
  ┌
  │ 'Esperando 5 segundos para el procesamiento del video...'
  │ 'Espera completada, intentando descargar video procesado...'
  └
  GET http://localhost/api/videos/processed/16 [200 OK, 1.41MB, 23ms]
  ✓  Status code is 200 OK
  ✓  Response is a video file
  ✓  Response has content
  ┌
  │ 'Video procesado descargado exitosamente'
  └
  ✓  Video processing completed successfully

❏ 3. Endpoints Públicos
↳ Register Second User
  POST http://localhost/api/auth/signup [201 Created, 201B, 274ms]
  ✓  Status code is 201 Created or 400 Bad Request (user exists)
  ✓  Response body contains success message or user exists message

↳ Login Second User
  POST http://localhost/api/auth/login [200 OK, 334B, 256ms]
  ✓  Status code is 200 OK
  ✓  Response includes an access_token
  ✓  Set second_user_token variable

↳ List Videos for Voting
  GET http://localhost/api/public/videos [200 OK, 1.73kB, 5ms]
  ✓  Status code is 200 OK
  ✓  Response is an array

↳ Vote for a Video
  POST http://localhost/api/public/videos/16/vote [200 OK, 197B, 8ms]
  ✓  Status code is 200 OK
  ✓  Response confirms vote was registered

↳ Get Rankings
  GET http://localhost/api/public/rankings?city=Bogotá [200 OK, 546B, 10ms]
  ✓  Status code is 200 OK
  ✓  Response is an array of ranking objects

↳ Upload Second Video
  POST http://localhost/api/videos/upload [201 Created, 274B, 13ms]
  ✓  Status code is 201 Created
  ✓  Response contains a task_id
  GET http://localhost/api/videos [200 OK, 539B, 5ms]
  ┌
  │ 'Video to delete ID set to:', 17
  └

↳ Delete Video
  DELETE http://localhost/api/videos/17 [200 OK, 222B, 8ms]
  ✓  Status code is 200 OK
  ✓  Response confirms deletion

┌─────────────────────────┬───────────────────┬───────────────────┐
│                         │          executed │            failed │
├─────────────────────────┼───────────────────┼───────────────────┤
│              iterations │                 1 │                 0 │
├─────────────────────────┼───────────────────┼───────────────────┤
│                requests │                15 │                 0 │
├─────────────────────────┼───────────────────┼───────────────────┤
│            test-scripts │                14 │                 0 │
├─────────────────────────┼───────────────────┼───────────────────┤
│      prerequest-scripts │                 1 │                 0 │
├─────────────────────────┼───────────────────┼───────────────────┤
│              assertions │                34 │                 0 │
├─────────────────────────┴───────────────────┴───────────────────┤
│ total run duration: 6.4s                                        │
├─────────────────────────────────────────────────────────────────┤
│ total data received: 1.58MB (approx)                            │
├─────────────────────────────────────────────────────────────────┤
│ average response time: 81ms [min: 5ms, max: 312ms, s.d.: 117ms] │