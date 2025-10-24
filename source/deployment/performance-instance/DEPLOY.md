# Guía de Deployment: Instancia de Performance Testing

Esta guía te ayudará a configurar una instancia EC2 en AWS dedicada exclusivamente para ejecutar pruebas de rendimiento contra la infraestructura de tu compañero.

---

## Arquitectura del Performance Testing

```
┌─────────────────────────────────────────────────────────────┐
│ TU CUENTA AWS (Performance Testing)                        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ EC2: anb-performance-testing                        │  │
│  │                                                     │  │
│  │  • Producer (Python + Celery Client)               │  │
│  │  • JMeter (HTTP Load Testing)                      │  │
│  │  • Prometheus (Metrics Collection)                 │  │
│  │  • Grafana (Metrics Visualization)                 │  │
│  └─────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         │ SSH Tunnel                        │
│                         ▼                                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ SSH Connection
                          │
┌─────────────────────────┼───────────────────────────────────┐
│ CUENTA DE TU COMPAÑERO  │                                   │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ EC2: anb-backend (IP Pública de tu compañero)      │  │
│  │                                                     │  │
│  │  • Redis (Puerto 6379) ◄─── Túnel SSH              │  │
│  │  • API Backend (Puerto 80) ◄─── HTTP directo       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ EC2: anb-worker                                     │  │
│  │                                                     │  │
│  │  • Celery Worker (procesa las tareas)              │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Flujo de las Pruebas

1. **Producer** (tu instancia) → Encola tareas en **Redis** (instancia de tu compañero) vía SSH tunnel
2. **Worker** (instancia de tu compañero) → Procesa las tareas de la cola
3. **Prometheus** (tu instancia) → Recolecta métricas del backend de tu compañero vía HTTP
4. **Grafana** (tu instancia) → Visualiza las métricas

---

## Paso 1: Crear Security Group (5 min)

**En AWS Console > EC2 > Security Groups > Create Security Group:**

```
Name: anb-performance-sg
Description: Security group for Performance Testing instance

Inbound Rules:
- SSH (22) from Your IP
- Custom TCP (3000) from Your IP [Grafana]
- Custom TCP (9090) from Your IP [Prometheus - opcional]

Outbound Rules:
- All traffic to 0.0.0.0/0
```

---

## Paso 2: Crear Instancia EC2 (10 min)

**En AWS Console > EC2 > Launch Instance:**

```
Name: anb-performance-testing
AMI: Ubuntu Server 22.04 LTS
Instance type: t2.medium (recomendado para JMeter)
Key pair: <tu-key>
Security group: anb-performance-sg
Storage: 20 GB (gp3)
```

**Anotar IPs:**
```
PERFORMANCE_PUBLIC_IP: _____________________________________________
PERFORMANCE_PRIVATE_IP: _____________________________________________
```

---

## Paso 3: Configurar Acceso SSH al Backend de tu Compañero (15 min)

### 3.1 Obtener datos del Backend de tu compañero

Tu compañero debe proporcionarte:

```
BACKEND_PUBLIC_IP: _____________________________________________
BACKEND_SSH_KEY: <archivo-clave.pem>
BACKEND_SSH_USER: ubuntu (generalmente)
```

### 3.2 Copiar la clave SSH del backend a tu instancia

**En tu máquina local:**

```bash
# Copiar la clave del backend de tu compañero a tu instancia de performance
scp -i "your-key.pem" backend-key.pem ubuntu@<PERFORMANCE_PUBLIC_IP>:~/backend-key.pem

# Conectarte a tu instancia de performance
ssh -i "your-key.pem" ubuntu@<PERFORMANCE_PUBLIC_IP>

# Configurar permisos de la clave del backend
chmod 400 ~/backend-key.pem
```

### 3.3 Probar conexión SSH al backend

```bash
# Desde tu instancia de performance, conectarte al backend de tu compañero
ssh -i ~/backend-key.pem ubuntu@<BACKEND_PUBLIC_IP>

# Si funciona, deberías estar conectado al servidor backend
# Verifica que Redis esté corriendo:
docker ps | grep redis

# Salir del backend
exit
```

---

## Paso 4: Instalar Docker y Dependencias (10 min)

**Conectarse a tu instancia de performance:**

```bash
ssh -i "your-key.pem" ubuntu@<PERFORMANCE_PUBLIC_IP>
```

**Instalar Docker y herramientas:**

```bash
# Actualizar paquetes
sudo apt update

# Instalar Docker y Docker Compose
sudo apt install -y docker.io docker-compose

# Agregar usuario al grupo docker
sudo usermod -aG docker ubuntu

# Instalar herramientas adicionales
sudo apt install -y git curl wget

# Cerrar sesión y volver a entrar para aplicar permisos
exit
ssh -i "your-key.pem" ubuntu@<PERFORMANCE_PUBLIC_IP>

# Verificar instalación
docker --version
docker-compose --version
```

---

## Paso 5: Copiar Archivos del Proyecto (15 min)

### 5.1 Clonar el repositorio o copiar archivos

**Opción 1: Clonar desde Git (Recomendado)**

```bash
# Conectado a tu instancia de performance
cd ~
git clone https://github.com/TU_USUARIO/MISW-4204-desarrollo-de-software-en-la-nube.git
cd MISW-4204-desarrollo-de-software-en-la-nube/source/deployment/performance-instance
```

**Opción 2: Copiar desde tu máquina local**

```bash
# Desde tu máquina local
scp -i "your-key.pem" -r ./source/deployment/performance-instance ubuntu@<PERFORMANCE_PUBLIC_IP>:~/performance-instance
scp -i "your-key.pem" -r ./source/performance-testing ubuntu@<PERFORMANCE_PUBLIC_IP>:~/performance-testing

# Conectarte a la instancia
ssh -i "your-key.pem" ubuntu@<PERFORMANCE_PUBLIC_IP>
cd ~/performance-instance
```

---

## Paso 6: Configurar Variables de Entorno (10 min)

### 6.1 Crear archivo .env

```bash
# Desde tu instancia de performance
cd ~/performance-instance
nano .env
```

**Contenido del .env:**

```bash
# ==========================================
# CONFIGURACIÓN DEL BACKEND DE TU COMPAÑERO
# ==========================================

# IP pública del backend de tu compañero
BACKEND_PUBLIC_IP=3.XXX.XXX.XXX

# Usuario SSH del backend
BACKEND_SSH_USER=ubuntu

# Ruta a la clave SSH del backend (dentro de tu instancia)
BACKEND_SSH_KEY=/home/ubuntu/backend-key.pem

# ==========================================
# CONFIGURACIÓN DE REDIS (vía SSH Tunnel)
# ==========================================

# Redis se conectará vía túnel SSH al backend
# El producer se conectará a localhost:6379 que será tunelizado
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# ==========================================
# CONFIGURACIÓN DE LA API (Acceso Directo HTTP)
# ==========================================

# La API del backend se accede directamente por HTTP (puerto 80)
API_BASE_URL=http://3.XXX.XXX.XXX

# Usuario de prueba para JMeter (debe existir en el backend)
TEST_USER_EMAIL=performance_test@example.com
TEST_USER_PASSWORD=PerformanceTest123!

# ==========================================
# CONFIGURACIÓN DE PROMETHEUS
# ==========================================

# IP pública del backend para scraping de métricas
PROMETHEUS_BACKEND_TARGET=3.XXX.XXX.XXX:8000
PROMETHEUS_WORKER_TARGET=3.XXX.XXX.XXX:8001

# ==========================================
# CONFIGURACIÓN DE GRAFANA
# ==========================================

GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=admin
```

**Guardar:** `Ctrl + O`, `Enter`, `Ctrl + X`

### 6.2 Validar configuración

```bash
# Verificar que el archivo .env está correcto
cat .env

# Verificar que la clave SSH existe
ls -lh ~/backend-key.pem
```

---

## Paso 7: Configurar SSH Tunnel a Redis (20 min)

### 7.1 Crear script de túnel SSH

```bash
cd ~/performance-instance
nano setup-ssh-tunnel.sh
```

**Contenido del script:**

```bash
#!/bin/bash

# Cargar variables de entorno
source .env

echo "=========================================="
echo "Configurando túnel SSH a Redis"
echo "=========================================="
echo "Backend IP: $BACKEND_PUBLIC_IP"
echo "SSH User: $BACKEND_SSH_USER"
echo "SSH Key: $BACKEND_SSH_KEY"
echo ""

# Verificar que la clave SSH existe
if [ ! -f "$BACKEND_SSH_KEY" ]; then
    echo "ERROR: La clave SSH no existe en $BACKEND_SSH_KEY"
    exit 1
fi

# Verificar permisos de la clave
PERMS=$(stat -c %a "$BACKEND_SSH_KEY")
if [ "$PERMS" != "400" ]; then
    echo "ADVERTENCIA: Los permisos de la clave SSH no son 400. Corrigiendo..."
    chmod 400 "$BACKEND_SSH_KEY"
fi

# Verificar conectividad SSH
echo "Probando conexión SSH al backend..."
ssh -i "$BACKEND_SSH_KEY" \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=no \
    "$BACKEND_SSH_USER@$BACKEND_PUBLIC_IP" \
    "echo 'Conexión SSH exitosa' && docker ps | grep redis"

if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo conectar al backend via SSH"
    echo "Verifica:"
    echo "  1. La IP pública del backend es correcta"
    echo "  2. La clave SSH es correcta"
    echo "  3. El Security Group del backend permite SSH desde esta IP"
    exit 1
fi

echo ""
echo "Creando túnel SSH a Redis (puerto 6379)..."
echo "Nota: Este proceso se ejecutará en segundo plano"

# Crear túnel SSH a Redis
# -f: ejecutar en background
# -N: no ejecutar comandos remotos (solo túnel)
# -L: port forwarding local
ssh -f -N \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -o StrictHostKeyChecking=no \
    -i "$BACKEND_SSH_KEY" \
    -L 6379:localhost:6379 \
    "$BACKEND_SSH_USER@$BACKEND_PUBLIC_IP"

if [ $? -eq 0 ]; then
    echo "Túnel SSH creado exitosamente"
    echo ""
    echo "Verificando túnel..."
    sleep 2

    # Verificar que el puerto 6379 está escuchando
    if netstat -tuln | grep -q ":6379"; then
        echo "El puerto 6379 está abierto localmente"
        echo ""
        echo "Para verificar que Redis responde:"
        echo "  docker run --rm --network host redis:latest redis-cli ping"
        echo ""
        echo "Para ver el proceso del túnel SSH:"
        echo "  ps aux | grep 'ssh.*6379'"
        echo ""
        echo "Para cerrar el túnel:"
        echo "  pkill -f 'ssh.*6379'"
    else
        echo "ADVERTENCIA: El puerto 6379 no está escuchando"
        echo "Verifica los logs de SSH"
    fi
else
    echo "ERROR: No se pudo crear el túnel SSH"
    exit 1
fi

echo "=========================================="
echo "Túnel SSH configurado correctamente"
echo "=========================================="
```

**Guardar y dar permisos:**

```bash
chmod +x setup-ssh-tunnel.sh
```

### 7.2 Ejecutar el script de túnel SSH

```bash
./setup-ssh-tunnel.sh
```

**Deberías ver:**

```
==========================================
Túnel SSH configurado correctamente
==========================================
```

### 7.3 Verificar el túnel SSH

```bash
# Verificar que el puerto 6379 está escuchando localmente
netstat -tuln | grep 6379

# Probar conexión a Redis (requiere redis-cli)
docker run --rm --network host redis:latest redis-cli ping
# Debería responder: PONG

# Ver el proceso del túnel
ps aux | grep 'ssh.*6379'
```

---

## Paso 8: Desplegar Performance Testing (15 min)

### 8.1 Levantar servicios con Docker Compose

```bash
cd ~/performance-instance

# Levantar servicios en modo detached
docker-compose up -d

# Ver logs de los servicios
docker-compose logs -f
```

**Servicios que se levantarán:**

1. **setup-jwt**: Configura el token JWT inicial (se ejecuta una vez)
2. **renew-jwt**: Renueva el token cada 30 minutos
3. **prometheus**: Recolecta métricas (puerto 9090)
4. **grafana**: Visualiza métricas (puerto 3000)
5. **jmeter**: Ejecutor de pruebas HTTP
6. **producer**: Cliente para inyectar tareas en Redis

### 8.2 Verificar que los servicios están corriendo

```bash
docker ps
```

**Deberías ver:**

```
CONTAINER ID   IMAGE                     STATUS
xxxxx          grafana/grafana:latest    Up 1 minute   0.0.0.0:3000->3000/tcp
xxxxx          prom/prometheus:latest    Up 1 minute   0.0.0.0:9090->9090/tcp
xxxxx          justb4/jmeter:latest      Up 1 minute
xxxxx          producer                  Up 1 minute
xxxxx          renew-jwt                 Up 1 minute
```

### 8.3 Verificar logs iniciales

```bash
# Ver logs del setup JWT
docker logs setup-jwt

# Deberías ver:
# [INFO] Usuario de prueba creado/verificado exitosamente
# [INFO] JWT token obtenido exitosamente

# Ver logs del producer (verificar conexión a Redis)
docker logs producer
```

---

## Paso 9: Verificación End-to-End (20 min)

### 9.1 Verificar acceso a Grafana

**Desde tu navegador local:**

```
http://<PERFORMANCE_PUBLIC_IP>:3000
```

- **Usuario:** `admin`
- **Password:** `admin`

**Navegar a:**
- Dashboard del Worker: [http://localhost:3000/d/worker-perf/worker-performance-video-processing](http://localhost:3000/d/worker-perf/worker-performance-video-processing)
- Dashboard del Backend: [http://localhost:3000/d/backend-api-perf/backend-api-performance](http://localhost:3000/d/backend-api-perf/backend-api-performance)

### 9.2 Verificar conexión a Redis

```bash
# Desde tu instancia de performance
docker exec producer redis-cli -h localhost -p 6379 ping
# Debería responder: PONG

# Ver la longitud de la cola
docker exec producer redis-cli -h localhost -p 6379 LLEN video_processing
# Debería responder: (integer) 0
```

### 9.3 Verificar acceso a la API del backend

```bash
# Verificar health check
curl http://<BACKEND_PUBLIC_IP>/health

# Deberías ver:
# {"status":"healthy"}
```

### 9.4 Ejecutar prueba de sanidad con JMeter

```bash
# Ejecutar smoke test
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"

# Ver resultados
cat ~/performance-testing/web-api-tests/scenarios/scenarios/smoke_results.jtl
```

### 9.5 Ejecutar prueba básica con el Producer

```bash
# Encolar 5 tareas de prueba
docker exec producer python producer.py --num-videos 5 --video-file ./assets/dummy_file_50mb.mp4 --no-wait --debug

# Deberías ver:
# [INFO] Verificando conexión a Redis...
# [INFO] ✅ Conexión a Redis exitosa
# [INFO] ✅ 5 tareas encoladas exitosamente.

# Verificar que las tareas se encolaron en Redis
docker exec producer redis-cli -h localhost -p 6379 LLEN video_processing
# Debería mostrar: (integer) 5 (o menos si ya se están procesando)

# Monitorear en Grafana que las tareas se procesan
```

---

## Paso 10: Ejecutar Escenarios de Prueba

### 10.1 Pruebas de API con JMeter

**Smoke Test (Validación básica):**

```bash
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"
```

**Ramp-up Test (Encontrar capacidad máxima):**

```bash
# Prueba con 100 usuarios
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_100_users_results.jtl -Jusers=100"

# Prueba con 200 usuarios
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_200_users_results.jtl -Jusers=200"

# Prueba con 300 usuarios
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_300_users_results.jtl -Jusers=300"
```

**Sustained Test (Prueba sostenida al 80% de capacidad):**

```bash
# Si la capacidad máxima fue 146 usuarios, prueba con 116 (80%)
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/sustained_test.jmx -l /scripts/sustained_116_users_results.jtl -Jusers=116"
```

### 10.2 Pruebas de Worker con Producer

**Prueba básica (20 videos):**

```bash
docker exec producer python producer.py --num-videos 20 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Prueba de saturación (50, 100, 200 videos):**

```bash
# 50 videos
docker exec producer python producer.py --num-videos 50 --video-file ./assets/dummy_file_50mb.mp4 --no-wait

# Esperar a que se procesen (monitorear en Grafana)

# 100 videos
docker exec producer python producer.py --num-videos 100 --video-file ./assets/dummy_file_50mb.mp4 --no-wait

# 200 videos
docker exec producer python producer.py --num-videos 200 --video-file ./assets/dummy_file_50mb.mp4 --no-wait
```

**Prueba con videos de 100MB:**

```bash
docker exec producer python producer.py --num-videos 10 --video-file ./assets/dummy_file_100mb.mp4 --no-wait
```

---

## Monitoreo y Troubleshooting

### Ver logs en tiempo real

```bash
# Logs del producer
docker logs -f producer

# Logs de Grafana
docker logs -f grafana

# Logs de Prometheus
docker logs -f prometheus

# Logs de JMeter
docker logs -f jmeter

# Logs de renovación de JWT
docker logs -f renew-jwt
```

### Verificar túnel SSH

```bash
# Ver proceso del túnel SSH
ps aux | grep 'ssh.*6379'

# Verificar puerto 6379 local
netstat -tuln | grep 6379

# Probar conexión a Redis
docker exec producer redis-cli -h localhost -p 6379 ping

# Ver longitud de la cola
docker exec producer redis-cli -h localhost -p 6379 LLEN video_processing
```

### Reiniciar túnel SSH

```bash
# Cerrar túnel SSH existente
pkill -f 'ssh.*6379'

# Volver a crear el túnel
cd ~/performance-instance
./setup-ssh-tunnel.sh
```

### Reiniciar servicios

```bash
cd ~/performance-instance

# Reiniciar todos los servicios
docker-compose restart

# Reiniciar un servicio específico
docker-compose restart producer
docker-compose restart grafana
```

### Ver métricas de Prometheus

**Desde tu navegador:**

```
http://<PERFORMANCE_PUBLIC_IP>:9090
```

**Queries útiles:**

```promql
# Tamaño de la cola de Redis
celery_queue_length{queue="video_processing"}

# Tareas completadas
celery_tasks_completed_total

# Requests HTTP al backend
http_requests_total
```

---

## Troubleshooting Común

### Problema 1: El producer no puede conectarse a Redis

**Síntoma:**

```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solución:**

```bash
# Verificar que el túnel SSH está activo
ps aux | grep 'ssh.*6379'

# Si no está activo, recrearlo
./setup-ssh-tunnel.sh

# Verificar que Redis responde en el backend
ssh -i ~/backend-key.pem ubuntu@<BACKEND_PUBLIC_IP> "docker ps | grep redis"
```

### Problema 2: JMeter no puede conectarse a la API

**Síntoma:**

```
Non HTTP response code: java.net.ConnectException
```

**Solución:**

```bash
# Verificar que la API está accesible
curl http://<BACKEND_PUBLIC_IP>/health

# Verificar que el .env tiene la IP correcta
cat .env | grep API_BASE_URL

# Verificar Security Group del backend permite HTTP (80) desde tu IP
```

### Problema 3: Grafana no muestra métricas

**Síntoma:**

```
No data
```

**Solución:**

```bash
# Verificar que Prometheus puede hacer scraping del backend
curl http://<BACKEND_PUBLIC_IP>:8000/metrics

# Verificar configuración de Prometheus
docker exec prometheus cat /etc/prometheus/prometheus.yml

# Ver targets en Prometheus
http://<PERFORMANCE_PUBLIC_IP>:9090/targets
```

### Problema 4: El túnel SSH se cae constantemente

**Síntoma:**

```
Connection reset by peer
```

**Solución:**

```bash
# Usar autossh para mantener el túnel activo
sudo apt install -y autossh

# Crear script persistente
nano ~/start-persistent-tunnel.sh

# Contenido:
#!/bin/bash
source ~/performance-instance/.env
autossh -M 0 -f -N \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -o StrictHostKeyChecking=no \
    -i "$BACKEND_SSH_KEY" \
    -L 6379:localhost:6379 \
    "$BACKEND_SSH_USER@$BACKEND_PUBLIC_IP"

# Dar permisos y ejecutar
chmod +x ~/start-persistent-tunnel.sh
~/start-persistent-tunnel.sh
```

---

## Checklist Final

- [ ] Instancia EC2 `anb-performance-testing` creada
- [ ] Security Group `anb-performance-sg` configurado
- [ ] Docker y Docker Compose instalados
- [ ] Clave SSH del backend copiada y con permisos correctos
- [ ] Archivo `.env` configurado con IPs correctas
- [ ] Túnel SSH a Redis funcionando (`netstat -tuln | grep 6379`)
- [ ] Servicios de Docker Compose corriendo (`docker ps`)
- [ ] Grafana accesible en puerto 3000
- [ ] Producer puede conectarse a Redis (`docker exec producer redis-cli ping`)
- [ ] JMeter puede ejecutar smoke test exitosamente
- [ ] Métricas visibles en Grafana

---

## Comandos de Referencia Rápida

```bash
# Conexión SSH a la instancia de performance
ssh -i "your-key.pem" ubuntu@<PERFORMANCE_PUBLIC_IP>

# Ver estado del túnel SSH
ps aux | grep 'ssh.*6379'

# Recrear túnel SSH
cd ~/performance-instance && ./setup-ssh-tunnel.sh

# Levantar servicios
cd ~/performance-instance && docker-compose up -d

# Ver logs de todos los servicios
docker-compose logs -f

# Ejecutar prueba básica con producer
docker exec producer python producer.py --num-videos 10 --no-wait --debug

# Ejecutar smoke test con JMeter
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"

# Ver tamaño de la cola de Redis
docker exec producer redis-cli -h localhost -p 6379 LLEN video_processing

# Acceder a Grafana
http://<PERFORMANCE_PUBLIC_IP>:3000
Usuario: admin / Password: admin
```

---

**Tiempo estimado total: 2 - 2.5 horas**

¡Éxito con las pruebas de rendimiento! 🚀
