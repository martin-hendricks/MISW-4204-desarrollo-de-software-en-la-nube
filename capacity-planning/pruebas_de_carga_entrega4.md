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



### 1.2 Prueba con Video Grande - 10 Videos (100MB)
```bash
docker exec producer python producer.py --num-videos 10 --video-file ./assets/dummy_file_100mb.mp4 --no-wait
```

**Evidencias:**
- Capturas del sistema durante la prueba

<img width="1223" height="934" alt="screencapture-us-east-1-console-aws-amazon-ec2-instance-connect-ssh-home-2025-11-16-18_48_41" src="https://github.com/user-attachments/assets/70903d51-0f81-4f9e-8dca-63e3add2609e" />


<img width="1223" height="1169" alt="screencapture-us-east-1-console-aws-amazon-ec2-home-2025-11-16-18_50_30" src="https://github.com/user-attachments/assets/20ab10c9-57ce-4cfe-9b59-4fe34be97850" />

<img width="1223" height="1540" alt="screencapture-us-east-1-console-aws-amazon-cloudwatch-home-2025-11-16-18_56_57" src="https://github.com/user-attachments/assets/9c4562c7-984b-44df-8730-8e52e79896e8" />

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


### 2.2 Carga Aumentada - 100 Videos (50MB)
```bash
docker exec producer python producer.py --num-videos 100 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Evidencias:**
- Capturas del sistema durante la prueba
<img width="1223" height="934" alt="screencapture-us-east-1-console-aws-amazon-ec2-instance-connect-ssh-home-2025-11-16-19_14_34" src="https://github.com/user-attachments/assets/6448f5c6-4539-4795-933d-6bc200a2ea41" />

<img width="1223" height="1540" alt="screencapture-us-east-1-console-aws-amazon-cloudwatch-home-2025-11-16-19_29_06" src="https://github.com/user-attachments/assets/07ad9b2a-2806-4946-949d-56e379174021" />



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


## 3. Análisis de Resultados

### Resumen de Métricas
- [ ] Tabla comparativa de throughput
- [ ] Gráfico de evolución de la cola
- [ ] Análisis de recursos consumidos
- [ ] Identificación del punto de saturación

### Conclusiones
- [ ] Capacidad máxima del sistema
- [ ] Recomendaciones de configuración
- [ ] Limitaciones identificadas
- [ ] Mejoras propuestas

## 4. Anexos
- [ ] Configuración del entorno de pruebas
- [ ] Logs completos
- [ ] Capturas adicionales del sistema
