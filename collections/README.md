# Coleccion de Postman - ANB Rising Stars Showcase

Este directorio contiene la coleccion de Postman con todos los endpoints de la API de ANB Rising Stars Showcase documentados y listos para probar.

## Archivos Incluidos

- `ANB Rising Stars Showcase.postman_collection.json` - Coleccion completa de endpoints de la API

## Como Importar la Coleccion en Postman

### Opcion 1: Importar desde Archivo Local

1. **Abrir Postman**
   - Inicia la aplicacion de Postman en tu computadora
   - Si no tienes Postman instalado, descargalo desde: https://www.postman.com/downloads/

2. **Importar la Coleccion**
   - Haz clic en el boton **"Import"** en la esquina superior izquierda
   - Se abrira una ventana de dialogo

3. **Seleccionar el Archivo**
   - Arrastra y suelta el archivo `ANB Rising Stars Showcase.postman_collection.json` en la ventana
   - O haz clic en **"Upload Files"** y navega hasta este directorio para seleccionar el archivo

4. **Confirmar la Importacion**
   - Postman mostrara un preview de la coleccion
   - Haz clic en **"Import"** para confirmar

5. **Verificar**
   - La coleccion aparecera en el panel izquierdo de Postman bajo "Collections"
   - Expande la coleccion para ver todos los endpoints disponibles

### Opcion 2: Importar desde GitHub (si el repositorio es publico)

1. **Abrir Postman**
   - Inicia la aplicacion de Postman

2. **Importar desde Link**
   - Haz clic en el boton **"Import"**
   - Selecciona la pestana **"Link"**

3. **Pegar la URL**
   - Pega la URL raw del archivo JSON desde GitHub
   - Ejemplo: `https://raw.githubusercontent.com/[usuario]/[repo]/[branch]/collections/ANB%20Rising%20Stars%20Showcase.postman_collection.json`

4. **Importar**
   - Haz clic en **"Continue"** y luego en **"Import"**

## Configuracion de Variables de Entorno

Antes de usar la coleccion, configura las variables de entorno necesarias:

1. **Crear un Entorno**
   - En Postman, haz clic en **"Environments"** en el panel izquierdo
   - Haz clic en **"+"** para crear un nuevo entorno
   - Nombra el entorno como "ANB Local" o "ANB Dev"

2. **Configurar Variables**
   - Agrega las siguientes variables:

   | Variable | Valor Inicial | Descripcion |
   |----------|--------------|-------------|
   | `base_url` | `http://localhost/api` | URL base de la API |
   | `token` | (vacio) | Se auto-completa despues del login |

3. **Guardar el Entorno**
   - Haz clic en **"Save"**

4. **Activar el Entorno**
   - Selecciona el entorno "ANB Local" en el dropdown de la esquina superior derecha

## Como Usar la Coleccion

### 1. Registro de Usuario

- Abre el request **"Register Player"**
- Modifica el body JSON con los datos del nuevo jugador
- Haz clic en **"Send"**
- Deberas recibir un response con status 201 y los datos del jugador creado

### 2. Login (Autenticacion)

- Abre el request **"Login"**
- Modifica el body con el email y password del jugador registrado
- Haz clic en **"Send"**
- El token JWT se guardara automaticamente en la variable de entorno `token`

### 3. Usar Endpoints Protegidos

- Los requests que requieren autenticacion ya tienen configurado el header `Authorization` con el token
- Simplemente selecciona el request que deseas probar y haz clic en **"Send"**
- El token se incluira automaticamente desde la variable de entorno

### 4. Subir Videos

- Abre el request **"Upload Video"**
- En la pestana **"Body"**, selecciona **"form-data"**
- Para el campo `file`, haz clic en el dropdown y selecciona **"File"**
- Haz clic en **"Select Files"** y elige un archivo de video de tu computadora
- Completa los demas campos requeridos
- Haz clic en **"Send"**

## Estructura de la Coleccion

La coleccion esta organizada en las siguientes carpetas:

### Auth (Autenticacion)
- `POST /auth/register` - Registrar nuevo jugador
- `POST /auth/login` - Iniciar sesion

### Videos
- `POST /videos/upload` - Subir un video
- `GET /videos` - Listar todos los videos
- `GET /videos/{id}` - Obtener detalles de un video
- `GET /videos/processed/{video_id}` - Descargar video procesado
- `GET /videos/original/{video_id}` - Descargar video original
- `PATCH /videos/{id}` - Actualizar informacion de un video
- `DELETE /videos/{id}` - Eliminar un video

### Votacion
- `POST /videos/{id}/vote` - Votar por un video
- `GET /videos/{id}/votes` - Obtener votos de un video

### Public (Endpoints Publicos)
- `GET /public/videos` - Listar videos procesados (sin autenticacion)
- `GET /public/ranking` - Obtener ranking de jugadores
