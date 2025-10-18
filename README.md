# ANB Rising Stars Showcase

## Integrantes del Grupo

| Nombre | Correo |
|--------|--------|
| Angel Tejedor | a.tejedor@uniandes.edu.co |
| Mauricio Rodriguez | am.rodriguezs1@uniandes.edu.co |
| Juan Acevedo | jc.acevedoo1@uniandes.edu.co |
| Martin Romero | mr.romero@uniandes.edu.co |

## Descripción del Aplicativo

**ANB Rising Stars Showcase** es una plataforma web desarrollada para la Asociación Nacional de Baloncesto (ANB) que permite democratizar el proceso de selección de nuevos talentos en el baloncesto. La aplicación facilita que jóvenes atletas de diferentes regiones del país puedan participar en un proceso de preselección enviando videos que demuestran sus habilidades, sin barreras geográficas o económicas.

### Propósito

La plataforma sirve como centro de carga, almacenamiento y evaluación de videos de jugadores aficionados que aspiran a ser parte del torneo de exhibición **Rising Stars Showcase** frente a cazatalentos de la liga profesional. Los jugadores con mayor número de votos en cada ciudad serán seleccionados para integrar los equipos participantes, con la posibilidad de ser reclutados por equipos profesionales.

### Funcionalidades Principales

- **Registro y Gestión de Jugadores**: Los jugadores pueden registrarse, crear su perfil y subir videos de prueba mostrando sus habilidades (entrenamientos, jugadas destacadas, lanzamientos, etc.).

- **Procesamiento Automático de Videos**: La plataforma procesa automáticamente los videos cargados para:
  - Recortar la duración a un máximo de 30 segundos
  - Ajustar resolución y formato de aspecto para calidad óptima
  - Agregar marca de agua de ANB para autenticar el contenido
  - Eliminar audio (no relevante para la evaluación)

- **Sistema de Votación**: El público puede visualizar los videos y votar por sus jugadores favoritos, con controles para evitar fraudes o múltiples votos por usuario.

- **Ranking Dinámico**: Se genera un ranking en tiempo real mostrando los jugadores más votados por ciudad.

- **Procesamiento Asíncrono**: Los videos se procesan de manera asíncrona mediante procesos batch para optimizar la experiencia del usuario y evitar tiempos de espera prolongados.

## Estructura del Repositorio

Este repositorio contiene todos los componentes del proyecto ANB Rising Stars Showcase, organizado en los siguientes directorios:

### 📁 [capacity-planning/](capacity-planning/plan_de_pruebas.md)
Contiene el análisis detallado de capacidad de la aplicación, incluyendo:
- Escenarios de carga planteados
- Métricas seleccionadas para evaluación
- Resultados esperados de las pruebas
- Recomendaciones para escalar la solución

**[Ver plan de pruebas de capacidad →](capacity-planning/plan_de_pruebas.md)**

### 📁 [collections/](collections/README.md)
Contiene la colección de Postman con todos los endpoints de la API documentados y listos para probar. Incluye ejemplos de requests y responses para facilitar la integración y testing de la API.

**[Ver documentación completa de la colección →](collections/README.md)**

### 📁 [docs/Entrega_1/](docs/Entrega_1/README.md)
Contiene todos los archivos entregables de la primera entrega del proyecto, incluyendo diagramas de arquitectura, documentación técnica, y reportes de las pruebas realizadas.

**[Ver documentación de la Entrega 1 →](docs/Entrega_1/README.md)**

### 📁 [source/](source/README.md)
Contiene los archivos fuente de la aplicación, incluyendo el código del backend API, worker de procesamiento de videos, configuración de servicios y pruebas de carga. Esta es la carpeta principal del desarrollo.

**Componentes incluidos:**
- Backend API (FastAPI)
- Worker de procesamiento de videos (Celery)
- API Gateway (NGINX)
- Base de datos (PostgreSQL)
- Pruebas de rendimiento (JMeter)

**[Ver documentación técnica completa →](source/README.md)**

### 📁 [sustentacion/Entrega_1/](sustentacion/Entrega_1/README.md)
Contiene el video de sustentación del proyecto para la primera entrega, donde se presenta la solución desarrollada, la arquitectura implementada y una demostración del funcionamiento del sistema.

**[Ver información del video de sustentación →](sustentacion/Entrega_1/README.md)**

## Inicio Rápido

### Requisitos Previos

- Docker Desktop (versión 20.10 o superior)
- Docker Compose (versión 2.0 o superior)
- Al menos 4GB de RAM disponible
- 10GB de espacio en disco

### Instalación y Ejecución

```bash
# 1. Clonar el repositorio
git clone <repository-url>
cd MISW-4204-desarrollo-de-software-en-la-nube

# 2. Ir al directorio source
cd source

# 3. Configurar variables de entorno
cd backend
cp config.env.example config.env
# Editar config.env con los valores apropiados
cd ..

# 4. Levantar los servicios
docker-compose up --build
```

Los servicios estarán disponibles en:
- **API Backend**: http://localhost/api
- **Documentación API (Swagger)**: http://localhost/docs
- **RabbitMQ Management**: http://localhost:15672

Para instrucciones detalladas de instalación, configuración y despliegue, consulte la **[documentación técnica en source/](source/README.md)**.

## Pruebas de la API

Para probar la API puede utilizar:

1. **Swagger UI**: Acceder a http://localhost/docs
2. **Colección de Postman**: Importar desde [collections/](collections/README.md)

## Documentación del Proyecto

- **[Plan de Pruebas de Capacidad](capacity-planning/plan_de_pruebas.md)** - Análisis de capacidad y escalabilidad
- **[Arquitectura y Detalles Técnicos](source/README.md)** - Información completa sobre la arquitectura, tecnologías y componentes
- **[Colección de Postman](collections/README.md)** - Endpoints y ejemplos de uso de la API
- **[Documentación Entrega 1](docs/Entrega_1/README.md)** - Entregables y documentación académica
- **[Video de Sustentación](sustentacion/Entrega_1/README.md)** - Presentación del proyecto

## Impacto Esperado

ANB Rising Stars Showcase democratiza el acceso al proceso de selección de nuevos talentos en el baloncesto, reduciendo barreras geográficas y económicas. La plataforma tecnológica apoya la misión de la ANB de fomentar el deporte e identificar jóvenes promesas que puedan integrarse en el baloncesto profesional.

## Licencia

Este proyecto es desarrollado como parte del curso MISW-4204 Desarrollo de Software en la Nube de la Universidad de los Andes.