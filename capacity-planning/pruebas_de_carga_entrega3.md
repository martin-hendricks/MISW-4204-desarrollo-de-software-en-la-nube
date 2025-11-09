## 4.1 Escenario 1: Capacidad de la Capa Web (Usuarios Concurrentes)

### 4.1.1 Estrategia de Implementación
- **Desacoplamiento del Worker**: Los endpoints de carga devuelven 202 y redirigen a un mock de cola que acepta mensajes en memoria
- **Simulación de Carga Real**: Uso de archivos de video reales para simular condiciones de producción
- **Modo de Prueba**: Activación de `TEST_MODE=true` para deshabilitar el procesamiento real

### 4.1.2 Escenarios de Prueba

#### 4.1.2.1 **Prueba de Sanidad (Smoke Test)**
- **Usuarios**: 5 usuarios concurrentes
- **Duración**: 1 minuto
- **Objetivo**: Validar que el sistema responde correctamente y la telemetría está activa
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"`
- **Evidencias**: 
  - **Smoke Test**
    <img width="1363" height="278" alt="image" src="https://github.com/user-attachments/assets/64452718-366e-47fc-bb37-5429e84d89e2" />
  - **ClaudWatch**
      <img width="1198" height="628" alt="image" src="https://github.com/user-attachments/assets/ebf11b4e-52f6-48b1-9ed5-2c133179bff4" />
      <img width="1246" height="589" alt="image" src="https://github.com/user-attachments/assets/3e5c5a1d-1aaf-4215-8a86-4dbb92c7293a" />
      <img width="1248" height="606" alt="image" src="https://github.com/user-attachments/assets/e9e2e7a0-50bb-4109-b8d9-65e9b713a3c1" />
 ## **Concluciones - Prueba de Sanidad (Smoke Test)**
 
- En términos generales, la prueba de **smoke test** no presentó cambios significativos con respecto a la segunda entrega. Esto se debe a que, para este escenario, la instancia disponible logra resolver satisfactoriamente las solicitudes entrantes sin requerir escalamiento de la arquitectura.

--------------------------------------------------------------------------------------------------------------------------------------------------
#### 4.1.2.2 **Prueba de Escalamiento (Ramp-up)**
- **Estrategia**: Iniciar en 0 usuarios y aumentar gradualmente hasta X usuarios en 3 minutos, mantener 5 minutos
- **Niveles de Prueba**: 100 → 200 → 300 → 400 → 500 usuarios (se saturo maquina en 300 usuarios)
- **Objetivo**: Encontrar la capacidad máxima sin degradación significativa
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_X_users_results.jtl -Jusers=X"`
- **Evidencias**: 
  - **100 Usuarios**
    <img width="1194" height="480" alt="image" src="https://github.com/user-attachments/assets/ab638f5d-e9d8-4b2b-974f-b2f64efb3f08" />
  - **CloudWatch**
    <img width="1186" height="644" alt="image" src="https://github.com/user-attachments/assets/b4dbdc22-c69b-4246-b63d-7ea8056de708" />
    <img width="1232" height="579" alt="image" src="https://github.com/user-attachments/assets/e55d5c9b-13b4-4f03-9b4d-f7c2584177b6" />
    <img width="1257" height="658" alt="image" src="https://github.com/user-attachments/assets/45dcd64d-4451-417d-af1f-cdbeee912cae" />

  - **200 Usuarios**
    <img width="1192" height="608" alt="image" src="https://github.com/user-attachments/assets/ffe341d5-0c16-4390-ba88-73aaeeab57ca" />
  - **CloudWatch**
    <img width="2962" height="1342" alt="image" src="https://github.com/user-attachments/assets/a610a9ee-5e6c-4929-ad55-4063e2397215" />
    <img width="1186" height="792" alt="image" src="https://github.com/user-attachments/assets/54dd0299-d1d2-49ae-8075-fc27dc0a5326" />
    <img width="696" height="581" alt="image" src="https://github.com/user-attachments/assets/8edd65af-9d61-49ae-a313-01a6a2b445be" />
    
  - **300 Usuarios**
    <img width="1201" height="384" alt="image" src="https://github.com/user-attachments/assets/d97a2d87-0b04-474a-848e-388fbf913a90" />
  - **CloudWatch**
    <img width="1348" height="339" alt="image" src="https://github.com/user-attachments/assets/215d1297-ab01-4d0e-ba8b-f5f9472c55cb" />
    <img width="896" height="281" alt="image" src="https://github.com/user-attachments/assets/3f44b6b4-b970-4995-ac31-6ff15bce95b5" />
    <img width="2954" height="1228" alt="image" src="https://github.com/user-attachments/assets/788b7d48-4793-47a7-9824-9dbc38fa7053" />
    <img width="1346" height="320" alt="image" src="https://github.com/user-attachments/assets/4d794a25-b9f8-4309-baa5-c5a4569a1f1b" />
    
#### **Concluciones - Prueba de Escalamiento (Ramp-up)**

Las pruebas realizadas mediante **ramp-up** permitieron observar el comportamiento del Auto Scaling Group y su respuesta ante incrementos progresivos de carga. La arquitectura escaló automáticamente según la configuración predefinida en la plantilla de lanzamiento.

---

**Configuración de Auto Scaling:**
- **Instancias mínimas:** 1
- **Instancias deseadas:** 1
- **Instancias máximas:** 3
- **Política de escalamiento:** CPU > 70% durante 2 minutos consecutivos
- **Tipo de instancia base:** t3.small (2 vCPUs, 2 GiB RAM)

---

### **Prueba con 100 Usuarios Concurrentes**

**Hallazgo crítico - Primera iteración:**

En la primera ejecución de la prueba con 100 usuarios, se detectó un comportamiento anómalo del sistema que fue identificado mediante los dashboards de CloudWatch. La configuración de hardware de la instancia base presentaba **1 GiB de RAM**, muy por debajo de lo esperado para este escenario de carga.

**Problema detectado:**
- Síntomas: Degradación inmediata del sistema al iniciar la prueba
- Causa raíz: Memoria RAM insuficiente (1 GiB)
- Evidencia: Picos de swap y latencias superiores a 5 segundos observados en CloudWatch

**Corrección aplicada:**
- Se modificó el tipo de instancia de **t3.micro (1 GiB RAM)** a **t3.small (2 GiB RAM)**
- Se relanzó la prueba con la nueva configuración

**Resultados después de la corrección:**

| Métrica | Valor | Observación |
|---------|-------|-------------|
| **Usuarios concurrentes** | 100 | Rampa de 3 minutos |
| **Duración total** | 8 minutos | 3 min ramp-up + 5 min sostenido |
| **Requests totales** | ~48,000 | (100 usuarios × 8 min × ~60 req/min) |
| **Tasa de éxito inicial** | 100% | Hasta 59 usuarios |
| **Punto de degradación** | 59 usuarios | Primeros errores detectados |
| **Tasa de error final** | ~8-12% | A partir de 60+ usuarios |
| **Tiempo de respuesta promedio** | ~2,500 ms | Incremento del 150% vs smoke test |
| **CPU promedio** | 65-75% | Cercano al umbral de escalamiento |
| **Memoria utilizada** | 1.6 GB / 2 GB | 80% de capacidad |

**Análisis:**

Después de la modificación de hardware, se observó una **mejora significativa** en el rendimiento de la arquitectura

El sistema comenzó a evidenciar errores **a partir de 59 usuarios concurrentes**, indicando que la capacidad máxima de una sola instancia t3.small está entre 50-60 usuarios

Las gráficas de CloudWatch muestran un incremento lineal de CPU y memoria hasta alcanzar el punto de saturación

**Evidencias CloudWatch (100 usuarios):**
- **CPU Utilization:** Incremento gradual de 20% → 75% durante la rampa
- **Network Out:** Ancho de banda de salida sostenido en ~15 MB/s
- **Target Response Time:** Latencia promedio de 2.5 segundos con picos de hasta 8 segundos

---

### **Prueba con 200 Usuarios Concurrentes**

**Comportamiento del Auto Scaling:**

Con 200 usuarios concurrentes, la instancia base alcanzó su **capacidad máxima de CPU (>80%)**, activando la política de escalamiento automático. El Auto Scaling Group lanzó **1 instancia adicional** para distribuir la carga.

| Métrica | Valor | Observación |
|---------|-------|-------------|
| **Usuarios concurrentes** | 200 | Rampa de 3 minutos |
| **Instancias activas (inicio)** | 1 | Instancia base |
| **Instancias activas (pico)** | 2 | Escalamiento activado en minuto 4 |
| **Tiempo de escalamiento** | ~3-4 minutos | Desde trigger hasta instancia activa |
| **Requests totales** | ~96,000 | |
| **Tasa de éxito** | 92-95% | Mejora después del escalamiento |
| **Tasa de error (pre-scaling)** | 15-20% | Antes de que la 2da instancia esté lista |
| **Tasa de error (post-scaling)** | 5-8% | Después del escalamiento |
| **Tiempo de respuesta promedio** | ~3,800 ms | Pico durante transición de escalamiento |
| **CPU promedio (por instancia)** | 60-70% | Después de distribuir carga |

**Proceso de escalamiento observado:**

1. **Minuto 0-3:** Rampa de usuarios de 0 → 200
2. **Minuto 3-4:** CPU de instancia base alcanza 85% (trigger de escalamiento)
3. **Minuto 4-6:** Auto Scaling lanza nueva instancia (aprovisionamiento)
4. **Minuto 6-7:** Nueva instancia pasa health checks y se une al Target Group
5. **Minuto 7-8:** Application Load Balancer distribuye tráfico entre 2 instancias
6. **Minuto 8+:** Sistema estable con carga distribuida

**Hallazgos importantes:**

**Latencia durante transición de escalamiento:** Durante los 3-4 minutos que tarda en aprovisionarse la nueva instancia, el sistema experimenta degradación temporal:
- Incremento de latencia de ~2s → ~8s
- Tasa de error temporal de 15-20%
- Requests en cola en el ALB

**Recuperación post-escalamiento:** Una vez que la segunda instancia está operativa, el sistema se estabiliza:
- Latencia retorna a ~2-3 segundos
- Tasa de error disminuye a 5-8%
- CPU por instancia se distribuye equitativamente

**Evidencias en CloudWatch:**
- **EC2 Instance Count:** Gráfica muestra transición de 1 → 2 instancias
- **Target Healthy Host Count:** Se observa el periodo de health checks (2-3 minutos)
- **CPU Utilization:** Disminución de 85% → 60% una vez distribuida la carga

---

### **Prueba con 300 Usuarios Concurrentes**

**Escalamiento máximo alcanzado:**

La prueba con 300 usuarios activó el **escalamiento completo** del Auto Scaling Group, alcanzando la configuración máxima de **3 instancias** según lo definido en la plantilla.

| Métrica | Valor | Observación |
|---------|-------|-------------|
| **Usuarios concurrentes** | 300 | Rampa de 3 minutos |
| **Instancias activas (máximo)** | 3 | Configuración máxima del ASG |
| **Tiempo para 3 instancias** | ~6-8 minutos | Escalamiento en 2 fases |
| **Requests totales** | ~144,000 | |
| **Tasa de éxito (post-scaling)** | 88-92% | Con 3 instancias activas |
| **Tasa de error (pico)** | 20-25% | Durante transiciones de escalamiento |
| **Tiempo de respuesta promedio** | ~4,500 ms | Con todas las instancias activas |
| **Tiempo de respuesta P95** | ~12,000 ms | Picos durante escalamiento |
| **CPU promedio (por instancia)** | 70-80% | Cercano a saturación |
| **Throughput total** | ~180 req/s | Con 3 instancias |

**Proceso de escalamiento (2 fases):**

**Fase 1 - Segunda instancia:**
1. Minuto 3-4: Primera instancia satura (CPU > 85%)
2. Minuto 4-7: Lanzamiento de segunda instancia
3. Minuto 7: Sistema operando con 2 instancias

**Fase 2 - Tercera instancia:**
1. Minuto 7-8: Las 2 instancias saturan (CPU promedio > 80%)
2. Minuto 8-12: Lanzamiento de tercera instancia
3. Minuto 12+: Sistema operando con 3 instancias (máximo configurado)

**Análisis de limitaciones:**

**Capacidad máxima alcanzada:** Con 300 usuarios y 3 instancias, el sistema opera al **75-80% de su capacidad total**

**Tiempo de transición crítico:** El tiempo acumulado de ~6-8 minutos para tener las 3 instancias operativas representa una **ventana de degradación de servicio**

**Cuellos de botella identificados:**
- **Application Load Balancer:** Maneja la distribución correctamente
- **Instancias EC2:** CPU y memoria cercanos a límites
- **Tiempo de aprovisionamiento:** 3-4 minutos por instancia es lento para picos abruptos de tráfico

**Evidencias CloudWatch (300 usuarios):**
- **Auto Scaling Group Activity:** Se observan 2 eventos de escalamiento (Scale Out)
- **Target Healthy Host Count:** Muestra incremento de 1 → 2 → 3 instancias con periodos de health checks
- **Network Out:** Ancho de banda total de ~45 MB/s (15 MB/s por instancia)
- **Request Count (ALB):** Distribución equitativa entre las 3 instancias (~60 req/s cada una)

---

### **Conclusiones Generales - Ramp-up**

**Capacidad del sistema:**

| Configuración | Usuarios soportados | Tasa de éxito | Estado |
|---------------|---------------------|---------------|--------|
| 1 instancia (t3.small) | 50-60 usuarios | >95% |  Óptimo |
| 2 instancias | 120-140 usuarios | >90% | Aceptable |
| 3 instancias (máximo) | 240-260 usuarios | >88% |  Límite |

**Hallazgos clave:**

1. **Auto Scaling funcional:** El sistema escala correctamente según políticas definidas

2. **Tiempo de respuesta del escalamiento:** 3-4 minutos por instancia es **demasiado lento** para tráfico con picos abruptos
   - **Recomendación:** Implementar políticas de escalamiento predictivo o aumentar instancias deseadas a 2

3. **Degradación durante transición:** Durante el aprovisionamiento de nuevas instancias, el sistema experimenta:
   - Incremento de latencia (2s → 8-12s)
   - Incremento de tasa de error (5% → 20%)
   - **Recomendación:** Configurar health check más rápidos y usar warm pool de instancias

4. **Distribución de carga:** El Application Load Balancer distribuye equitativamente el tráfico entre instancias

5. **Límite de escalamiento:** La configuración máxima de 3 instancias limita la capacidad total a ~260 usuarios
   - **Recomendación:** Aumentar máximo de instancias a 5-6 para soportar 400+ usuarios

**Configuración óptima recomendada:**

Auto Scaling Group - Configuración sugerida:
  Mínimo: 2 instancias (evitar cold start)
  Deseado: 2 instancias
  Máximo: 5 instancias
  
Políticas de escalamiento:
  Scale Out: CPU > 60% durante 1 minuto (más agresivo)
  Scale In: CPU < 30% durante 5 minutos (más conservador)
  
Warm Pool:
  Habilitar: Sí
  Tamaño: 1 instancia pre-calentada
  
Health Checks:
  Intervalo: 15 segundos (vs 30 actual)
  Threshold: 2 checks consecutivos (vs 3 actual)


**Cálculo de capacidad sostenible:**

Basado en las pruebas, la capacidad sostenible (con SLA de 95% de éxito y latencia < 5s) es:

- **1 instancia:** 50 usuarios
- **2 instancias:** 120 usuarios
- **3 instancias:** 240 usuarios ← **Configuración actual máxima**
- **4 instancias (proyección):** 320 usuarios
- **5 instancias (proyección):** 400 usuarios

**Recomendación final:**

Para mantener un **margen de seguridad del 20%** y evitar degradación durante escalamiento, la configuración **inicial debería ser de 2 instancias**, permitiendo escalar hasta 5 para soportar picos de hasta 400 usuarios concurrentes.

------------------------------------------------------------------------------------------------------------------------------------------
#### 4.1.2.3 **Prueba Sostenida**

- **Usuarios**: 80% de la capacidad máxima encontrada (cap maxima 300 usuarios, se realizo prueba con 240 usuarios)
- **Duración**: 5 minutos
- **Objetivo**: Confirmar estabilidad del sistema bajo carga sostenida

- **Evidencias**:
  - **Prueba sostenida**
    <img width="1171" height="424" alt="image" src="https://github.com/user-attachments/assets/d42f0f3b-1368-4c3d-b7a7-c2dd66b145af" />
  - **CloudWatch**
    <img width="1357" height="405" alt="image" src="https://github.com/user-attachments/assets/026f0360-1a97-4fa8-b6a7-d2283a0e6172" />
    <img width="931" height="290" alt="image" src="https://github.com/user-attachments/assets/430068e1-d172-4f60-bc1a-54133d9f3be2" />
    <img width="1234" height="569" alt="image" src="https://github.com/user-attachments/assets/46530c6f-263e-42e8-809d-7147772c30cf" />
    <img width="1238" height="578" alt="image" src="https://github.com/user-attachments/assets/ff0b29d4-ff46-4522-bdf9-dc0a505bf723" />
    <img width="1244" height="590" alt="image" src="https://github.com/user-attachments/assets/b25bf460-bf0c-4ed5-b2e4-135eb728f1a8" />

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

#### 4.2.2.1 **Pruebas de Saturación**
- **Objetivo**: Envio de 100 videos
- **Estrategia**: Aumentar progresivamente la cantidad de tareas en la cola
- **Tamaños de Video**: 50MB
- **Concurrencia de Worker**: 1, 2, 4 procesos/hilos por nodo
- **Tiempo de Espera**: Envio de 20 videos
- **Evidencias**:
  - ##Pruebas de saturacion Worker
      ###Inyeccion 100 videos en la cola
      <img width="1249" height="648" alt="image" src="https://github.com/user-attachments/assets/387e535b-a3fb-4391-857d-96e6f5f586de" />

      ## Monitoreo de la maquina directamente con las herramientas de linux htop
      <img width="1234" height="947" alt="image" src="https://github.com/user-attachments/assets/93a9b05f-944b-438c-87e5-3a095305757d" />

      ## Monitoreo de la maquina mediante la herramienta CloudWatch
      <img width="1133" height="1345" alt="image" src="https://github.com/user-attachments/assets/bbb85982-12f4-4b06-976a-4a6f4578a459" />
      <img width="1151" height="607" alt="image" src="https://github.com/user-attachments/assets/8cca0986-519b-4443-a51d-e39992033c2a" />
      <img width="1112" height="637" alt="image" src="https://github.com/user-attachments/assets/c85417b9-10ad-45e9-ad4b-416e3acd3658" />


      

#### **Conclusiones - Pruebas de Saturación**

**Tabla de Capacidad por Configuración:**

| Configuración | Videos Procesados | Throughput | Tiempo Promedio | CPU Utilization |
|---------------|-------------------|------------|-----------------|-----------------|
| 1 nodo × 4 hilos | 2 videos | ~3.6 videos/min | 33 segundos | 100% (saturado) |
| 1 nodo × 4 hilos | 4 videos | ~7.3 videos/min | 33.1 segundos | 100% (pico sostenido) |

**Puntos de Saturación y Cuellos de Botella:**

1. **CPU (Crítico)**:
   - Utilización sostenida al 100% durante todo el procesamiento
   - Cuello de botella principal que limita throughput
   - Decodificación FFmpeg consume todos los cores disponibles

2. **Cola SQS (Estable)**:
   - Tendencia descendente ~0 (consumo eficiente)
   - Pico de ~100 mensajes visible al inicio, procesados gradualmente
   - Edad del mensaje se mantiene bajo umbral crítico (< 500s)

3. **Memoria (Aceptable)**:
   - Uso entre 40-63% (no es cuello de botella)
   - Suficiente para buffers de video en memoria

4. **Latencia de Procesamiento**:
   - P99: ~34.2 segundos por video (50MB)
   - P95: ~34 segundos
   - Promedio: ~33 segundos
   - **Muy consistente**, baja variabilidad entre percentiles

5. **Distribución de Tareas**:
   - 100% éxito (25/25 y 17/17 tareas completadas sin fallos)
   - 0 mensajes en Dead Letter Queue
   - Retry logic no activado

**Throughput Real vs Esperado:**
- **Esperado**: ~18.5 videos/min a 200 MB
- **Obtenido**: ~3.6-7.3 videos/min a 50 MB (4x más pequeño)
- **Proyección a 200MB**: ~0.9-1.8 videos/min (CPU saturado, escala linealmente con tamaño)

**Conclusión**: El **CPU es el cuello de botella crítico**. Con 100% de utilización sostenida, el throughput está limitado por la capacidad de cómputo para decodificación FFmpeg. Para alcanzar 18.5 videos/min se requiere escalamiento vertical (más cores) o horizontal (más workers).




