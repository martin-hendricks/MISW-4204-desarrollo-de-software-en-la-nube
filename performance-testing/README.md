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

1.  **Iniciar la Aplicación Principal**
    *   Abre una terminal en la raíz del proyecto. Si la aplicación ya está corriendo, es recomendable reconstruirla para asegurar que los cambios en el código se apliquen.
    ```sh
    docker-compose up --build --remove-orphans
    ```

2.  **Iniciar el Entorno de Pruebas**
    *   En la misma terminal, levanta el stack de Prometheus, Grafana y JMeter.
    ```sh
    docker-compose -f performance-testing/docker-compose.testing.yml up -d
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


# Guía de Pruebas de Rendimiento del Worker(Escenario 2)

Para medir el rendimiento de la capa de workers (videos procesados por minuto), se utiliza un script (`producer.py`) que inyecta tareas directamente en la cola de Redis.

**Requisitos:**
*   Tener la aplicación principal corriendo: `docker-compose up -d`
*   Tener el entorno de pruebas corriendo: `docker-compose -f performance-testing/docker-compose.testing.yml up -d`

**Pasos para Ejecutar una Prueba:**

1.  **Acceder al contenedor `producer`:** El script se ejecuta desde dentro del contenedor `producer` usando `docker exec`.

2.  **Ejecutar el script `producer.py`:** Los parámetros clave son:
    *   `--num-videos`: Número total de tareas a encolar.
    *   `--video-file`: Ruta al video de prueba. Los videos disponibles están en `./assets/`.

---
### Ejemplos de Uso

A continuación se muestran ejemplos para los dos tipos de pruebas principales.

#### 1. Pruebas Sostenidas (Medir Throughput Estable)

El objetivo es medir cuántos videos por minuto procesa el sistema bajo una carga constante y estable, sin que la cola de tareas crezca indefinidamente.

**Ejemplo con video de 50MB:**
```bash
docker exec producer python producer.py --num-videos 20 --video-file ./assets/dummy_file_50mb.mp4
```

**Ejemplo con video de 100MB (requiere añadir el archivo `dummy_file_100mb.mp4` a la carpeta `worker-tests/assets`):**
```bash
docker exec producer python producer.py --num-videos 10 --video-file ./assets/dummy_file_100mb.mp4
```

#### 2. Pruebas de Saturación (Encontrar el Límite)

El objetivo es encontrar el punto de quiebre del sistema. Para ello, se aumenta progresivamente el número de videos en la cola hasta que se observa inestabilidad (la cola crece sin parar, los tiempos de procesamiento se disparan o empiezan a aparecer errores).

Se recomienda ejecutar los siguientes comandos de forma secuencial, observando el comportamiento en Grafana entre cada ejecución.

**Ejemplo de rampa de carga con video de 50MB:**

```bash
# Paso 1: Carga inicial
docker exec producer python producer.py --num-videos 50 --video-file ./assets/dummy_file_50mb.mp4

# Paso 2: Aumentar la carga si el sistema se mantiene estable
docker exec producer python producer.py --num-videos 100 --video-file ./assets/dummy_file_50mb.mp4

# Paso 3: Carga alta para encontrar el punto de saturación
docker exec producer python producer.py --num-videos 200 --video-file ./assets/dummy_file_50mb.mp4
```

---
### Monitoreo

Mientras la prueba está en ejecución, monitorea las métricas en tiempo real desde Grafana:
*   **URL:** [http://localhost:3000](http://localhost:3000) (user: `admin`, pass: `admin`)

Observa el dashboard del Worker, prestando especial atención al **tamaño de la cola de tareas**, el **throughput (videos/min)** y el **tiempo de procesamiento**.