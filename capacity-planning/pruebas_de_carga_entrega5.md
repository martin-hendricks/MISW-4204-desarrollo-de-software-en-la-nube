
# Pruebas de Carga - Entrega 5

## 4.1 Escenario 1: Capacidad de la Capa Web (Usuarios Concurrentes)

### 4.1.1 Escenarios de Prueba

#### 4.1.2.1 **Prueba de Sanidad (Smoke Test)**
- **Usuarios**: 5 usuarios concurrentes
- **Duración**: 1 minuto
- **Objetivo**: Validar que el sistema responde correctamente y la telemetría está activa
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"`
- **Evidencias**: 
  - **Smoke Test**
    
<img width="1080" height="264" alt="image (28)" src="https://github.com/user-attachments/assets/70103f02-3131-42b3-ad08-a04281768027" />

  - **ClaudWatch**
    
![Cloud watch smoke test 2](https://github.com/user-attachments/assets/53625796-1756-4122-966e-71f300409c2c)


 ## **Conclusiónes - Prueba de Sanidad (Smoke Test)**
 
- En términos generales, la prueba de **smoke test** no presentó cambios significativos con respecto a la terecera entrega. Esto se debe a que, para este escenario, la instancia disponible logra resolver satisfactoriamente las solicitudes entrantes sin requerir escalamiento de la arquitectura.

--------------------------------------------------------------------------------------------------------------------------------------------------
#### 4.1.2.2 **Prueba de Escalamiento (Ramp-up)**
- **Estrategia**: Iniciar en 0 usuarios y aumentar gradualmente hasta X usuarios en 3 minutos, mantener 5 minutos
- **Comando**: en la instancia de AWS `docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_X_users_results.jtl -Jusers=X"`
- **Evidencias**: 
  - **100 Usuarios**
    
<img width="1267" height="703" alt="image (29)" src="https://github.com/user-attachments/assets/6ecc9d13-b55c-46cf-b72c-0062f5d75467" />

   ![Rump up - Cloudwatch -100 ](https://github.com/user-attachments/assets/36b13e6d-4013-4286-93e6-f2853a155f9d)
![Rump up - Cloudwatch 2 -100 ](https://github.com/user-attachments/assets/06020d90-2c58-439f-b010-86f12654514f)
![Rump up - Cloudwatch 3 -100 ](https://github.com/user-attachments/assets/f01df2e7-ca43-45f5-a8fb-3de7d482251e)
![Rump up - Cloudwatch 4 -100 ](https://github.com/user-attachments/assets/d8d6ff5e-cc9b-43a9-ad84-d9af8fdeffdc)

  - **200 Usuarios**
<img width="1197" height="657" alt="image (30)" src="https://github.com/user-attachments/assets/d5d9b4c9-194d-498a-913f-2ca04d82b0ff" />

  - **CloudWatch**
![Rump up - Cloudwatch 3 -200 ](https://github.com/user-attachments/assets/09322db7-17c1-44ab-b604-8856450b291a)

    ![Rump up - Cloudwatch 2 -200 ](https://github.com/user-attachments/assets/f5ec7e2f-3f42-4beb-99a4-29d1eb87eff8)

  - **300 Usuarios**
<img width="1265" height="480" alt="image (31)" src="https://github.com/user-attachments/assets/80e07081-891b-4b99-a7f7-5f98346dbe3d" />

  - **CloudWatch**
<img width="1232" height="582" alt="Captura de pantalla 2025-11-16 220137" src="https://github.com/user-attachments/assets/648bd57e-5d37-40ad-8c9f-b37d4e8fb720" />
<img width="1248" height="591" alt="Captura de pantalla 2025-11-16 220720" src="https://github.com/user-attachments/assets/1d8741bc-cc31-4e6e-bb37-9de21ed64ecc" />

    
## **Conclusiónes - Prueba de Escalamiento (Ramp-up)**

Las pruebas realizadas mediante **ramp-up** con 100 y 200 usuarios concurrentes permitieron observar el comportamiento del Auto Scaling Group no presento errores debido al correcto autoescalamiento de las instancias, llegando a consumir un pico maximo de cpu de 65% y un desenso de forma repentina. 

En la prueba de **ramp-up** de 0 a 300 usuario evidenciamos degradación del servicio debido a que tuvo llego a un pico máximo de 75% en la instancia principal y cuando se encontraba escalando evidenciamos que la siguiente instancia el balanceador verificaba que estaba lista y le enviaba las peticiones pero los servicios internos como el docker y el aplicativo aún se encontraban levantando por lo cual la instancia ec2 comenzo a devolver 404, para próximas entrergas vamos a revisar a fondo si esta hipótesis es la acertada.

------------------------------------------------------------------------------------------------------------------------------------------
#### 4.1.2.3 **Prueba Sostenida**

- **Usuarios**: Volvemos a evidenciar que de la prueba ramp-uop al llegar a los 300 usduarios tenemos degradacion del servicio por lo que al calcular el 80% de la capacidad con 300 usuarios tenemos un valor de 240 usuarios para realizar la prueba sostenida
- **Duración**: 5 minutos
- **Objetivo**: Confirmar estabilidad del sistema bajo carga sostenida

- **Evidencias**:
  - **Prueba sostenida**
    <img width="1265" height="475" alt="image (32)" src="https://github.com/user-attachments/assets/7e638a43-f16c-4725-8716-120e8f87b6ea" />

  - **CloudWatch**
    <img width="1244" height="603" alt="Captura de pantalla 2025-11-16 222216" src="https://github.com/user-attachments/assets/c3d63367-0521-44d5-b590-eb95d653eac7" />
<img width="1239" height="609" alt="Captura de pantalla 2025-11-16 222427" src="https://github.com/user-attachments/assets/66bace07-3a07-4485-bca8-c4bffd87b2dc" />



## **Conclusiónes - Prueba Sostenida**

Durante la prueba siostenida de 240 usuarios se evidencio un consumo de cpu de 57%, aunque la instancia principal opera cerca de su límite de CPU.


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

##Conclusión: 

- El promedio de MB procesado por minuto fue de 555
- El sistema procesó 20× más videos con solo 66.7% de incremento en tiempo comparado con la referencia de 200 videos de resultado de la entrega anterior
- TaskCount muestra escalamiento limpio de 1 a 200 tareas exitosas sin fallos
- Archivos resultaron en:
  *Throughput de videos 68.8% menor (1.25 → 4.0 no compensa el volumen)
  *Pero throughput de datos 17.76× mayor (125 → 2,220 MB/min)
- La duración p95 de 34.4s indica que archivos grandes dominan el tiempo de procesamiento

El sistema demuestra excelente escalabilidad horizontal (200 videos procesados exitosamente) pero enfrenta limitaciones de CPU que degradan el throughput 40% vs la referencia con archivos más pequeños. La arquitectura es sólida, pero requiere ajustes de capacidad para manejar cargas de archivos grandes de manera eficiente. El costo/beneficio de escalar verticalmente (instancias más potentes) vs horizontalmente (más instancias) debe evaluarse según el patrón de carga esperado.

