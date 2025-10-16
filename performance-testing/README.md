# Guía de Pruebas de Rendimiento (Escenario 1)

Este documento contiene las instrucciones para ejecutar los escenarios de prueba de carga definidos para la capa web de la aplicación.

---

### Requisitos Previos

1.  **Token de Autenticación (¡MUY IMPORTANTE!)**
    *   Antes de ejecutar cualquier prueba, es **indispensable** editar los 3 archivos `.jmx` (`smoke_test.jmx`, `ramp_up_test.jmx`, `sustained_test.jmx`) en un editor de texto.
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
    docker-compose up -d --build
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

Los archivos de resultados (`.jtl`) de cada ejecución aparecerán en la carpeta `performance-testing/jmeter/scenarios/` para su posterior análisis.
