# 🚀 Quick Start - Performance Testing Instance

Guía ultra-rápida para configurar tu instancia de performance testing en 30 minutos.

---

## ⚡ Requisitos Rápidos

Obtén de tu compañero:

```bash
BACKEND_PUBLIC_IP: ____________________
BACKEND_SSH_KEY: backend-key.pem
```

---

## 📝 Pasos Rápidos

### 1. Crear EC2 en AWS (5 min)

```
Name: anb-performance-testing
AMI: Ubuntu 22.04
Instance: t2.medium
Security Group: SSH (22) + Custom TCP (3000) desde tu IP
```

### 2. Conectar y configurar (5 min)

```bash
# Conectar
ssh -i "your-key.pem" ubuntu@<PERFORMANCE_IP>

# Instalar Docker
sudo apt update && sudo apt install -y docker.io docker-compose git
sudo usermod -aG docker ubuntu
exit

# Reconectar
ssh -i "your-key.pem" ubuntu@<PERFORMANCE_IP>
```

### 3. Copiar archivos (5 min)

```bash
# Clonar repo
cd ~
git clone https://github.com/TU_REPO/MISW-4204-desarrollo-de-software-en-la-nube.git
cd MISW-4204-desarrollo-de-software-en-la-nube/source/deployment/performance-instance

# Copiar clave SSH del backend (desde tu máquina local)
scp -i "your-key.pem" backend-key.pem ubuntu@<PERFORMANCE_IP>:~/backend-key.pem

# Configurar permisos (en la instancia de performance)
chmod 400 ~/backend-key.pem
```

### 4. Configurar .env (5 min)

```bash
cp .env.example .env
nano .env
```

Completar:
```bash
BACKEND_PUBLIC_IP=3.XXX.XXX.XXX
BACKEND_SSH_KEY=/home/ubuntu/backend-key.pem
API_BASE_URL=http://3.XXX.XXX.XXX
PROMETHEUS_BACKEND_TARGET=3.XXX.XXX.XXX:8000
PROMETHEUS_WORKER_TARGET=3.XXX.XXX.XXX:8001
```

### 5. Configurar Prometheus (2 min)

```bash
nano prometheus.yml
```

Reemplazar `BACKEND_PUBLIC_IP` y `WORKER_PUBLIC_IP` con IPs reales.

### 6. Crear túnel SSH (3 min)

```bash
chmod +x setup-ssh-tunnel.sh
./setup-ssh-tunnel.sh
```

Verificar:
```bash
netstat -tuln | grep 6379
docker run --rm --network host redis:latest redis-cli ping
```

### 7. Levantar servicios (3 min)

```bash
docker-compose up -d
docker ps
```

### 8. Verificar (2 min)

```bash
# Grafana
http://<PERFORMANCE_IP>:3000
# Usuario: admin / Password: admin

# Producer
docker exec producer redis-cli -h localhost -p 6379 ping

# JMeter
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"
```

---

## 🧪 Ejecutar Pruebas

### API (JMeter)

```bash
# Smoke test
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"

# Ramp-up 100 usuarios
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_100_users_results.jtl -Jusers=100"
```

### Worker (Producer)

```bash
# 20 videos
docker exec producer python producer.py --num-videos 20 --no-wait

# 100 videos
docker exec producer python producer.py --num-videos 100 --no-wait
```

---

## 🐛 Problemas Comunes

### Túnel SSH se cae

```bash
pkill -f 'ssh.*6379'
./setup-ssh-tunnel.sh
```

### Producer no conecta a Redis

```bash
ps aux | grep 'ssh.*6379'
netstat -tuln | grep 6379
docker exec producer redis-cli ping
```

### JMeter no conecta a API

```bash
curl http://<BACKEND_IP>/health
cat .env | grep API_BASE_URL
```

---

## 📚 Documentación Completa

Para más detalles, consulta:

- **[DEPLOY.md](./DEPLOY.md)** - Guía completa paso a paso
- **[CHECKLIST.md](./CHECKLIST.md)** - Checklist detallado de verificación
- **[README.md](./README.md)** - Documentación general

---

**Tiempo total: ~30 minutos**

¡Éxito! 🎉
