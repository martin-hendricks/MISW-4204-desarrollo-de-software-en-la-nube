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
- [ ] Capturas del sistema durante la prueba
- [ ] Logs del sistema
- [ ] Métricas de throughput

### 1.2 Prueba Intermedia - 50 Videos (50MB) con Debug
```bash
docker exec producer python producer.py --num-videos 50 --video-file ./assets/dummy_file_50mb.mp4 --no-wait --debug
```

**Evidencias:**
- [ ] Capturas del sistema durante la prueba
- [ ] Logs del sistema con debug habilitado
- [ ] Métricas de throughput

### 1.3 Prueba con Video Grande - 10 Videos (100MB)
```bash
docker exec producer python producer.py --num-videos 10 --video-file ./assets/dummy_file_100mb.mp4 --no-wait
```

**Evidencias:**
- [ ] Capturas del sistema durante la prueba
- [ ] Logs del sistema
- [ ] Métricas de throughput

## 2. Pruebas de Saturación (Encontrar el Límite)

### Objetivo
Encontrar el punto de quiebre del sistema aumentando progresivamente el número de videos en la cola hasta observar inestabilidad.

### 2.1 Carga Inicial - 50 Videos (50MB)
```bash
docker exec producer python producer.py --num-videos 50 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Evidencias:**
- [ ] Capturas del sistema durante la prueba
- [ ] Estado de la cola de tareas
- [ ] Métricas de CPU y memoria

### 2.2 Carga Aumentada - 100 Videos (50MB)
```bash
docker exec producer python producer.py --num-videos 100 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Evidencias:**
- [ ] Capturas del sistema durante la prueba
- [ ] Estado de la cola de tareas
- [ ] Métricas de CPU y memoria
- [ ] Tiempo de respuesta promedio

### 2.3 Carga de Saturación - 200 Videos (50MB)
```bash
docker exec producer python producer.py --num-videos 200 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Evidencias:**
- [ ] Capturas del sistema durante la prueba
- [ ] Estado de la cola de tareas
- [ ] Métricas de CPU y memoria
- [ ] Errores detectados
- [ ] Punto de saturación identificado

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