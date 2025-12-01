
# Pruebas de Carga - Entrega 5

## 1 Escenario 1: Capacidad de la Capa Web (Usuarios Concurrentes)

### 1.1 Escenarios de Prueba

#### 1.2.1 **Prueba de Sanidad (Smoke Test)**
- **Usuarios**: 5 usuarios concurrentes
- **Duración**: 1 minuto
- **Objetivo**: Validar que el sistema responde correctamente y la telemetría está activa
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"`
- **Evidencias**: 

<img width="1237" height="648" alt="image (34)" src="https://github.com/user-attachments/assets/edbeaa66-7000-4cdc-93c3-627a3d790233" />
<img width="1241" height="605" alt="image (35)" src="https://github.com/user-attachments/assets/aab90f33-ba3c-4f05-9d7a-7b94b589d0f8" />
<img width="1252" height="605" alt="image (36)" src="https://github.com/user-attachments/assets/87ceef95-075f-4625-85d3-06c983459608" />
<img width="1237" height="653" alt="image (37)" src="https://github.com/user-attachments/assets/d60f8876-4e0c-4794-89ca-c8e918e30ed7" />
<img width="1243" height="647" alt="image (38)" src="https://github.com/user-attachments/assets/e2b4fa0d-2b2b-483c-af4d-81589eb3759a" />
<img width="1255" height="657" alt="image (39)" src="https://github.com/user-attachments/assets/1f371dca-ca2d-454a-b70b-1123eb5b39b9" />

Métricas Observadas
- **Duración total de la prueba**: Aproximadamente 15 minutos (16:15 - 16:30)
- **Requests totales procesados**: 423 requests
- **Throughput observado**:
- **Pico máximo**: 417 requests/minuto (16:40 UTC)
- **Promedio durante carga activa**: ~300-400 requests/minuto
- **Latencia p95**: 575.2 milisegundos (575ms) al final de la prueba
- **Patrón de latencia**: Crecimiento lineal desde ~0ms hasta 575ms durante los 15 minutos
- **Tasa de éxito**:
  - **Status 201 (Created)**: 419 requests (99.05%)
  - **Status 200 (OK)**: 4 requests (0.95%)
- **CPU**: Pico máximo 22.3%, promedio ~22.4% (muy baja)
- **Memoria**: Estable en 47.6% promedio, mínimo 47.65%
- **Comportamiento de carga**:
- **Rampa gradual** de 0 a 417 requests/minuto en ~13 minutos

 ## **Conclusiónes - Prueba de Sanidad (Smoke Test)**
 
 El sistema backend demostró capacidad para manejar 423 requests con una tasa de éxito del 99.05% (419 requests exitosos con status 201). El patrón de carga gradual permitió observar el comportamiento del sistema bajo presión incremental, alcanzando un pico sostenido de 417 requests/minuto. 
 
 La latencia p95 de 575ms al final de la prueba, con un patrón de crecimiento lineal desde 0ms, indica que el sistema experimenta degradación progresiva del tiempo de respuesta a medida que aumenta la carga acumulada. Este comportamiento sugiere posible acumulación de tareas en cola o procesamiento secuencial que impacta los tiempos de respuesta bajo carga sostenida.

La utilización de CPU extremadamente baja (22.3% máximo) contrasta significativamente con las pruebas de procesamiento de video (99.96%), indicando que el backend API no está limitado por CPU. La memoria estable en 47.6% sugiere un consumo constante sin fugas evidentes. Esta sub-utilización de recursos computacionales con latencias crecientes apunta a que el cuello de botella probablemente reside en operaciones de I/O (base de datos, almacenamiento, red) o en la arquitectura de procesamiento de requests.
--------------------------------------------------------------------------------------------------------------------------------------------------
#### 1.2.2 **Prueba de Escalamiento (Ramp-up)**
- **Estrategia**: Iniciar en 0 usuarios y aumentar gradualmente hasta X usuarios en 3 minutos, mantener 5 minutos
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_X_users_results.jtl -Jusers=X"`
- **Evidencias**: 
  - **100 Usuarios**
    
<img width="1245" height="655" alt="image (34)" src="https://github.com/user-attachments/assets/4b9c83f3-743b-49a4-81a5-cbeb13bab3d1" />
<img width="1244" height="641" alt="image (35)" src="https://github.com/user-attachments/assets/c874fb54-2b21-48ad-b3d4-03e9ce30bdc7" />
<img width="1251" height="649" alt="image (36)" src="https://github.com/user-attachments/assets/cd59d90c-ef45-49c0-8187-244625676b28" />
<img width="1254" height="608" alt="image (37)" src="https://github.com/user-attachments/assets/abd3ca28-8ecc-4096-9c11-c704ed93473d" />
<img width="1244" height="648" alt="image (38)" src="https://github.com/user-attachments/assets/b278d3cc-f27d-4d4f-8297-ce4de971bc88" />
<img width="1255" height="656" alt="image (39)" src="https://github.com/user-attachments/assets/543fd46f-0876-462a-854a-968e9ccbc53b" />
<img width="1251" height="649" alt="image (40)" src="https://github.com/user-attachments/assets/4e059948-5f8b-4db6-8dfb-6572397b8ac7" />

  - **200 Usuarios**
    
<img width="1252" height="652" alt="image (34)" src="https://github.com/user-attachments/assets/97635e80-1886-48ad-bbbd-4690da7fc103" />
<img width="1250" height="655" alt="image (35)" src="https://github.com/user-attachments/assets/c16b62f9-58ff-4737-91c8-d12a8d25cef3" />
<img width="1245" height="653" alt="image (36)" src="https://github.com/user-attachments/assets/bfa4ba77-1f90-496d-9f85-0f9e88e1d7de" />
<img width="1251" height="660" alt="image (37)" src="https://github.com/user-attachments/assets/54ac3d75-1a00-4918-9fa5-6e29f4738657" />
<img width="1251" height="652" alt="image (38)" src="https://github.com/user-attachments/assets/512d9ab5-0f04-4aed-9926-6dbdbadeb296" />

  - **400 Usuarios**

<img width="2036" height="580" alt="image (34)" src="https://github.com/user-attachments/assets/f9bbae9b-359f-4bfb-8657-20c1d8897e3e" />
<img width="2040" height="584" alt="image (35)" src="https://github.com/user-attachments/assets/7be3361e-5974-4b0a-9941-1136a4d9720f" />
<img width="2046" height="742" alt="image (36)" src="https://github.com/user-attachments/assets/e69ebecc-e519-4cf6-91cf-92022c9ed9ed" />
<img width="2042" height="750" alt="image (37)" src="https://github.com/user-attachments/assets/cb2f9fee-6e3f-4ff5-9189-c93fc0145eeb" />
<img width="1692" height="666" alt="image (38)" src="https://github.com/user-attachments/assets/56d84666-9c26-42ef-a8a2-f6baaa6f9d18" />
<img width="1686" height="660" alt="image (39)" src="https://github.com/user-attachments/assets/29c06d8e-8bd8-4370-b019-d6d4d14d6600" />

 - **1500 Usuarios**
 - 
<img width="1517" height="667" alt="image (34)" src="https://github.com/user-attachments/assets/0d3b4f67-bed2-4d6b-bade-34ce11eceaeb" />
<img width="2040" height="580" alt="image (35)" src="https://github.com/user-attachments/assets/d2861914-f496-485d-b49c-7dbad2fcd2a4" />
<img width="2052" height="680" alt="image (36)" src="https://github.com/user-attachments/assets/2ee6d577-ecfa-4db1-a238-4fb8c6cc2d92" />
<img width="2056" height="764" alt="image (37)" src="https://github.com/user-attachments/assets/2e055a3f-f872-4687-8cf7-855572b1d604" />
<img width="2048" height="614" alt="image (38)" src="https://github.com/user-attachments/assets/71f49113-71e7-4211-a6e7-455ca403e988" />
<img width="1688" height="658" alt="image (39)" src="https://github.com/user-attachments/assets/b0052538-57f8-448f-a83c-d08dddfefab5" />
<img width="1692" height="656" alt="image (40)" src="https://github.com/user-attachments/assets/4c5a3e0e-54d2-4789-b777-8e53fa302efa" />


## **Conclusiónes - Prueba de Escalamiento (Ramp-up)**


------------------------------------------------------------------------------------------------------------------------------------------
#### 1.2.3 **Prueba Sostenida**

- **Usuarios**: Se calcula que de 1500 usuarios de la prueba ramp-up el 80% de la capacidad son 1200 usuarios por lo cual procedemos a realizar la prueba sostenida con esta cantidad de usuarios
- **Duración**: 5 minutos
- **Objetivo**: Confirmar estabilidad del sistema bajo carga sostenida

- **Evidencias**:



## **Conclusiónes - Prueba Sostenida**



# Escenario 2: Rendimiento de la Capa Worker 

**Configuración de la Política:**
- **Nombre**: worker-cpu-scale-up
- **Tipo de política**: Escalado de seguimiento de destino
- **Estado**: Habilitado
- **Métrica objetivo**: Utilización promedio de la CPU
- **Acción de escalado**: Agregar o eliminar unidades de capacidad según sea necesario
- **Tiempo de preparación**: 60 segundos para que las instancias se incluyan en la métrica
- **Escalado descendente**: Habilitado


## Pruebas Sostenidas (Medir Throughput Estable)

### Objetivo
Medir cuántos videos por minuto procesa el sistema bajo una carga constante y estable, sin que la cola de tareas crezca indefinidamente.

### 1.1 Prueba Básica - 20 Videos (50MB)
```bash
docker exec producer python producer.py --num-videos 20 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Evidencias:**
- Capturas del sistema durante la prueba
<img width="1237" height="656" alt="image (34)" src="https://github.com/user-attachments/assets/36a8084e-09cc-427e-9c28-3db645c63f43" />
<img width="1230" height="598" alt="image (35)" src="https://github.com/user-attachments/assets/d981da60-9328-452a-8407-67fc3bd34d7e" />
<img width="1241" height="610" alt="image (36)" src="https://github.com/user-attachments/assets/e65f5bb7-835f-458b-bdba-76c625db702a" />
<img width="1248" height="582" alt="image (37)" src="https://github.com/user-attachments/assets/62ba0f3a-4d44-47a0-945e-7a157171807c" />
<img width="1222" height="282" alt="image (38)" src="https://github.com/user-attachments/assets/21705c02-29c7-426c-af6a-1a824d2bf4f0" />


**Datos de Entrega 4:**
- **Tiempo de ejecución**: Aproximadamente 8 minutos (18:13 - 18:21)
- **Throughput observado**: 2.5 videos por minuto
- **Estado del sistema**: Procesamiento estable sin degradación
- **Utilización de CPU**: Mantiene niveles moderados según CloudWatch
- **Memoria**: Sin indicios de saturación
- **Comportamiento de la cola**: Procesamiento lineal sin acumulación
- **Métricas de throughput**: 2.5 videos/minuto - 125 MB/minuto procesados

**Datos de Entrega Actual(5):**
- **Tiempo de ejecución**: Aproximadamente 13 minutos (03:58 - 04:16)
- **Throughput observado**: ~0.8 videos por minuto (11 videos procesados)
- **Estado del sistema**: Procesamiento con picos de carga significativos
- **Utilización de CPU**: Picos de hasta 100% (p99) con promedio ~95% durante carga
- **Memoria**: Incremento de ~28% a ~42% durante procesamiento, sin saturación
- **Comportamiento de la cola**: Crecimiento hasta 11 tareas, luego descenso abrupto a 2
- **VideoFileSize**: Procesamiento promedio de 16M/M

## Conclusión:
 El sistema muestra degradación de rendimiento comparado con la prueba anterior:
- **Throughput reducido**: De 2.5 a 0.8 videos/minuto (68% menos eficiencia)
- **CPU saturada**: Alcanza 100% vs niveles moderados previos
- **Procesamiento inconsistente**: Duración variable (20-150 seg) indica sobrecarga
- **Bottleneck identificado**: La CPU es el limitante principal del sistema
- **Leciones Aprendidas**: El Auto Scaling Group debería ser configurado en  CPU > 70% sostenido para que pueda escalar para distribuir la carga cuando CPU > 70% sostenido.

## 1.2 Pruebas de 50 Videos (50MB)

```bash
docker exec producer python producer.py --num-videos 50 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Evidencias:**
- Capturas del sistema durante la prueba

<img width="1231" height="585" alt="image (34)" src="https://github.com/user-attachments/assets/9ade04ad-9cf7-4089-bff7-5d3252ffff5f" />
<img width="1241" height="569" alt="image (35)" src="https://github.com/user-attachments/assets/6eea0b1c-f394-40ec-b06e-f365e43cba7d" />
<img width="1243" height="598" alt="image (36)" src="https://github.com/user-attachments/assets/052ddc22-3e01-4a45-bf68-ed04698fa86d" />
<img width="1224" height="601" alt="image (37)" src="https://github.com/user-attachments/assets/cbf31934-f99f-4f9f-9984-0e82bc4ca059" />
<img width="1224" height="581" alt="image (38)" src="https://github.com/user-attachments/assets/a260eccf-985c-45c1-8712-46e8f1de4c90" />
<img width="1198" height="263" alt="image (39)" src="https://github.com/user-attachments/assets/b153d2de-d480-494f-96b6-ddb820cd127c" />

**Resultados Entrega 4:**

- **Tiempo de ejecución**: Aproximadamente 6 minutos (18:58 - 19:04)
- **Throughput observado**: 8.3 videos por minuto
- **Mejora en eficiencia**: Mayor throughput por unidad de tiempo
- **Estado de la cola de tareas**: Procesamiento eficiente sin acumulación
- **Métricas de CPU y memoria**: Utilización moderada según monitoreo EC2
- **Estado de la cola de tareas**: Cola procesada completamente sin retrasos
- **Métricas de CPU y memoria**: CPU ~30-40%, Memoria estable
- **Tiempo de respuesta promedio**: ~7.2 segundos por video

**Resultados Entrega Actual (5):**

- **Tiempo de ejecución**: Aproximadamente 6 minutos (04:37 - 04:43)
- **Throughput observado**: ~2 videos por minuto (12 videos procesados en 6 min)
- **Estado del sistema**: Procesamiento con alta carga sostenida
- **Utilización de CPU**: Sostenida al 95-100% (máximo) durante 04:37-04:42, luego caída abrupta
- **Memoria**: Incremento gradual de ~8% a ~26%, manteniéndose estable en 15-25%
- **Comportamiento de la cola**: Crecimiento lineal de 8 a 12 tareas, sin procesamiento durante acumulación
- **VideoFileSize**: Archivos promedio de 200M procesados por minuto
- **Duración de procesamiento**: Estable en ~30 segundos (p95) durante carga activa

## Conclusión:
El sistema muestra mejor rendimiento comparado con la prueba de la entrega anterior esto debido al ajuste realizado de Auto Scaling Group configurado en  CPU > 70% sostenido :
- **Mejora de rendimiento**: 2.5× más throughput en Prueba 2
- **Procesamiento más predecible**: Duración estable (30s) vs variable (20-150s)
- **Mejor uso de memoria**: 26% vs 42% máximo
- **CPU saturada en ambas**: Bottleneck confirmado

### 1.3 Prueba con Video Grande - 10 Videos (100MB)
```bash
docker exec producer python producer.py --num-videos 10 --video-file ./assets/dummy_file_100mb.mp4 --no-wait
```

**Evidencias:**
- Capturas del sistema durante la prueba

<img width="1246" height="597" alt="image (34)" src="https://github.com/user-attachments/assets/986b0392-a4f6-4a25-8da5-d9b20ef2df35" />
<img width="1266" height="654" alt="image (35)" src="https://github.com/user-attachments/assets/5e724e6b-e6a0-4fde-8928-8efa6c5f5fb8" />
<img width="1730" height="668" alt="image (36)" src="https://github.com/user-attachments/assets/3c0bc82f-e6d5-4229-9256-453358028fe0" />
<img width="1734" height="668" alt="image (37)" src="https://github.com/user-attachments/assets/939084a2-f4e3-45f2-a107-52e76bba8256" />
<img width="1740" height="670" alt="image (38)" src="https://github.com/user-attachments/assets/a8dcd8c9-6239-40a3-ad7b-178df8720cae" />
<img width="1724" height="660" alt="image (39)" src="https://github.com/user-attachments/assets/04d81479-a586-4fc0-942d-7d92e65b5a1b" />
<img width="3992" height="1452" alt="image (40)" src="https://github.com/user-attachments/assets/807e24e7-7783-496e-9787-86824b52c550" />
<img width="1238" height="652" alt="image (41)" src="https://github.com/user-attachments/assets/acebd93e-32de-455f-8016-68e09e958659" />
<img width="1222" height="268" alt="image (42)" src="https://github.com/user-attachments/assets/7030f9bc-ecbe-4698-b868-dcc6ad92d9ac" />

**Resultados Entrega 4 :**
- **Tiempo de ejecución**: Aproximadamente 8 minutos (18:48 - 18:56)
- **Throughput observado**: 1.25 videos por minuto
- **Impacto del tamaño**: 50% reducción en throughput vs archivos de 50MB
- **Utilización de recursos**: Mayor consumo de I/O para archivos de 100MB
- **Comportamiento del sistema**: Procesamiento estable pero más lento
- **Escalabilidad**: El sistema maneja archivos grandes pero con menor throughput
- **Métricas de throughput**: 1.25 videos/minuto - 125 MB/minuto procesados
  
**Resultados Entrega 5 Actual :**
- **Tiempo de ejecución**: Aproximadamente 15 minutos (02:20 - 02:35)
- **Throughput observado**: 0.67 videos por minuto (10 videos en ~15 minutos)
- **Impacto del tamaño**: Archivos de ~334MB promedio (según VideoFileSize)
- **CPU**: Picos de hasta 89.9% (máximo) con promedio ~45%
- **Memoria**: Máximo 23.4%, promedio ~15-19%
- **Red**: Pico de entrada de ~1.00GB (descarga de videos)
- **Procesamiento** en ráfagas visibles entre 02:25-02:40
- **Duración de procesamiento p95**: ~29.3 segundos por tarea
- **Escalabilidad**: El sistema procesó archivos significativamente más grandes (334MB vs 100MB anterior)
- **Métricas de throughput:
  - 0.67 videos/minuto
  - ~334MBB/minuto procesados
  
## Conclusión:
1. Videos promedio procesado 334M por minuto
2. Escalabilidad por Tamaño: Aunque el throughput en videos/minuto disminuyó 46%, el throughput en MB/minuto aumentó 79%, demostrando que el sistema escala eficientemente con archivos más grandes.
3. Eficiencia Relativa: Procesar archivos 3.34× más grandes solo incrementó el tiempo total en 1.87×, indicando una relación sublineal entre tamaño y tiempo de procesamiento.
4. Utilización de Recursos:
- El sistema muestra un uso equilibrado con CPU alcanzando picos altos (~90%) durante procesamiento activo
- Memoria se mantiene relativamente baja (23.4% máximo), sugiriendo procesamiento eficiente por streaming
- Tráfico de red significativo (~1GB) corresponde a la descarga de videos más grandes
4. Estabilidad: El sistema mantuvo estabilidad sin errores visibles, completando exitosamente los 10 videos.

El sistema demuestra buena escalabilidad para archivos grandes. La configuración actual del Auto Scaling Group (1-6 instancias) parece adecuada, aunque para cargas sostenidas de archivos >300MB podría considerarse aumentar la capacidad deseada a 2 instancias para mantener throughput más constante.

### 1.4 Carga Aumentada - 200 Videos (50MB)
```bash
docker exec producer python producer.py --num-videos 100 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Evidencias:**
- Capturas del sistema durante la prueba
<img width="1082" height="427" alt="image (34)" src="https://github.com/user-attachments/assets/e36d8af0-19f7-4228-a246-0706d033f6a4" />
<img width="1233" height="657" alt="image (35)" src="https://github.com/user-attachments/assets/5ab3aa86-b8bd-4f56-b77b-d2e252c1c640" />
<img width="1229" height="641" alt="image (36)" src="https://github.com/user-attachments/assets/5e469696-70b4-4fee-9e47-20cc579f4dbf" />
<img width="1225" height="647" alt="image (37)" src="https://github.com/user-attachments/assets/33717e86-87fb-4b43-affb-669b5ab9b0f1" />
<img width="1247" height="629" alt="image (38)" src="https://github.com/user-attachments/assets/a6862894-bfa8-401a-9d48-7081c8eaaae2" />
<img width="1231" height="608" alt="image (39)" src="https://github.com/user-attachments/assets/0f2156cd-cfbe-4b66-adea-c10614e52c37" />
<img width="1242" height="609" alt="image (40)" src="https://github.com/user-attachments/assets/b898ace4-6ae4-416d-9382-6f77ea9bfdf3" />
<img width="1348" height="230" alt="image (41)" src="https://github.com/user-attachments/assets/1f58b349-b33c-45aa-9ca5-351a1d9e3cc6" />

**Resultados Entrega 4:**
- **Tiempo de ejecución**: Aproximadamente 15 minutos (19:14 - 19:29)
- **Throughput observado**: 6.7 videos por minuto
- **Degradación del rendimiento**: 20% reducción vs prueba de 50 videos
- **Comportamiento de CloudWatch**: Métricas estables sin picos críticos
- **Utilización de recursos**: Incremento notable pero manejable
- **Estado de la cola de tareas**: Procesamiento secuencial exitoso
- **Métricas de CPU y memoria**: CPU ~50-60%, Memoria en niveles aceptables
- **Tiempo de respuesta promedio**: ~9 segundos por video

**Resultados Entrega Actual (5):**

- **Tiempo de ejecución**: Aproximadamente 25 minutos (03:05 - 03:30)
- **Throughput observado**: 4.0 videos por minuto 
- **Impacto del tamaño**: Archivos de ~555MB promedio (según VideoFileSize)
- **CPU**: Máximo 99.96%, promedio ~94.4%, sostenido en ~100% durante procesamiento activo
- **Memoria**: Máximo 24%, promedio ~23%, mínimo ~21.7%
- **Red RX**: Pico de 25.1M bytes/segundo, promedio 14.2M bytes/segundo
- **Comportamiento del sistema**:Procesamiento continuo sostenido entre 03:10-03:25
- **Duración de procesamiento p95**: ~34.4 segundos por tarea
- **Escalabilidad**: Sistema procesó carga 10× mayor con archivos 1.66× más grandes que ejecución anterior
  - Métricas de throughput**:
  - 4.0 videos/minuto
  - ~555MB/minuto procesados
- **Tareas del servicio**: 6 tareas corriendo simultáneamente (RunningTaskCount)

## Conclusión: 

- El promedio de MB procesado por minuto fue de 555
- El sistema procesó 20× más videos con solo 66.7% de incremento en tiempo comparado con la referencia de 200 videos de resultado de la entrega anterior
- TaskCount muestra escalamiento limpio de 1 a 200 tareas exitosas sin fallos
- Archivos resultaron en:
  *Throughput de videos 68.8% menor (1.25 → 4.0 no compensa el volumen)
  *Pero throughput de datos 17.76× mayor (125 → 2,220 MB/min)
- La duración p95 de 34.4s indica que archivos grandes dominan el tiempo de procesamiento

El sistema demuestra excelente escalabilidad horizontal (200 videos procesados exitosamente) pero enfrenta limitaciones de CPU que degradan el throughput 40% vs la referencia con archivos más pequeños. La arquitectura es sólida, pero requiere ajustes de capacidad para manejar cargas de archivos grandes de manera eficiente. El costo/beneficio de escalar verticalmente (instancias más potentes) vs horizontalmente (más instancias) debe evaluarse según el patrón de carga esperado.

