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

  - [Grafana](https://github.com/user-attachments/assets/20ffcc92-7fc4-4726-b8c5-63acb9167efd)
    - <img width="1385" height="1141" alt="rtamup-100-grafana" src="https://github.com/user-attachments/assets/20ffcc92-7fc4-4726-b8c5-63acb9167efd" />

  - [Grafana-2](https://github.com/user-attachments/assets/20ffcc92-7fc4-4726-b8c5-63acb9167efd](https://github.com/user-attachments/assets/0b53584c-f7c9-4d2c-be28-bff19e6fdf7c))
<img width="1385" height="1141" alt="rtamup-100-grafana-2" src="https://github.com/user-attachments/assets/0b53584c-f7c9-4d2c-be28-bff19e6fdf7c" />
  - [NFS](https://github.com/user-attachments/assets/8e8578f4-bb43-4f4c-b41d-6ecae8652c2e)
    <img width="599" height="214" alt="rtamup-100-nfs" src="https://github.com/user-attachments/assets/8e8578f4-bb43-4f4c-b41d-6ecae8652c2e" />

  - [200 Usuarios](https://github.com/user-attachments/assets/fc025045-8940-4984-ab8f-77cc94acd700)
    
    <img width="2996" height="1182" alt="rtamup-200-logs" src="https://github.com/user-attachments/assets/fc025045-8940-4984-ab8f-77cc94acd700" />

  - [Grafana](https://github.com/user-attachments/assets/8b9b63db-dfba-4381-b1e5-240b760895c3)
   <img width="1385" height="1141" alt="rtamup-200-grafana" src="https://github.com/user-attachments/assets/8b9b63db-dfba-4381-b1e5-240b760895c3" />

  - [Grafana-2](https://github.com/user-attachments/assets/c5acf368-12fe-4b56-be2a-fbc5eea3aa25)

   <img width="1385" height="1141" alt="rtamup-200-grafana-2" src="https://github.com/user-attachments/assets/c5acf368-12fe-4b56-be2a-fbc5eea3aa25" />
   
  - [NFS](https://github.com/user-attachments/assets/4703dae9-18a8-4a4c-87a1-2fc05fd19291)
    <img width="2996" height="1182" alt="rtamup-200-logs" src="https://github.com/user-attachments/assets/4703dae9-18a8-4a4c-87a1-2fc05fd19291" />

  - [300 Usuarios](https://github.com/user-attachments/assets/aedd275f-76fb-49f9-a1ce-b3a9e412a578)
    <img width="2992" height="854" alt="image (11)" src="https://github.com/user-attachments/assets/aedd275f-76fb-49f9-a1ce-b3a9e412a578" />

  - [Grafana](https://github.com/user-attachments/assets/e4dddd04-c77d-4e6e-ab9a-063c27e04e6d)
    <img width="1385" height="1141" alt="rtamup-300-grafana" src="https://github.com/user-attachments/assets/e4dddd04-c77d-4e6e-ab9a-063c27e04e6d" />

**Prueba Sostenida**

- **Usuarios**: 80% de la capacidad máxima encontrada (cap maxima 175 usuarios, se realizo prueba con 219 usuarios)
- **Duración**: 5 minutos
- **Objetivo**: Confirmar estabilidad del sistema bajo carga sostenida

- **Evidencias**:
  - [Prueba sostenida](https://github.com/user-attachments/assets/1aa8e913-d210-40fc-be2f-6a449c48af45)
  - <img width="3052" height="844" alt="image (15)" src="https://github.com/user-attachments/assets/1aa8e913-d210-40fc-be2f-6a449c48af45" />

  - [Grafana](https://github.com/user-attachments/assets/a6eb91e7-e343-4a72-8bdb-7b6de3755199)
  - <img width="1385" height="1141" alt="screencapture-ec2-54-147-163-25-compute-1-amazonaws-3000-d-backend-api-perf-backend-api-performance-2025-10-26-23_21_06" src="https://github.com/user-attachments/assets/a6eb91e7-e343-4a72-8bdb-7b6de3755199" />

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
- **Objetivo**: Envio de 20 videos
- **Estrategia**: Aumentar progresivamente la cantidad de tareas en la cola
- **Comandos**:
  ```bash
  # Carga en la instancia de AWS
  docker exec producer python producer.py --num-videos 20 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
  ```
#### 4.2.3 Configuraciones de Prueba
- **Tamaños de Video**: 50MB
- **Concurrencia de Worker**: 1, 2, 4 procesos/hilos por nodo
- **Tiempo de Espera**: Envio de 20 videos
- **Evidencias**:
  - [Pruebas de saturacion Worker]()
 <img width="2144" height="1106" alt="image (17)" src="https://github.com/user-attachments/assets/e96d591e-13bd-442a-9ecb-9a8edddfaeab" />
<img width="2144" height="1106" alt="image (18)" src="https://github.com/user-attachments/assets/7aaf9ab2-393a-4bf6-99ee-cfe968c0bdaf" />

 # Concluciones

  - Se evidencio que la capacidad de 50 Gigas para la instacia del NFS se vio superada en la prueba de saturacion del worker, esto debido al tamaño de cada video, esto no solo afecto a la instacia del worker si no que afecto la estabilidad de todo el sistema.

  <img width="650" height="412" alt="image (12)" src="https://github.com/user-attachments/assets/6543a9e9-0f1c-4872-ae44-8b9a6b144889" />

  <img width="1265" height="816" alt="image (13)" src="https://github.com/user-attachments/assets/bad4988a-ef5a-4001-a178-fa5d42014c9c" />

- Se evidencia que no solo se debe levantar la instancia con las configuraciones de memoria si no adicional se debe otorgar memoria al Docker para si ejecucion, debido a que se alcanbaba muy rapido y presentabla problemas.

<img width="1421" height="230" alt="image (14)" src="https://github.com/user-attachments/assets/66233f43-500d-4b1a-99a0-355a6dabecb4" />

-En las pruebas de Jmeter se evidencio inastibilidad del sistema en la ejecucion de 300 usuario, esto debido a la cantidad de trafico que estaba recibiendo el backend.

-Em la prueba sostenida evidenciamos que llevamos las maquinas al limite pewro sin generar error
  
