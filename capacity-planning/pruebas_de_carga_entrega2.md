## 4. Escenarios de Prueba

### 4.1 Escenario 1: Capacidad de la Capa Web (Usuarios Concurrentes)

#### 4.1.1 Estrategia de Implementación
- **Desacoplamiento del Worker**: Los endpoints de carga devuelven 202 y redirigen a un mock de cola que acepta mensajes en memoria
- **Simulación de Carga Real**: Uso de archivos de video reales para simular condiciones de producción
- **Modo de Prueba**: Activación de `TEST_MODE=true` para deshabilitar el procesamiento real

#### 4.1.2 Escenarios de Prueba

**Prueba de Sanidad (Smoke Test)**
- **Usuarios**: 5 usuarios concurrentes
- **Duración**: 1 minuto
- **Objetivo**: Validar que el sistema responde correctamente y la telemetría está activa
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"`
- **Evidencias**: 
  - [Smoke Test](https://uniandes-my.sharepoint.com/:i:/r/personal/am_rodriguezs1_uniandes_edu_co1/Documents/Desarrollo%20de%20Software%20en%20la%20Nube/Semana%201-2/Evidencias%20pruebas%20de%20carga/Captura%20de%20pantalla%202025-10-19%20104146.jpg?csf=1&web=1&e=C57rsM)
  - [Grafana](https://uniandes-my.sharepoint.com/:i:/r/personal/am_rodriguezs1_uniandes_edu_co1/Documents/Desarrollo%20de%20Software%20en%20la%20Nube/Semana%201-2/Evidencias%20pruebas%20de%20carga/Captura%20de%20pantalla%202025-10-19%20121438.jpg?csf=1&web=1&e=HfT6R2)

**Prueba de Escalamiento (Ramp-up)**
- **Estrategia**: Iniciar en 0 usuarios y aumentar gradualmente hasta X usuarios en 3 minutos, mantener 5 minutos
- **Niveles de Prueba**: 100 → 200 → 300 → 400 → 500 usuarios (se saturo maquina en 300 usuarios)
- **Objetivo**: Encontrar la capacidad máxima sin degradación significativa
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_X_users_results.jtl -Jusers=X"`
- **Evidencias**: 
  - [100 Usuarios](https://uniandes-my.sharepoint.com/:i:/r/personal/am_rodriguezs1_uniandes_edu_co1/Documents/Desarrollo%20de%20Software%20en%20la%20Nube/Semana%201-2/Evidencias%20pruebas%20de%20carga/Captura%20de%20pantalla%202025-10-19%20104146.jpg?csf=1&web=1&e=P5vQ1z)
    - [Grafana](https://uniandes-my.sharepoint.com/:i:/r/personal/am_rodriguezs1_uniandes_edu_co1/Documents/Desarrollo%20de%20Software%20en%20la%20Nube/Semana%201-2/Evidencias%20pruebas%20de%20carga/Captura%20de%20pantalla_19-10-2025_105523_localhost.jpeg?csf=1&web=1&e=1V6JtO)

  - [200 Usuarios](https://uniandes-my.sharepoint.com/:i:/r/personal/am_rodriguezs1_uniandes_edu_co1/Documents/Desarrollo%20de%20Software%20en%20la%20Nube/Semana%201-2/Evidencias%20pruebas%20de%20carga/Captura%20de%20pantalla%202025-10-19%20110937.jpg?csf=1&web=1&e=xXUYYO)
    - [Grafana](https://uniandes-my.sharepoint.com/:i:/r/personal/am_rodriguezs1_uniandes_edu_co1/Documents/Desarrollo%20de%20Software%20en%20la%20Nube/Semana%201-2/Evidencias%20pruebas%20de%20carga/Captura%20de%20pantalla_19-10-2025_105523_localhost.jpeg?csf=1&web=1&e=1V6JtO)
  - [300 Usuarios](https://uniandes-my.sharepoint.com/:i:/r/personal/am_rodriguezs1_uniandes_edu_co1/Documents/Desarrollo%20de%20Software%20en%20la%20Nube/Semana%201-2/Evidencias%20pruebas%20de%20carga/Captura%20de%20pantalla%202025-10-19%20113342.jpg?csf=1&web=1&e=qWGLfL)
    - [Grafana](https://uniandes-my.sharepoint.com/:i:/r/personal/am_rodriguezs1_uniandes_edu_co1/Documents/Desarrollo%20de%20Software%20en%20la%20Nube/Semana%201-2/Evidencias%20pruebas%20de%20carga/Captura%20de%20pantalla_19-10-2025_113229_localhost.jpeg?csf=1&web=1&e=kljeOP)

**Prueba Sostenida**
- **Usuarios**: 80% de la capacidad máxima encontrada (cap maxima 145 usuarios, se realizo prueba con 116 usuarios)
- **Duración**: 5 minutos
- **Objetivo**: Confirmar estabilidad del sistema bajo carga sostenida
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/sustained_test.jmx -l /scripts/sustained_X_users_results.jtl -Jusers=X"`
- **Evidencias**:
  - [Prueba sostenida](https://uniandes-my.sharepoint.com/:i:/r/personal/am_rodriguezs1_uniandes_edu_co1/Documents/Desarrollo%20de%20Software%20en%20la%20Nube/Semana%201-2/Evidencias%20pruebas%20de%20carga/Captura%20de%20pantalla%202025-10-19%20121438.jpg?csf=1&web=1&e=HfT6R2)
  - [Grafana](https://uniandes-my.sharepoint.com/:i:/r/personal/am_rodriguezs1_uniandes_edu_co1/Documents/Desarrollo%20de%20Software%20en%20la%20Nube/Semana%201-2/Evidencias%20pruebas%20de%20carga/Captura%20de%20pantalla_19-10-2025_11947_localhost.jpeg?csf=1&web=1&e=xOhcXk)
#### 4.1.3 Endpoints a Probar
- `POST /auth/login` - Autenticación
- `POST /videos/upload` - Subida de videos
- `GET /videos` - Lista de videos del usuario
- `GET /public/videos` - Videos públicos
- `POST /public/videos/{video_id}/vote` - Votación

### 4.2 Escenario 2: Rendimiento de la Capa Worker (Videos/Minuto)

#### 4.2.1 Estrategia de Implementación
- **Bypass de la Web**: Inyección directa de mensajes en la cola Redis
- **Payloads Realistas**: Uso de archivos de video de diferentes tamaños (50MB)
- **Configuraciones Variables**: 1, 2, 4 procesos/hilos por nodo

#### 4.2.2 Escenarios de Prueba

**Pruebas de Saturación**
- **Objetivo**: Encontrar el punto de quiebre del sistema
- **Estrategia**: Aumentar progresivamente la cantidad de tareas en la cola
- **Comandos**:
  ```bash
  # Carga en la instancia de AWS
  docker exec producer python producer.py --num-videos 20 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
  ```
#### 4.2.3 Configuraciones de Prueba
- **Tamaños de Video**: 50MB
- **Concurrencia de Worker**: 1, 2, 4 procesos/hilos por nodo
- **Tiempo de Espera**: 600 segundos máximo por lote
- **Evidencias**:
  - [Pruebas de saturacion Worker](https://uniandes-my.sharepoint.com/:i:/r/personal/am_rodriguezs1_uniandes_edu_co1/Documents/Desarrollo%20de%20Software%20en%20la%20Nube/Semana%201-2/Evidencias%20pruebas%20de%20carga/Captura%20de%20pantalla_19-10-2025_11947_localhost.jpeg?csf=1&web=1&e=xOhcXk)