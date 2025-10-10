# MISW-4204-desarrollo-de-software-en-la-nube

## Docker Compose

Este repositorio incluye un archivo `docker-compose.yml` que proporciona una infraestructura completa para el desarrollo de aplicaciones en la nube.

### Servicios incluidos

- **web**: Servidor web Nginx para servir contenido estático
- **app**: Servicio de backend con Python
- **db**: Base de datos PostgreSQL
- **cache**: Cache Redis
- **mongodb**: Base de datos NoSQL MongoDB

### Uso

#### Iniciar todos los servicios

```bash
docker compose up -d
```

#### Detener todos los servicios

```bash
docker compose down
```

#### Ver logs de los servicios

```bash
docker compose logs -f
```

#### Ver el estado de los servicios

```bash
docker compose ps
```

#### Iniciar servicios específicos

```bash
docker compose up -d db cache
```

#### Eliminar todos los contenedores y volúmenes

```bash
docker compose down -v
```

### Configuración

Los servicios están configurados con las siguientes credenciales por defecto:

- **PostgreSQL**:
  - Usuario: `postgres`
  - Contraseña: `postgres`
  - Base de datos: `appdb`
  - Puerto: `5432`

- **MongoDB**:
  - Usuario: `admin`
  - Contraseña: `admin`
  - Puerto: `27017`

- **Redis**:
  - Puerto: `6379`

- **Nginx**:
  - Puerto: `80`

- **Backend App**:
  - Puerto: `8000`

### Estructura de directorios

Para utilizar los servicios web y app, crea los siguientes directorios:

```bash
mkdir -p web app
```

- `web/`: Coloca aquí los archivos HTML, CSS, JS para el servidor Nginx
- `app/`: Coloca aquí el código de tu aplicación backend

### Red

Todos los servicios están conectados a través de la red `app-network`, permitiendo la comunicación entre ellos usando sus nombres de servicio como hostnames.

### Volúmenes persistentes

Los siguientes volúmenes se crean para persistir datos:

- `postgres-data`: Datos de PostgreSQL
- `redis-data`: Datos de Redis
- `mongodb-data`: Datos de MongoDB