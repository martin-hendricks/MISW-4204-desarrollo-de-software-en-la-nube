# Documentacion - Entrega 3

Este directorio contiene todos los archivos entregables de la Segunda entrega del proyecto ANB Rising Stars Showcase, incluyendo diagramas de arquitectura, documentacion tecnica y reportes de las pruebas realizadas.

## Contenido de la Entrega

### 📄 Codigo Fuente del backend para subir en la instancia de AWS
**Ubicacion:** `source/deployment/backend-instance/`

Contiene los archivos necesarios para el despliegue en las instancias de aws,tambien encontrara las instrucciones de ejecucion.

**Componentes incluidos:**
- `DEPLOY.md` - Instrucciones de despliegue del backend
- `docker-compose.yml` - Configuracion de contenedores Docker
- `init-database.sh` - Script de inicializacion de base de datos
- `nginx.conf` - Configuracion del servidor Nginx
- `setup-nfs-mount.sh` - Script de montaje de NFS

**[Ver documentacion tecnica completa →](../../source/deployment/backend-instance/DEPLOY.md)**

### 📄 Codigo Fuente del Worker para subir en la instancia de AWS
**Ubicacion:** `source/deployment/worker-instance/`

Contiene los archivos necesarios para el despliegue en las instancias de aws,tambien encontrara las instrucciones de ejecucion.

**Componentes incluidos:**
- `DEPLOY.md` - Instrucciones de despliegue del worker
- `docker-compose.yml` - Configuracion de contenedores Docker
- `setup-nfs-mount.sh` - Script de montaje de NFS

**[Ver documentacion tecnica completa →](../../source/deployment/worker-instance/DEPLOY.md)**

### 🧪Codigo Fuente de las Pruebas de Rendimiento y Carga para subir en la instancia de AWS
**Ubicacion:** `source/deployment/performance-instance/`

Contiene los archivos necesarios para el despliegue en las instancias de aws,tambien encontrara las instrucciones de ejecucion.

**Componentes incluidos:**
- `CHECKLIST.md` - Lista de verificacion para pruebas
- `DEPLOY.md` - Instrucciones de despliegue de herramientas de prueba
- `docker-compose.yml` - Configuracion de contenedores Docker
- `prometheus.yml` - Configuracion de Prometheus para metricas
- `README.md` - Documentacion del sistema de pruebas
- `setup-ssh-tunnel.sh` - Script de configuracion de tunel SSH

**[Ver documentacion tecnica completa →](../../source/deployment/performance-instance/DEPLOY.md)**

### 📊 Diagramas de Arquitectura
**Ubicacion:** `docs/Entrega_2/diagramas_arquitectura.md`

Los diagramas de arquitectura actualizados a la arquitectura de AWS muestran diferentes niveles de abstraccion y detalle del sistema:

1. **Diagrama de Componentes**

**[Ver Diagramas de Arquitectura →](diagramas_arquitectura.md)**

### 📦 Plan de Pruebas de Capacidad
**Ubicacion:** `capacity-planning/plan_de_pruebas.md`

Contiene el analisis detallado de capacidad de la aplicacion, incluyendo:
- Escenarios de carga planteados
- Metricas seleccionadas para evaluacion
- Resultados esperados de las pruebas
- Recomendaciones para escalar la solucion

**[Ver plan de pruebas de capacidad →](../../capacity-planning/plan_de_pruebas.md)**

### 📦 Resultados Plan de Pruebas de Capacidad
**Ubicacion:** `capacity-planning/plan_de_pruebas_entrega2.md`

Contiene el analisis detallado de capacidad de la aplicacion, realizado sobre AWS incluyendo:
- Resultados de pruebas de carga en la capa web
- Resultados de pruebas de rendimiento del worker
- Evidencias fotograficas y enlaces a Grafana de cada prueba
- Analisis de capacidad maxima encontrada
- Metricas de rendimiento y estabilidad del sistema

**[Ver plan de pruebas de capacidad →](../../capacity-planning/pruebas_de_carga_entrega2.md)**

### 🎥 Video de Sustentacion
**Ubicacion:** `sustentacion/Entrega_3/`

Contiene el video de sustentacion del proyecto para la primera entrega, donde se presenta la solucion desarrollada, la arquitectura implementada y una demostracion del funcionamiento del sistema.

**[Ver informacion del video de sustentacion →]()**

**Curso**: MISW-4204 Desarrollo de Software en la Nube
**Numero de Equipo** : 2
**Universidad**: Universidad de los Andes
