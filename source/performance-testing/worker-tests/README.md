# Producer - Pruebas de Carga para Worker

Este script permite realizar pruebas de carga enviando tareas de procesamiento de video a la cola de AWS SQS (o Redis en modo desarrollo).

## Requisitos Previos

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

Copia el archivo de ejemplo y configúralo con tus valores:

```bash
cp .env.example .env
```

Edita el archivo `.env` con los valores correctos:

#### Para AWS SQS (Producción)

```bash
USE_SQS=true
AWS_REGION=us-east-1
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/anb-video-processing-queue
SQS_DLQ_URL=https://sqs.us-east-1.amazonaws.com/ACCOUNT_ID/anb-video-processing-dlq

# Credenciales de AWS (solo si no usas IAM Role)
AWS_ACCESS_KEY_ID=tu_access_key
AWS_SECRET_ACCESS_KEY=tu_secret_key
AWS_SESSION_TOKEN=tu_session_token
```

#### Para Redis (Desarrollo Local)

```bash
USE_SQS=false
REDIS_URL=redis://localhost:6379/0
```

### 3. Obtener URLs de SQS

Si aún no has creado las colas de SQS, ejecuta:

```bash
cd ../../deployment/sqs-setup
./setup-sqs.sh us-east-1
```

Esto generará un archivo `sqs-config.env` con las URLs necesarias.

## Uso del Producer

### Sintaxis Básica

```bash
python producer.py [opciones]
```

### Opciones Disponibles

| Opción | Descripción | Valor por defecto |
|--------|-------------|-------------------|
| `--num-videos` | Número de videos a procesar | 10 |
| `--video-file` | Ruta al archivo de video de prueba | `./assets/dummy_file_50mb.mp4` |
| `--timeout` | Tiempo máximo de espera en segundos | 600 (10 minutos) |
| `--debug` | Activar modo debug con información adicional | Desactivado |
| `--no-wait` | Solo encolar tareas sin esperar resultados | Desactivado |

### Ejemplos de Uso

#### 1. Prueba básica con 10 videos

```bash
python producer.py
```

#### 2. Prueba de carga con 100 videos

```bash
python producer.py --num-videos 100
```

#### 3. Prueba con video personalizado

```bash
python producer.py --num-videos 50 --video-file /ruta/a/tu/video.mp4
```

#### 4. Prueba con timeout personalizado (30 minutos)

```bash
python producer.py --num-videos 200 --timeout 1800
```

#### 5. Solo encolar tareas sin esperar (recomendado para pruebas grandes)

```bash
python producer.py --num-videos 1000 --no-wait
```

#### 6. Modo debug para troubleshooting

```bash
python producer.py --num-videos 5 --debug
```

## Cómo Funciona

### Con AWS SQS (USE_SQS=true)

1. **Validación**: Verifica la conexión a AWS SQS y las credenciales
2. **Preparación**: Copia los archivos de video al volumen compartido
3. **Encolado**: Envía las tareas a la cola de SQS `video_processing`
4. **Monitoreo**:
   - Si `--no-wait`: Termina inmediatamente después de encolar
   - Si espera resultados: Monitorea la cola de SQS para ver cuántos mensajes quedan

### Con Redis (USE_SQS=false)

Similar al flujo de SQS, pero usando Redis como broker y puede rastrear el progreso de las tareas si el result backend está configurado.

## Monitoreo del Procesamiento

### Opción 1: Logs del Worker

```bash
# Si el worker está en Docker
docker logs -f <worker-container-name>

# Si el worker está en EC2
ssh ec2-user@WORKER_IP
sudo journalctl -u worker -f
```

### Opción 2: AWS SQS Console

1. Ve a la [Consola de AWS SQS](https://console.aws.amazon.com/sqs/)
2. Selecciona la cola `anb-video-processing-queue`
3. Monitorea las métricas:
   - Mensajes disponibles
   - Mensajes en vuelo
   - Edad del mensaje más antiguo

### Opción 3: CloudWatch Metrics

El worker envía métricas automáticamente a CloudWatch:

```bash
# Ver métricas de TaskCount
aws cloudwatch get-metric-statistics \
  --namespace ANB/Worker \
  --metric-name TaskCount \
  --dimensions Name=Status,Value=Success \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-01T23:59:59Z \
  --period 300 \
  --statistics Sum

# Ver métricas de TaskDuration
aws cloudwatch get-metric-statistics \
  --namespace ANB/Worker \
  --metric-name TaskDuration \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-01T23:59:59Z \
  --period 300 \
  --statistics Average,Maximum,Minimum
```

## Salida del Producer

### Información de Inicio

```
============================================================
🚀 Iniciando prueba de rendimiento del Worker
   - Tareas a generar: 100
   - Archivo de video: ./assets/dummy_file_50mb.mp4
   - Destino de worker: /app/uploads/original
   - Timeout: 600 segundos
   - Broker: AWS SQS
   - AWS Region: us-east-1
   - SQS Queue: anb-video-processing-queue
   - Modo Debug: Desactivado
   - Modo: Encolar y esperar resultados
============================================================
```

### Durante el Procesamiento (con SQS)

```
[Paso 3/4] Esperando resultados...
   Timeout configurado: 600 segundos

   Monitoreando la cola de SQS...
   Mensajes en cola: 45 | En procesamiento: 5 | Tiempo: 120.5s
```

### Resultados Finales

```
============================================================
📊 Resultados de la Prueba de Rendimiento
------------------------------------------------------------
   - Videos procesados:       100
   - Tamaño por video:        50.00 MB
   - Datos totales:           5000.00 MB
   - Tiempo total:            245.67 segundos
   - Throughput (videos/seg): 0.41
   - Throughput (videos/min): 24.44
============================================================
```

## Troubleshooting

### Error: "No se encontraron credenciales de AWS"

**Solución**: Configura las credenciales de AWS en el archivo `.env` o usa un IAM Role si estás en EC2.

```bash
# Opción 1: Variables de entorno
export AWS_ACCESS_KEY_ID=tu_access_key
export AWS_SECRET_ACCESS_KEY=tu_secret_key
export AWS_SESSION_TOKEN=tu_session_token

# Opción 2: Configurar AWS CLI
aws configure
```

### Error: "La cola SQS no existe"

**Solución**: Crea las colas ejecutando el script de setup:

```bash
cd ../../deployment/sqs-setup
./setup-sqs.sh us-east-1
```

### Error: "No se puede continuar sin la carpeta de uploads"

**Solución**: Asegúrate de que el volumen compartido esté montado correctamente o que la carpeta exista:

```bash
mkdir -p /app/uploads/original
```

### Las tareas se encolan pero nunca se procesan

**Verificar**:
1. El worker está corriendo: `docker ps | grep worker`
2. El worker tiene las mismas credenciales de AWS
3. El worker tiene `USE_SQS=true` configurado
4. Las URLs de SQS coinciden entre producer y worker

## Notas Importantes

1. **Límites de SQS**: AWS SQS tiene límites de throughput. Para pruebas muy grandes (>1000 tareas), considera usar `--no-wait` y monitorear desde CloudWatch.

2. **Costos**: Cada llamada a SQS tiene un costo. El long polling (configurado a 20 segundos) ayuda a reducir costos.

3. **Timeout de Visibilidad**: Las tareas tienen 1 hora (3600 segundos) de visibility timeout. Si un worker no completa la tarea en ese tiempo, la tarea volverá a la cola.

4. **Dead Letter Queue**: Después de 3 reintentos fallidos, las tareas se mueven automáticamente a la DLQ para su análisis.

5. **CloudWatch Integration**: El worker envía métricas automáticamente. Revisa CloudWatch para análisis detallado del rendimiento.
