## 4. Escenarios de Prueba

## 4.1 Escenario 1: Capacidad de la Capa Web (Usuarios Concurrentes)

### 4.1.1 Estrategia de Implementación
- **Desacoplamiento del Worker**: Los endpoints de carga devuelven 202 y redirigen a un mock de cola que acepta mensajes en memoria
- **Simulación de Carga Real**: Uso de archivos de video reales para simular condiciones de producción
- **Modo de Prueba**: Activación de `TEST_MODE=true` para deshabilitar el procesamiento real

### 4.1.2 Escenarios de Prueba

#### **Prueba de Sanidad (Smoke Test)**
- **Usuarios**: 5 usuarios concurrentes
- **Duración**: 1 minuto
- **Objetivo**: Validar que el sistema responde correctamente y la telemetría está activa
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"`
- **Evidencias**: 
  - Smoke Test
  - <img width="1854" height="372" alt="smocke-test-5 usuario-logs" src="" />
  - ClaudWatch
<img width="1385" height="1141" alt="smocke-test-5 usuario-grafa" src="" />

 #### **Concluciones - Prueba de Sanidad (Smoke Test)**

#### **Prueba de Escalamiento (Ramp-up)**
- **Estrategia**: Iniciar en 0 usuarios y aumentar gradualmente hasta X usuarios en 3 minutos, mantener 5 minutos
- **Niveles de Prueba**: 100 → 200 → 300 → 400 → 500 usuarios (se saturo maquina en 300 usuarios)
- **Objetivo**: Encontrar la capacidad máxima sin degradación significativa
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_X_users_results.jtl -Jusers=X"`
- **Evidencias**: 
  - 100 Usuarios
  - <img width="3110" height="1132" alt="rtamup-100-log" src="" />
  - CloudWatch
    - <img width="1385" height="1141" alt="rtamup-100-grafana" src="" />
  - 200 Usuarios
  - <img width="3110" height="1132" alt="rtamup-100-log" src="" />
   - CloudWatch
    - <img width="1385" height="1141" alt="rtamup-100-grafana" src="" />
  - 300 Usuarios
  - <img width="3110" height="1132" alt="rtamup-100-log" src="" />
  - CloudWatch
    - <img width="1385" height="1141" alt="rtamup-100-grafana" src="" />

#### **Concluciones - Prueba de Escalamiento (Ramp-up)**

#### **Prueba Sostenida**

- **Usuarios**: 80% de la capacidad máxima encontrada (cap maxima 300 usuarios, se realizo prueba con 240 usuarios)
- **Duración**: 5 minutos
- **Objetivo**: Confirmar estabilidad del sistema bajo carga sostenida

- **Evidencias**:
  - Prueba sostenida
  - <img width="3052" height="844" alt="image (15)" src="" />

  - CloudWatch
  - <img width="1385" height="1141" alt="image (15)" src="" />

#### **Concluciones - Prueba Sostenida**

#### 4.1.3 Endpoints a Probar
- `POST /auth/login` - Autenticación
- `POST /videos/upload` - Subida de videos
- `GET /videos` - Lista de videos del usuario
- `GET /public/videos` - Videos públicos
- `POST /public/videos/{video_id}/vote` - Votación

## 4.2 Escenario 2: Rendimiento de la Capa Worker (Videos/Minuto)

### 4.2.1 Estrategia de Implementación
- **Bypass de la Web**: Inyección directa de mensajes en la cola de AWS SQS
- **Payloads Realistas**: Uso de archivos de video de diferentes tamaños (50MB)
- **Configuraciones Variables**: 1, 2, 4 procesos/hilos por nodo

### 4.2.2 Escenarios de Prueba

#### **Pruebas de Saturación**
- **Objetivo**: Envio de 20 videos
- **Estrategia**: Aumentar progresivamente la cantidad de tareas en la cola

### 4.2.3 Configuraciones de Prueba
- **Tamaños de Video**: 50MB
- **Concurrencia de Worker**: 1, 2, 4 procesos/hilos por nodo
- **Tiempo de Espera**: Envio de 20 videos
- **Evidencias**:
  - Pruebas de saturacion Worker
 <img width="2144" height="1106" alt="image (17)" src="" />

#### **Concluciones - Pruebas de Saturación**





