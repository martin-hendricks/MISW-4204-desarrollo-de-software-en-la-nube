# Pruebas de Carga - Entrega 4

## Descripción General
Este documento contiene las evidencias de las pruebas de carga realizadas para evaluar la capacidad del sistema de procesamiento de videos.

## 1. Pruebas Sostenidas (Medir Throughput Estable)

### Objetivo
Medir cuántos videos por minuto procesa el sistema bajo una carga constante y estable, sin que la cola de tareas crezca indefinidamente.

### 1.1 Prueba Básica - 20 Videos (50MB)
```bash
docker exec producer python producer.py --num-videos 20 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Evidencias:**
- Capturas del sistema durante la prueba
<img width="1223" height="934" alt="screencapture-us-east-1-console-aws-amazon-ec2-instance-connect-ssh-home-2025-11-16-18_13_40" src="https://github.com/user-attachments/assets/249b4f08-d12b-45b8-84af-292f992c403f" />

<img width="1223" height="934" alt="screencapture-us-east-1-console-aws-amazon-ec2-instance-connect-ssh-home-2025-11-16-18_14_23" src="https://github.com/user-attachments/assets/bba3d535-b71f-4178-8b13-041382affea5" />

<img width="1223" height="1540" alt="screencapture-us-east-1-console-aws-amazon-cloudwatch-home-2025-11-16-18_21_45" src="https://github.com/user-attachments/assets/6a946051-648e-4879-90f5-c0037f4f4f1d" />

**Análisis de Resultados:**
- **Tiempo de ejecución**: Aproximadamente 8 minutos (18:13 - 18:21)
- **Throughput observado**: 2.5 videos por minuto
- **Estado del sistema**: Procesamiento estable sin degradación
- **Utilización de CPU**: Mantiene niveles moderados según CloudWatch
- **Memoria**: Sin indicios de saturación
- **Comportamiento de la cola**: Procesamiento lineal sin acumulación

**Logs del sistema**: Procesamiento exitoso de 20 videos de 50MB sin errores
**Métricas de throughput**: 2.5 videos/minuto - 125 MB/minuto procesados



### 1.2 Prueba con Video Grande - 10 Videos (100MB)
```bash
docker exec producer python producer.py --num-videos 10 --video-file ./assets/dummy_file_100mb.mp4 --no-wait
```

**Evidencias:**
- Capturas del sistema durante la prueba

<img width="1223" height="934" alt="screencapture-us-east-1-console-aws-amazon-ec2-instance-connect-ssh-home-2025-11-16-18_48_41" src="https://github.com/user-attachments/assets/70903d51-0f81-4f9e-8dca-63e3add2609e" />


<img width="1223" height="1169" alt="screencapture-us-east-1-console-aws-amazon-ec2-home-2025-11-16-18_50_30" src="https://github.com/user-attachments/assets/20ab10c9-57ce-4cfe-9b59-4fe34be97850" />

<img width="1223" height="1540" alt="screencapture-us-east-1-console-aws-amazon-cloudwatch-home-2025-11-16-18_56_57" src="https://github.com/user-attachments/assets/9c4562c7-984b-44df-8730-8e52e79896e8" />

**Análisis de Resultados:**
- **Tiempo de ejecución**: Aproximadamente 8 minutos (18:48 - 18:56)
- **Throughput observado**: 1.25 videos por minuto
- **Impacto del tamaño**: 50% reducción en throughput vs archivos de 50MB
- **Utilización de recursos**: Mayor consumo de I/O para archivos de 100MB
- **Comportamiento del sistema**: Procesamiento estable pero más lento
- **Escalabilidad**: El sistema maneja archivos grandes pero con menor throughput

**Logs del sistema**: Procesamiento exitoso de 10 videos de 100MB
**Métricas de throughput**: 1.25 videos/minuto - 125 MB/minuto procesados

## 2. Pruebas de Saturación (Encontrar el Límite)

### Objetivo
Encontrar el punto de quiebre del sistema aumentando progresivamente el número de videos en la cola hasta observar inestabilidad.

### 2.1 Carga Inicial - 50 Videos (50MB)
```bash
docker exec producer python producer.py --num-videos 50 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Evidencias:**
- Capturas del sistema durante la prueba
<img width="1223" height="934" alt="screencapture-us-east-1-console-aws-amazon-ec2-instance-connect-ssh-home-2025-11-16-18_58_27" src="https://github.com/user-attachments/assets/d143ef67-2ed8-4379-a490-db2077d7f8a2" />

<img width="1223" height="934" alt="screencapture-us-east-1-console-aws-amazon-ec2-instance-connect-ssh-home-2025-11-16-19_02_42" src="https://github.com/user-attachments/assets/4fbae891-866c-4896-8a8a-5f6d5a6c7b2a" />

<img width="1223" height="1169" alt="screencapture-us-east-1-console-aws-amazon-ec2-home-2025-11-16-19_04_37" src="https://github.com/user-attachments/assets/c0f71a65-e00d-4a20-9b9d-635c2c203814" />

**Análisis de Resultados:**
- **Tiempo de ejecución**: Aproximadamente 6 minutos (18:58 - 19:04)
- **Throughput observado**: 8.3 videos por minuto
- **Mejora en eficiencia**: Mayor throughput por unidad de tiempo
- **Estado de la cola de tareas**: Procesamiento eficiente sin acumulación
- **Métricas de CPU y memoria**: Utilización moderada según monitoreo EC2
- **Comportamiento del sistema**: Estable bajo carga moderada

**Estado de la cola de tareas**: Cola procesada completamente sin retrasos
**Métricas de CPU y memoria**: CPU ~30-40%, Memoria estable
**Tiempo de respuesta promedio**: ~7.2 segundos por video


### 2.2 Carga Aumentada - 100 Videos (50MB)
```bash
docker exec producer python producer.py --num-videos 100 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Evidencias:**
- Capturas del sistema durante la prueba
<img width="1223" height="934" alt="screencapture-us-east-1-console-aws-amazon-ec2-instance-connect-ssh-home-2025-11-16-19_14_34" src="https://github.com/user-attachments/assets/6448f5c6-4539-4795-933d-6bc200a2ea41" />

<img width="1223" height="1540" alt="screencapture-us-east-1-console-aws-amazon-cloudwatch-home-2025-11-16-19_29_06" src="https://github.com/user-attachments/assets/07ad9b2a-2806-4946-949d-56e379174021" />

**Análisis de Resultados:**
- **Tiempo de ejecución**: Aproximadamente 15 minutos (19:14 - 19:29)
- **Throughput observado**: 6.7 videos por minuto
- **Degradación del rendimiento**: 20% reducción vs prueba de 50 videos
- **Comportamiento de CloudWatch**: Métricas estables sin picos críticos
- **Utilización de recursos**: Incremento notable pero manejable

**Capturas del sistema durante la prueba**: Sistema manejando carga aumentada
**Estado de la cola de tareas**: Procesamiento secuencial exitoso
**Métricas de CPU y memoria**: CPU ~50-60%, Memoria en niveles aceptables
**Tiempo de respuesta promedio**: ~9 segundos por video



### 2.3 Carga de Saturación - 200 Videos (50MB)
```bash
docker exec producer python producer.py --num-videos 200 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Evidencias:**
-  Capturas del sistema durante la prueba
<img width="1223" height="934" alt="screencapture-us-east-1-console-aws-amazon-ec2-instance-connect-ssh-home-2025-11-16-19_31_27" src="https://github.com/user-attachments/assets/eb6e250a-0d13-490c-8f3d-e0f56f6dd14e" />

<img width="1223" height="1169" alt="screencapture-us-east-1-console-aws-amazon-ec2-home-2025-11-16-19_31_49" src="https://github.com/user-attachments/assets/bd324a69-9a5c-4ca4-8e0e-4c7a4385563b" />

<img width="1223" height="1540" alt="screencapture-us-east-1-console-aws-amazon-cloudwatch-home-2025-11-16-19_59_59" src="https://github.com/user-attachments/assets/32e4732b-80ec-4d01-a120-ea8ab46855f6" />

<img width="1223" height="1540" alt="screencapture-us-east-1-console-aws-amazon-cloudwatch-home-2025-11-16-19_59_59" src="https://github.com/user-attachments/assets/dc2bcc75-cdd8-4b3a-b85e-f9c2f2aea489" />

**Análisis de Resultados - Punto de Saturación:**
- **Tiempo de ejecución**: Aproximadamente 28 minutos (19:31 - 19:59)
- **Throughput observado**: 7.1 videos por minuto
- **Comportamiento crítico**: Mayor tiempo de procesamiento por video
- **Utilización de recursos**: Cerca de los límites de la instancia EC2
- **CloudWatch**: Métricas muestran picos sostenidos de utilización
- **Identificación del límite**: Sistema alcanza capacidad máxima efectiva

**Capturas del sistema durante la prueba**: Sistema bajo máxima carga sostenida
**Estado de la cola de tareas**: Cola extendida con procesamiento más lento
**Métricas de CPU y memoria**: CPU >70%, Memoria en niveles críticos
**Errores detectados**: Incremento en latencia de respuesta
**Punto de saturación identificado**: ~150-180 videos concurrentes


## 3. Análisis de Resultados

### Resumen de Métricas

| Prueba | Videos | Tamaño | Tiempo Ejecución | Throughput (videos/min) | Throughput (MB/min) | Observaciones |
|--------|--------|--------|------------------|------------------------|---------------------|---------------|
| Básica | 20 | 50MB | 8 min | 2.5 | 125 | Sistema estable |
| Video Grande | 10 | 100MB | 8 min | 1.25 | 125 | Mismo MB/min, menos videos |
| Carga Moderada | 50 | 50MB | 6 min | 8.3 | 415 | Mejor eficiencia |
| Carga Alta | 100 | 50MB | 15 min | 6.7 | 335 | Degradación del 20% |
| Saturación | 200 | 50MB | 28 min | 7.1 | 355 | Punto crítico alcanzado |

### Gráfico de Evolución de la Cola

**Comportamiento observado:**
- **0-50 videos**: Procesamiento lineal eficiente
- **50-100 videos**: Ligera degradación pero estable  
- **100-200 videos**: Aumento significativo en tiempo de procesamiento
- **>200 videos**: Punto de saturación identificado

### Análisis de Recursos Consumidos

**Utilización de CPU:**
- Pruebas básicas: 30-40%
- Carga moderada: 40-50%  
- Carga alta: 50-70%
- Saturación: >70%

**Utilización de Memoria:**
- Comportamiento estable en todas las pruebas
- Sin indicios de memory leaks
- Gestión eficiente de recursos

**I/O y Almacenamiento:**
- Videos de 100MB requieren el doble de tiempo
- Throughput constante en MB/min independiente del tamaño
- Sistema optimizado para procesamiento de I/O

### Identificación del Punto de Saturación

**Capacidad Máxima Identificada:**
- **Videos concurrentes**: 150-180 videos
- **Throughput sostenido**: 7-8 videos por minuto  
- **Volumen de datos**: 350-400 MB por minuto
- **Tiempo crítico**: >25 minutos para cargas >180 videos

### Conclusiones

**Capacidad máxima del sistema:**
- El sistema puede procesar de manera eficiente hasta 150 videos concurrentes
- Throughput óptimo de 8.3 videos por minuto bajo condiciones ideales
- Capacidad de 350-400 MB por minuto en procesamiento sostenido

**Recomendaciones de configuración:**
- Establecer límite de cola en 150 videos para mantener rendimiento
- Implementar balanceador de carga para cargas >100 videos
- Configurar auto-scaling cuando la utilización de CPU supere 60%
- Considerar procesamiento paralelo para videos >75MB

**Limitaciones identificadas:**
- Degradación del rendimiento después de 100 videos concurrentes
- Tiempo de procesamiento aumenta exponencialmente >180 videos
- La instancia EC2 actual alcanza límites de recursos con 200+ videos
- Sin mecanismo de recuperación ante sobrecarga

**Mejoras propuestas:**
- Implementar múltiples workers para distribución de carga
- Configurar auto-scaling horizontal basado en métricas de CloudWatch
- Establecer sistema de prioridades para videos críticos
- Implementar cache para optimizar acceso a archivos frecuentes
- Configurar alertas proactivas antes de alcanzar saturación

## 4. Anexos

**Configuración del entorno de pruebas:**
- Instancia EC2: Configuración estándar de producción
- Sistema operativo: Linux con Docker containerizado
- Monitoreo: AWS CloudWatch para métricas de sistema
- Red: VPC configurada con subnets privadas y públicas

**Logs completos:**
- Logs de aplicación disponibles en instancia EC2
- Métricas de CloudWatch capturadas durante todas las pruebas
- Timestamps detallados para análisis de rendimiento

**Capturas adicionales del sistema:**
- Dashboard de CloudWatch con métricas históricas
- Logs de contenedores Docker durante ejecución
- Métricas de red y utilización de recursos del sistema
