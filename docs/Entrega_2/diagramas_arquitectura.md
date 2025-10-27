# Diagramas de Arquitectura - ANB Rising Stars Showcase - AWS

Este documento presenta el diagrama de arquitectura del sistema ANB Rising Stars Showcase, actualizado de acuerdo a las instancias levantasdas en AWS mostrando diferentes niveles de abstraccion y detalle de los componentes y sus interacciones.

## 1. Diagrama de Componentes

El diagrama de componentes muestra la estructura interna del Backend API, detallando los modulos y capas que lo componen siguiendo los principios de Domain-Driven Design (DDD). Los cuales se instalaron en las 4 instancias de AWS.   

![Deployment Diagram with Components](https://github.com/user-attachments/assets/b20aea3b-7adf-4a5a-a943-5ed76882498f)


**Capas principales:**
- **Routers**: Definicion de endpoints de la API REST
- **Services**: Logica de negocio y casos de uso
- **Domain**: Entidades, value objects y repositorios (interfaces)
- **Infrastructure**: Implementaciones concretas (base de datos, servicios externos)
- **DTOs**: Objetos de transferencia de datos para comunicacion con clientes


### Etapa de Carga
1. El jugador se autentica en el sistema
2. Sube el video a traves del API
3. El sistema guarda el video original y registra la metadata en la base de datos
4. Se publica una tarea de procesamiento en RabbitMQ
5. Se retorna un task_id al jugador

### Etapa de Procesamiento Asincrono
1. El Worker consume la tarea desde RabbitMQ
2. Descarga el video original del almacenamiento
3. Procesa el video con FFmpeg:
   - Recorta a maximo 30 segundos
   - Ajusta resolucion y formato
   - Agrega marca de agua de ANB
   - Elimina audio
4. Guarda el video procesado en el almacenamiento
5. Actualiza el estado del video a "procesado" en la base de datos

### Etapa de Consulta y Entrega
1. El publico consulta los videos disponibles
2. El sistema retorna los videos procesados
3. Los usuarios pueden visualizar y votar por los videos
4. Se actualiza el ranking dinamicamente


## Patrones de Diseno Implementados

### 1. API Gateway Pattern
- NGINX actua como punto de entrada unico
- Centraliza autenticacion, logging y routing

### 2. Message Queue Pattern
- Redis desacopla productores (backend) de consumidores (workers)
- Permite procesamiento asincrono y escalabilidad

### 3. Worker Pattern
- Workers especializados en tareas pesadas (procesamiento de video)
- Multiples workers pueden procesar tareas en paralelo

### 4. Repository Pattern
- El backend usa repositorios para abstraer el acceso a datos
- Facilita testing y cambios de base de datos

## Referencias

- [Documentacion Tecnica Completa](../../source/README.md)
- [Backend API Documentation](../../source/backend/README.md)
- [Performance Testing Guide](../../source/performance-testing/README.md)
