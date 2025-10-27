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
  - [Smoke Test](https://github.com/user-attachments/assets/2c667969-5672-48a4-8c69-2352482e0ce1)
  - <img width="1854" height="372" alt="smocke-test-5 usuario-logs" src="https://github.com/user-attachments/assets/ec1cf234-fc6a-4023-892a-90384972661e" />
  - [Grafana](https://github.com/user-attachments/assets/3393adf4-aa48-45fa-af0f-65ac2c9f3bb0)
<img width="1385" height="1141" alt="smocke-test-5 usuario-grafa" src="https://github.com/user-attachments/assets/3393adf4-aa48-45fa-af0f-65ac2c9f3bb0" />

**Prueba de Escalamiento (Ramp-up)**
- **Estrategia**: Iniciar en 0 usuarios y aumentar gradualmente hasta X usuarios en 3 minutos, mantener 5 minutos
- **Niveles de Prueba**: 100 → 200 → 300 → 400 → 500 usuarios (se saturo maquina en 300 usuarios)
- **Objetivo**: Encontrar la capacidad máxima sin degradación significativa
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_X_users_results.jtl -Jusers=X"`
- **Evidencias**: 
  - [100 Usuarios](https://github.com/user-attachments/assets/6c476e20-c3cf-4389-978b-fbe553440bb1)
  - <img width="3110" height="1132" alt="rtamup-100-log" src="https://github.com/user-attachments/assets/6c476e20-c3cf-4389-978b-fbe553440bb1" />
    - [Grafana-1](https://github.com/user-attachments/assets/20ffcc92-7fc4-4726-b8c5-63acb9167efd)
    - <img width="1385" height="1141" alt="rtamup-100-grafana" src="https://github.com/user-attachments/assets/20ffcc92-7fc4-4726-b8c5-63acb9167efd" />
    - [Grafana-2](https://github.com/user-attachments/assets/20ffcc92-7fc4-4726-b8c5-63acb9167efd](https://github.com/user-attachments/assets/0b53584c-f7c9-4d2c-be28-bff19e6fdf7c))
<img width="1385" height="1141" alt="rtamup-100-grafana-2" src="https://github.com/user-attachments/assets/0b53584c-f7c9-4d2c-be28-bff19e6fdf7c" />
  - [NFS](https://github.com/user-attachments/assets/8e8578f4-bb43-4f4c-b41d-6ecae8652c2e)
    <img width="599" height="214" alt="rtamup-100-nfs" src="https://github.com/user-attachments/assets/8e8578f4-bb43-4f4c-b41d-6ecae8652c2e" />

  - [200 Usuarios](https://github.com/user-attachments/assets/fc025045-8940-4984-ab8f-77cc94acd700)
  - 
<img width="2996" height="1182" alt="rtamup-200-logs" src="https://github.com/user-attachments/assets/fc025045-8940-4984-ab8f-77cc94acd700" />

    - [Grafana](https://github.com/user-attachments/assets/8b9b63db-dfba-4381-b1e5-240b760895c3)
   <img width="1385" height="1141" alt="rtamup-200-grafana" src="https://github.com/user-attachments/assets/8b9b63db-dfba-4381-b1e5-240b760895c3" />

  - [Grafana-2](https://github.com/user-attachments/assets/c5acf368-12fe-4b56-be2a-fbc5eea3aa25)

   <img width="1385" height="1141" alt="rtamup-200-grafana-2" src="https://github.com/user-attachments/assets/c5acf368-12fe-4b56-be2a-fbc5eea3aa25" />
   
    - [NFS-](https://github.com/user-attachments/assets/b0136313-1132-450f-9ffd-74d99ac19909)
<img width="1265" height="816" alt="Captura de pantalla 2025-10-26 205750" src="" />


  - [300 Usuarios]()
    - [Grafana]()

**Prueba Sostenida**

- **Usuarios**: 80% de la capacidad máxima encontrada (cap maxima 160 usuarios, se realizo prueba con 200 usuarios)
- **Duración**: 5 minutos
- **Objetivo**: Confirmar estabilidad del sistema bajo carga sostenida

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
