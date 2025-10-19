# Documentacion - Entrega 1

Este directorio contiene todos los archivos entregables de la primera entrega del proyecto ANB Rising Stars Showcase, incluyendo diagramas de arquitectura, documentacion tecnica y reportes de las pruebas realizadas.

## Contenido de la Entrega

### 📁 [Diagramas de Arquitectura](diagramas_arquitectura.md)

Los diagramas de arquitectura muestran diferentes niveles de abstraccion y detalle del sistema:

1. **Diagrama de Contexto**
2. **Diagrama de Contenedores**
3. **Diagrama de Componentes**
4. **Diagrama de Entidad-Relacion**
5. **Diagrama de Flujo**

**[Ver plan de Diagramas de Arquitectura](diagramas_arquitectura.md)**

## Estructura del Repositorio

Este repositorio contiene todos los componentes del proyecto ANB Rising Stars Showcase, organizado en los siguientes directorios:

### 📁 [capacity-planning/](../../capacity-planning/plan_de_pruebas.md)
Contiene el analisis detallado de capacidad de la aplicacion, incluyendo:
- Escenarios de carga planteados
- Metricas seleccionadas para evaluacion
- Resultados esperados de las pruebas
- Recomendaciones para escalar la solucion

**[Ver plan de pruebas de capacidad](../../capacity-planning/plan_de_pruebas.md)**

### 📁 [collections/](../../collections/README.md)
Contiene la coleccion de Postman con todos los endpoints de la API documentados y listos para probar. Incluye ejemplos de requests y responses para facilitar la integracion y testing de la API.

**[Ver documentacion completa de la coleccion](../../collections/README.md)**

### 📁 [source/](../../source/README.md)
Contiene los archivos fuente de la aplicacion, incluyendo el codigo del backend API, worker de procesamiento de videos, configuracion de servicios y pruebas de carga. Esta es la carpeta principal del desarrollo. Tambien encontrara las instrucciones de ejecucion.

**Componentes incluidos:**
- Backend API (FastAPI)
- Worker de procesamiento de videos (Celery)
- API Gateway (NGINX)
- Base de datos (PostgreSQL)

**[Ver documentacion tecnica completa](../../source/README.md)**

### 📁 [source/performance-testing/](../../source/performance-testing/README.md)
Contiene la suite completa de pruebas de rendimiento y carga del sistema, ejecutandose en un entorno Docker separado. Incluye:
- Pruebas de carga con Apache JMeter
- Monitoreo con Prometheus y Grafana
- Scripts de pruebas de rendimiento del worker
- Resultados y reportes de pruebas

**Tipos de pruebas:**
- Smoke Test (validacion basica)
- Ramp-up Test (incremento gradual de usuarios)
- Sustained Test (carga sostenida)
- Worker Performance Test (rendimiento del procesamiento)

**[Ver documentacion de pruebas de rendimiento](../../source/performance-testing/README.md)**

### 📁 [sustentacion/Entrega_1/](../../sustentacion/Entrega_1/README.md)
Contiene el video de sustentacion del proyecto para la primera entrega, donde se presenta la solucion desarrollada, la arquitectura implementada y una demostracion del funcionamiento del sistema.

**[Ver informacion del video de sustentacion](../../sustentacion/Entrega_1/README.md)**


**Curso**: MISW-4204 Desarrollo de Software en la Nube
**Universidad**: Universidad de los Andes