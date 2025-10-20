# Documentacion - Entrega 1

Este directorio contiene todos los archivos entregables de la primera entrega del proyecto ANB Rising Stars Showcase, incluyendo diagramas de arquitectura, documentacion tecnica y reportes de las pruebas realizadas.

## Contenido de la Entrega

### 📄 Codigo Fuente de la Aplicacion
**Ubicacion:** `source/`

Contiene los archivos fuente de la aplicacion, incluyendo el codigo del backend API, worker de procesamiento de videos, configuracion de servicios y pruebas de carga. Esta es la carpeta principal del desarrollo. Tambien encontrara las instrucciones de ejecucion.

**Componentes incluidos:**
- Backend API (FastAPI)
- Worker de procesamiento de videos (Celery)
- API Gateway (NGINX)
- Base de datos (PostgreSQL)

**[Ver documentacion tecnica completa →](../../source/README.md)**

### 🧪Codigo Fuente de las Pruebas de Rendimiento y Carga
**Ubicacion:** `source/performance-testing/`

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

**[Ver documentacion de pruebas de rendimiento →](../../source/performance-testing/README.md)**

### 📊 Diagramas de Arquitectura
**Ubicacion:** `docs/Entrega_1/diagramas_arquitectura.md`

Los diagramas de arquitectura muestran diferentes niveles de abstraccion y detalle del sistema:

1. **Diagrama de Contexto**
2. **Diagrama de Contenedores**
3. **Diagrama de Componentes**
4. **Diagrama de Entidad-Relacion**
5. **Diagrama de Flujo**

**[Ver Diagramas de Arquitectura →](diagramas_arquitectura.md)**

### ⚙️ Pipeline de CI/CD
**Ubicacion:** `.github/`

Contiene la configuracion del pipeline de CI/CD implementado con GitHub Actions. El pipeline incluye:
- Ejecucion automatica de pruebas unitarias con cobertura
- Construccion y validacion de imagenes Docker
- Integracion con Codecov para reportes de cobertura

**Pipelines disponibles:**
- Pipeline principal (CI completo con tests, build y SonarCloud)
- Pipeline de backend (optimizado para cambios solo en backend)

**[Ver documentacion completa de CI/CD →](../../.github/README-CI.md)**

### 📈 Resultados de SonarCloud
**Ubicacion:** `docs/Entrega_1/resultados_sonarclaud.md`

Contiene el analisis estatico de calidad de codigo realizado con SonarCloud, una plataforma de inspeccion continua que evalua la calidad del codigo fuente. Incluye:
- Metricas de calidad de codigo (bugs, vulnerabilidades, code smells)
- Analisis de cobertura de pruebas
- Evaluacion de duplicacion de codigo
- Calificacion general del proyecto (Quality Gate)
- Recomendaciones para mejoras de calidad

**Metricas evaluadas:**
- Reliability (Confiabilidad)
- Security (Seguridad)
- Maintainability (Mantenibilidad)
- Coverage (Cobertura de pruebas)
- Duplications (Duplicacion de codigo)

**[Ver resultados completos de SonarCloud →](resultados_sonarclaud.md)**

### 📦 Plan de Pruebas de Capacidad
**Ubicacion:** `capacity-planning/plan_de_pruebas.md`

Contiene el analisis detallado de capacidad de la aplicacion, incluyendo:
- Escenarios de carga planteados
- Metricas seleccionadas para evaluacion
- Resultados esperados de las pruebas
- Recomendaciones para escalar la solucion

**[Ver plan de pruebas de capacidad →](../../capacity-planning/plan_de_pruebas.md)**

### 📊 Resultados de Pruebas de Capacidad
**Ubicacion:** `capacity-planning/resultados.md`

Contiene los resultados completos y evidencias de las pruebas de capacidad ejecutadas sobre el sistema. Documenta los escenarios de prueba implementados para evaluar tanto la capa web como la capa de procesamiento worker. Incluye:
- Resultados de pruebas de carga en la capa web
- Resultados de pruebas de rendimiento del worker
- Evidencias fotograficas y enlaces a Grafana de cada prueba
- Analisis de capacidad maxima encontrada
- Metricas de rendimiento y estabilidad del sistema

**Escenarios de prueba documentados:**

**Escenario 1: Capacidad de la Capa Web**
- Smoke Test (5 usuarios concurrentes, 1 minuto)
- Ramp-up Test (escalamiento gradual hasta saturacion: 100, 200, 300 usuarios)
- Sustained Test (carga sostenida al 80% de capacidad maxima: 116 usuarios)

**Escenario 2: Rendimiento de la Capa Worker**
- Pruebas de saturacion con diferentes niveles de concurrencia
- Configuraciones de worker: 1, 2, 4 procesos/hilos por nodo
- Procesamiento de videos de 50MB
- Medicion de videos procesados por minuto

**[Ver resultados completos de Pruebas de Capacidad →](../../capacity-planning/resultados.md)**

### 📦 Coleccion de Postman
**Ubicacion:** `collections/`

Contiene la coleccion de Postman con todos los endpoints de la API documentados y listos para probar. Incluye ejemplos de requests y responses para facilitar la integracion y testing de la API.

**[Ver documentacion completa de la coleccion →](../../collections/)**

### 📈 Resultados de Newman
**Ubicacion:** `collections/resultados_newman.md`

Contiene los resultados de las pruebas automatizadas de la API ejecutadas con Newman, el corredor de linea de comandos para colecciones de Postman. Incluye:
- Ejecucion de pruebas de endpoints de la API
- Validacion de contratos de respuesta
- Verificacion de codigos de estado HTTP
- Tiempos de respuesta de cada endpoint
- Tasa de exito de las pruebas
- Reportes detallados de pruebas fallidas (si las hay)

**Tipos de pruebas ejecutadas:**
- Tests de autenticacion y autorizacion
- Tests de operaciones CRUD
- Tests de validacion de datos
- Tests de manejo de errores

**[Ver resultados completos de Newman →](../../collections/resultados_newman.md)**

### 🎥 Video de Sustentacion
**Ubicacion:** `sustentacion/Entrega_1/`

Contiene el video de sustentacion del proyecto para la primera entrega, donde se presenta la solucion desarrollada, la arquitectura implementada y una demostracion del funcionamiento del sistema.

**[Ver informacion del video de sustentacion →](../../sustentacion)**

**Curso**: MISW-4204 Desarrollo de Software en la Nube
**Numero de Equipo** : 2
**Universidad**: Universidad de los Andes
