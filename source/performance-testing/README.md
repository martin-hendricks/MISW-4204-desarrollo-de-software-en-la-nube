# Guía de Pruebas de Rendimiento (Escenario 1)

Este documento contiene las instrucciones para ejecutar los escenarios de prueba de carga definidos para la capa web de la aplicación.

---

### Requisitos Previos

1.  **Token de Autenticación (¡MUY IMPORTANTE!)**
    *   Antes de ejecutar cualquier prueba, es **indispensable** editar los 3 archivos `.jmx` (`smoke_test.jmx`, `ramp_up_test.jmx`, `sustained_test.jmx`) en un editor de texto. Estos archivos se encuentran en la carpeta `performance-testing/web-api-tests/scenarios/`.
    *   Busca el valor `Bearer YOUR_JWT_TOKEN_HERE` y reemplázalo con un token JWT válido de un usuario de prueba de tu aplicación.

2.  **Activar el Modo de Prueba en el Backend**
    *   Asegúrate de que tu archivo principal `docker-compose.yml` tenga la variable de entorno `TEST_MODE: "true"` en el servicio `backend`. Esto es necesario para desacoplar la capa asíncrona y medir únicamente el rendimiento de la capa web.

    ```yaml
    # docker-compose.yml
    services:
      backend:
        build: ./backend
        ports:
          - "8000:8000"
        environment:
          - TEST_MODE=true  # <--- ASEGURARSE DE QUE ESTA LÍNEA EXISTA
          - DATABASE_URL=postgresql://user:password@database:5432/fileprocessing
          # ... resto de variables
    ```

### Pasos para la Ejecución

#### 1. Iniciar la Aplicación Principal

**Opcion 1: Desde el directorio source**
```sh
cd source
docker-compose up --build --remove-orphans
```

**Opcion 2: Desde el directorio raiz**
```sh
docker-compose -f source/docker-compose.yml up --build --remove-orphans
```

#### 2. Iniciar el Entorno de Pruebas

**Opcion 1: Desde el directorio source**
```sh
docker-compose -f performance-testing/docker-compose.testing.yml up -d
```

**Opcion 2: Desde el directorio raiz**
```sh
docker-compose -f source/performance-testing/docker-compose.testing.yml up -d
```

### Comandos de JMeter

Una vez que ambos entornos estén corriendo, puedes ejecutar los diferentes escenarios de prueba desde tu terminal.

#### 1. Prueba de Sanidad (Smoke Test)
*   **Propósito:** Validar que todo el sistema responde correctamente con una carga mínima.
*   **Comando:**
    ```sh
    docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"
    ```

#### 2. Prueba de Escalamiento (Ramp-up)
*   **Propósito:** Encontrar la capacidad máxima de usuarios concurrentes aumentando la carga gradualmente.
*   **Parámetro:** `-Jusers=<numero>` permite definir el número de usuarios para la prueba.
*   **Comandos de ejemplo:**
    ```sh
    # Prueba con 100 usuarios
    docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_100_users_results.jtl -Jusers=100"

    # Prueba con 200 usuarios
    docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_200_users_results.jtl -Jusers=200"
    ```

#### 3. Prueba Sostenida (Sustained)
*   **Propósito:** Confirmar la estabilidad del sistema a un alto porcentaje (ej. 80%) de su capacidad máxima encontrada.
*   **Parámetro:** `-Jusers=<numero>`
*   **Comando de ejemplo:**
    ```sh
    # Prueba con 80 usuarios (si 100 fue la capacidad máxima)
    docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/sustained_test.jmx -l /scripts/sustained_80_users_results.jtl -Jusers=80"
    ```

---

Los archivos de resultados (`.jtl`) de cada ejecución aparecerán en la carpeta `performance-testing/web-api-tests/scenarios/` para su posterior análisis.


# Guía de Pruebas de Rendimiento del Worker (Escenario 2)

Para medir el rendimiento de la capa de workers (videos procesados por minuto), se utiliza un script (`producer.py`) que inyecta tareas directamente en la cola de Redis.

## Requisitos Previos

### Tener la aplicación principal corriendo

**Opcion 1: Desde el directorio source**
```sh
cd source
docker-compose up --build --remove-orphans
```

**Opcion 2: Desde el directorio raiz**
```sh
docker-compose -f source/docker-compose.yml up --build --remove-orphans
```

### Tener el entorno de pruebas corriendo

**Opcion 1: Desde el directorio source**
```sh
docker-compose -f performance-testing/docker-compose.testing.yml up -d
```

**Opcion 2: Desde el directorio raiz**
```sh
docker-compose -f source/performance-testing/docker-compose.testing.yml up -d
```

## Parámetros del Script

El script `producer.py` acepta los siguientes parámetros:

*   `--num-videos`: Número total de tareas a encolar (default: 10)
*   `--video-file`: Ruta al video de prueba dentro del contenedor (default: `./assets/dummy_file_50mb.mp4`)
*   `--timeout`: Tiempo máximo de espera en segundos (default: 600)
*   `--debug`: Activar modo debug con información adicional
*   `--no-wait`: **[RECOMENDADO]** Solo encolar tareas sin esperar resultados

## Importante: Modo `--no-wait`

**Se recomienda usar siempre el flag `--no-wait`** para pruebas de rendimiento, ya que:
- El worker NO tiene `result_backend` configurado (solo usa PostgreSQL)
- Sin `--no-wait`, el script intentará esperar resultados que nunca llegarán
- Con `--no-wait`, el script simplemente encola las tareas y termina inmediatamente
- Puedes monitorear el progreso real en Grafana o los logs del worker

---
## Ejemplos de Uso

A continuación se muestran ejemplos para los dos tipos de pruebas principales.

### 1. Pruebas Sostenidas (Medir Throughput Estable)

El objetivo es medir cuántos videos por minuto procesa el sistema bajo una carga constante y estable, sin que la cola de tareas crezca indefinidamente.

**Ejemplo básico con 20 videos:**
```bash
docker exec producer python producer.py --num-videos 20 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Ejemplo con 50 videos y modo debug:**
```bash
docker exec producer python producer.py --num-videos 50 --video-file ./assets/dummy_file_50mb.mp4 --no-wait --debug
```

**Ejemplo con video de 100MB:**
```bash
docker exec producer python producer.py --num-videos 10 --video-file ./assets/dummy_file_100mb.mp4 --no-wait
```

### 2. Pruebas de Saturación (Encontrar el Límite)

El objetivo es encontrar el punto de quiebre del sistema. Para ello, se aumenta progresivamente el número de videos en la cola hasta que se observa inestabilidad (la cola crece sin parar, los tiempos de procesamiento se disparan o empiezan a aparecer errores).

**Se recomienda ejecutar los siguientes comandos de forma secuencial**, observando el comportamiento en Grafana entre cada ejecución:

```bash
# Paso 1: Carga inicial (50 videos)
docker exec producer python producer.py --num-videos 50 --video-file ./assets/dummy_file_50mb.mp4 --no-wait

# Paso 2: Aumentar la carga si el sistema se mantiene estable (100 videos)
docker exec producer python producer.py --num-videos 100 --video-file ./assets/dummy_file_50mb.mp4 --no-wait

# Paso 3: Carga alta para encontrar el punto de saturación (200 videos)
docker exec producer python producer.py --num-videos 200 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Importante:** Espera a que se procesen todas las tareas antes de lanzar el siguiente lote. Monitorea en Grafana que la cola se vacíe completamente.

---
## Monitoreo del Rendimiento

Existen varias formas de monitorear el procesamiento de las tareas:

### 1. Grafana (Recomendado para Métricas)
*   **URL:** [http://localhost:3000](http://localhost:3000)
*   **Credenciales:** `admin` / `admin`
*   **Qué observar:**
    - Tamaño de la cola de tareas (debe decrecer si el sistema está procesando)
    - Throughput (videos procesados por minuto)
    - Tiempo de procesamiento por video
    - Uso de CPU y memoria

### 2. Logs del Worker en Tiempo Real
Para ver el procesamiento en tiempo real:
```bash
docker logs -f misw-4204-desarrollo-de-software-en-la-nube-worker-1
```

Para ver solo las tareas completadas:
```bash
docker logs misw-4204-desarrollo-de-software-en-la-nube-worker-1 2>&1 | grep "succeeded"
```

### 3. Verificar Cola de Redis
Para ver cuántas tareas hay pendientes en la cola:
```bash
docker exec redis redis-cli LLEN video_processing
```

---
## Troubleshooting

### El script no muestra output
- **Solución:** Asegúrate de haber reconstruido el contenedor producer después de modificar el código:

**Desde el directorio source:**
```bash
docker-compose -f performance-testing/docker-compose.testing.yml up -d --build producer
```

**Desde el directorio raiz:**
```bash
docker-compose -f source/performance-testing/docker-compose.testing.yml up -d --build producer
```

### Las tareas no se procesan
- **Verificar que el worker esté corriendo:**
  ```bash
  docker ps | grep worker
  ```
- **Ver logs del worker para errores:**
  ```bash
  docker logs misw-4204-desarrollo-de-software-en-la-nube-worker-1
  ```

### Error de conexión a Redis
- **Verificar que Redis esté corriendo:**
  ```bash
  docker ps | grep redis
  ```
- **Verificar que ambos contenedores estén en la misma red:**
  ```bash
  docker network inspect app-network
  ```

---
## Resultados Esperados

Con la configuración por defecto (4 workers concurrentes), deberías observar:
- **Throughput:** Aproximadamente 12-15 videos/minuto (con videos de ~2MB)
- **Tiempo de procesamiento:** 4-5 segundos por video
- **Concurrencia:** Hasta 4 videos procesándose simultáneamente

**Nota:** Los tiempos reales dependerán del hardware donde se ejecute Docker y del tamaño de los videos.