# Checklist de Configuración - Performance Testing Instance

Usa este checklist para asegurarte de que todos los pasos estén completos.

---

## 📋 Pre-requisitos (Antes de empezar)

- [ ] Tengo acceso a una cuenta de AWS
- [ ] Tengo la IP pública del backend de mi compañero
- [ ] Tengo la clave SSH (`.pem`) del backend de mi compañero
- [ ] El Security Group del backend permite SSH (22) desde mi IP
- [ ] El Security Group del backend permite HTTP (80) desde mi IP
- [ ] El Security Group del backend permite puerto 8000 desde mi IP (métricas)

---

## 🔧 Paso 1: Crear Infraestructura AWS

- [ ] Security Group `anb-performance-sg` creado
  - [ ] Inbound: SSH (22) desde mi IP
  - [ ] Inbound: Custom TCP (3000) desde mi IP [Grafana]
  - [ ] Outbound: All traffic to 0.0.0.0/0

- [ ] Instancia EC2 `anb-performance-testing` creada
  - [ ] AMI: Ubuntu Server 22.04 LTS
  - [ ] Instance type: t2.medium
  - [ ] Storage: 20 GB (gp3)
  - [ ] Security group: `anb-performance-sg`

- [ ] IPs anotadas:
  ```
  PERFORMANCE_PUBLIC_IP: _______________________________
  BACKEND_PUBLIC_IP: ____________________________________
  ```

---

## 🛠️ Paso 2: Configurar Instancia

- [ ] Docker instalado (`docker --version`)
- [ ] Docker Compose instalado (`docker-compose --version`)
- [ ] Usuario agregado al grupo docker (`groups | grep docker`)
- [ ] Git instalado (`git --version`)

---

## 📁 Paso 3: Copiar Archivos del Proyecto

- [ ] Repositorio clonado o archivos copiados
- [ ] Navegado a la carpeta `performance-instance`
  ```bash
  cd ~/MISW-4204-desarrollo-de-software-en-la-nube/source/deployment/performance-instance
  ```

---

## 🔑 Paso 4: Configurar SSH al Backend

- [ ] Clave SSH del backend copiada a la instancia
  ```bash
  ls -l ~/backend-key.pem
  ```

- [ ] Permisos de la clave corregidos
  ```bash
  chmod 400 ~/backend-key.pem
  stat -c %a ~/backend-key.pem
  # Debe mostrar: 400
  ```

- [ ] Conexión SSH al backend verificada
  ```bash
  ssh -i ~/backend-key.pem ubuntu@<BACKEND_PUBLIC_IP> "echo 'Conexión exitosa'"
  ```

- [ ] Redis corriendo en el backend
  ```bash
  ssh -i ~/backend-key.pem ubuntu@<BACKEND_PUBLIC_IP> "docker ps | grep redis"
  ```

---

## ⚙️ Paso 5: Configurar Variables de Entorno

- [ ] Archivo `.env` creado desde `.env.example`
  ```bash
  cp .env.example .env
  ```

- [ ] Variables completadas en `.env`:
  - [ ] `BACKEND_PUBLIC_IP` = IP pública del backend
  - [ ] `BACKEND_SSH_USER` = ubuntu
  - [ ] `BACKEND_SSH_KEY` = /home/ubuntu/backend-key.pem
  - [ ] `API_BASE_URL` = http://IP_BACKEND
  - [ ] `PROMETHEUS_BACKEND_TARGET` = IP_BACKEND:8000
  - [ ] `PROMETHEUS_WORKER_TARGET` = IP_WORKER:8001

- [ ] Archivo `.env` verificado
  ```bash
  cat .env
  ```

---

## 📊 Paso 6: Configurar Prometheus

- [ ] Archivo `prometheus.yml` editado
- [ ] IP del backend reemplazada en `prometheus.yml`
- [ ] IP del worker reemplazada en `prometheus.yml`
  ```bash
  cat prometheus.yml | grep -v "^#" | grep targets
  ```

---

## 🔌 Paso 7: Crear Túnel SSH a Redis

- [ ] Script de túnel tiene permisos de ejecución
  ```bash
  chmod +x setup-ssh-tunnel.sh
  ```

- [ ] Script de túnel ejecutado exitosamente
  ```bash
  ./setup-ssh-tunnel.sh
  ```

- [ ] Puerto 6379 escuchando localmente
  ```bash
  netstat -tuln | grep 6379
  # Debe mostrar: tcp ... 127.0.0.1:6379 ... LISTEN
  ```

- [ ] Proceso del túnel SSH activo
  ```bash
  ps aux | grep 'ssh.*6379'
  ```

- [ ] Redis responde a través del túnel
  ```bash
  docker run --rm --network host redis:latest redis-cli -h localhost -p 6379 ping
  # Debe responder: PONG
  ```

---

## 🐳 Paso 8: Levantar Servicios con Docker

- [ ] Servicios levantados
  ```bash
  docker-compose up -d
  ```

- [ ] Todos los contenedores corriendo
  ```bash
  docker ps
  # Verificar que estén: grafana, prometheus, jmeter, producer, renew-jwt
  ```

- [ ] Logs del setup JWT exitoso
  ```bash
  docker logs setup-jwt
  # Debe mostrar: JWT token obtenido exitosamente
  ```

- [ ] Servicio de renovación JWT corriendo
  ```bash
  docker logs renew-jwt
  ```

---

## ✅ Paso 9: Verificaciones End-to-End

### 9.1 Grafana

- [ ] Grafana accesible en navegador
  ```
  http://<PERFORMANCE_PUBLIC_IP>:3000
  Usuario: admin / Password: admin
  ```

- [ ] Dashboard del Worker visible
  ```
  http://<PERFORMANCE_PUBLIC_IP>:3000/d/worker-perf/worker-performance-video-processing
  ```

- [ ] Dashboard del Backend visible
  ```
  http://<PERFORMANCE_PUBLIC_IP>:3000/d/backend-api-perf/backend-api-performance
  ```

### 9.2 Prometheus

- [ ] Prometheus accesible (opcional)
  ```
  http://<PERFORMANCE_PUBLIC_IP>:9090
  ```

- [ ] Targets del backend UP
  ```
  http://<PERFORMANCE_PUBLIC_IP>:9090/targets
  ```

### 9.3 Conexión a Redis

- [ ] Producer puede hacer ping a Redis
  ```bash
  docker exec producer redis-cli -h localhost -p 6379 ping
  # Debe responder: PONG
  ```

- [ ] Cola de videos accesible
  ```bash
  docker exec producer redis-cli -h localhost -p 6379 LLEN video_processing
  # Debe responder: (integer) 0 o algún número
  ```

### 9.4 Conexión a la API

- [ ] Health check del backend responde
  ```bash
  curl http://<BACKEND_PUBLIC_IP>/health
  # Debe responder: {"status":"healthy"}
  ```

### 9.5 JMeter

- [ ] Smoke test ejecutado exitosamente
  ```bash
  docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"
  ```

- [ ] Resultados del smoke test generados
  ```bash
  ls -lh ../../performance-testing/web-api-tests/scenarios/scenarios/smoke_results.jtl
  ```

### 9.6 Producer

- [ ] Prueba básica con producer exitosa
  ```bash
  docker exec producer python producer.py --num-videos 5 --no-wait --debug
  ```

- [ ] Tareas encoladas en Redis
  ```bash
  docker exec producer redis-cli -h localhost -p 6379 LLEN video_processing
  # Debe mostrar: (integer) 5 o menos (si ya se procesaron)
  ```

- [ ] Tareas procesadas por el worker (verificar en Grafana)

---

## 🎯 Paso 10: Ejecutar Pruebas de Rendimiento

### Pruebas de API (JMeter)

- [ ] Smoke test completado
  ```bash
  docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"
  ```

- [ ] Ramp-up test con 100 usuarios completado
  ```bash
  docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_100_users_results.jtl -Jusers=100"
  ```

- [ ] Ramp-up test con 200 usuarios completado
  ```bash
  docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_200_users_results.jtl -Jusers=200"
  ```

- [ ] Sustained test completado
  ```bash
  docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/sustained_test.jmx -l /scripts/sustained_116_users_results.jtl -Jusers=116"
  ```

### Pruebas de Worker (Producer)

- [ ] Prueba con 20 videos completada
  ```bash
  docker exec producer python producer.py --num-videos 20 --no-wait
  ```

- [ ] Prueba con 50 videos completada
  ```bash
  docker exec producer python producer.py --num-videos 50 --no-wait
  ```

- [ ] Prueba con 100 videos completada
  ```bash
  docker exec producer python producer.py --num-videos 100 --no-wait
  ```

- [ ] Métricas visibles en Grafana

---

## 📊 Paso 11: Recolectar Resultados

- [ ] Screenshots de dashboards de Grafana guardados
- [ ] Archivos `.jtl` de JMeter descargados
- [ ] Métricas de throughput documentadas
- [ ] Logs de errores (si los hay) guardados

---

## 🐛 Troubleshooting (si algo falla)

### Si el túnel SSH falla:

```bash
# Verificar conectividad
ssh -i ~/backend-key.pem ubuntu@<BACKEND_PUBLIC_IP> "echo test"

# Recrear túnel
pkill -f 'ssh.*6379'
./setup-ssh-tunnel.sh
```

### Si el producer no conecta a Redis:

```bash
# Verificar que el túnel está activo
ps aux | grep 'ssh.*6379'
netstat -tuln | grep 6379

# Verificar que Redis responde
docker exec producer redis-cli -h localhost -p 6379 ping
```

### Si JMeter no puede conectarse a la API:

```bash
# Verificar que la API responde
curl http://<BACKEND_PUBLIC_IP>/health

# Verificar que el .env tiene la IP correcta
cat .env | grep API_BASE_URL
```

### Si Grafana no muestra métricas:

```bash
# Verificar que Prometheus puede hacer scraping
curl http://<BACKEND_PUBLIC_IP>:8000/metrics

# Ver targets en Prometheus
http://<PERFORMANCE_PUBLIC_IP>:9090/targets
```

---

## ✅ Checklist Final

- [ ] Instancia EC2 corriendo
- [ ] Túnel SSH a Redis activo
- [ ] Todos los servicios Docker corriendo
- [ ] Grafana accesible y mostrando métricas
- [ ] Producer puede encolar tareas en Redis
- [ ] JMeter puede ejecutar pruebas contra la API
- [ ] Tareas se procesan correctamente en el worker
- [ ] Métricas visibles en tiempo real

---

**Estado:** _____ de _____ items completados

**Fecha de completación:** ________________

**Notas adicionales:**

_______________________________________________________________

_______________________________________________________________

_______________________________________________________________
