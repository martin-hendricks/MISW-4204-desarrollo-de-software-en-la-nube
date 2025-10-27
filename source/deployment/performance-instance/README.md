# Performance Testing Instance - Deployment

Esta carpeta contiene los archivos necesarios para desplegar una instancia de **Performance Testing** en AWS EC2 que se conecta de manera remota al backend de tu compañero para ejecutar pruebas de carga.

## 📁 Archivos en esta carpeta

- **[DEPLOY.md](./DEPLOY.md)** - Guía completa paso a paso para el deployment
- **docker-compose.yml** - Configuración de Docker Compose para producción
- **prometheus.yml** - Configuración de Prometheus para scraping de métricas
- **setup-ssh-tunnel.sh** - Script para crear túnel SSH a Redis del backend remoto
- **.env.example** - Plantilla de variables de entorno

## 🚀 Inicio Rápido

### 1. Lee la guía completa de deployment

➡️ **[DEPLOY.md](./DEPLOY.md)**

Esta guía contiene TODOS los pasos necesarios, incluyendo:

- Creación de la instancia EC2
- Configuración de Security Groups
- Instalación de Docker
- Configuración de túnel SSH a Redis
- Deployment de servicios (Prometheus, Grafana, JMeter, Producer)
- Ejecución de pruebas de carga
- Troubleshooting

### 2. Requisitos previos

Antes de comenzar, asegúrate de tener:

- [ ] Una cuenta de AWS con permisos para crear instancias EC2
- [ ] La IP pública del backend de tu compañero
- [ ] La clave SSH (`.pem`) para acceder al backend de tu compañero
- [ ] El Security Group del backend configurado para permitir SSH desde tu IP

### 3. Datos que necesitas de tu compañero

Tu compañero debe proporcionarte:

```
BACKEND_PUBLIC_IP: _____________________________________________
BACKEND_SSH_KEY: <archivo-clave.pem>
BACKEND_SSH_USER: ubuntu (generalmente)
```

## 🎯 ¿Qué hace esta instancia?

La instancia de Performance Testing ejecuta:

1. **Producer** (Python + Celery Client)
   - Inyecta tareas en la cola de Redis del backend remoto vía SSH tunnel
   - Simula carga de procesamiento de videos

2. **JMeter**
   - Ejecuta pruebas de carga HTTP contra la API del backend
   - Soporta smoke tests, ramp-up tests y sustained tests

3. **Prometheus**
   - Recolecta métricas del backend y worker remotos
   - Almacena datos de rendimiento

4. **Grafana**
   - Visualiza métricas en dashboards interactivos
   - Accesible en puerto 3000

## 📊 Arquitectura

```
┌─────────────────────────────────────┐
│ TU CUENTA AWS                       │
│                                     │
│  ┌───────────────────────────────┐ │
│  │ EC2: Performance Testing      │ │
│  │                               │ │
│  │  • Producer                   │ │
│  │  • JMeter                     │ │
│  │  • Prometheus                 │ │
│  │  • Grafana                    │ │
│  └───────────────────────────────┘ │
│            │                        │
│            │ SSH Tunnel             │
└────────────┼────────────────────────┘
             │
             ▼
┌────────────────────────────────────┐
│ CUENTA DE TU COMPAÑERO             │
│                                    │
│  ┌──────────────────────────────┐ │
│  │ EC2: Backend                 │ │
│  │  • Redis ◄── SSH Tunnel      │ │
│  │  • API ◄── HTTP directo      │ │
│  └──────────────────────────────┘ │
│                                    │
│  ┌──────────────────────────────┐ │
│  │ EC2: Worker                  │ │
│  │  • Celery Worker             │ │
│  └──────────────────────────────┘ │
└────────────────────────────────────┘
```

## 🔧 Configuración Rápida

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/MISW-4204-desarrollo-de-software-en-la-nube.git
cd MISW-4204-desarrollo-de-software-en-la-nube/source/deployment/performance-instance
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
nano .env
```

Completa los valores:
- `BACKEND_PUBLIC_IP` - IP pública del backend de tu compañero
- `API_BASE_URL` - URL de la API (http://IP_BACKEND)
- `BACKEND_SSH_KEY` - Ruta a la clave SSH del backend
- `PROMETHEUS_BACKEND_TARGET` - IP y puerto del backend para métricas (ej: `3.XXX.XXX.XXX:8000`)
- `PROMETHEUS_WORKER_TARGET` - IP y puerto del worker para métricas (ej: `3.YYY.YYY.YYY:8001`)

**Nota:** No necesitas editar `prometheus.yml` manualmente. El script `setup-ssh-tunnel.sh` lo configurará automáticamente usando los valores del `.env`.

### 4. Copiar clave SSH del backend

```bash
# Desde tu máquina local
scp -i "your-key.pem" backend-key.pem ubuntu@<PERFORMANCE_IP>:~/backend-key.pem

# Conectarte a la instancia de performance
ssh -i "your-key.pem" ubuntu@<PERFORMANCE_IP>

# Configurar permisos
chmod 400 ~/backend-key.pem
```

### 5. Crear túnel SSH a Redis y configurar Prometheus

```bash
cd ~/performance-instance
chmod +x setup-ssh-tunnel.sh
./setup-ssh-tunnel.sh
```

**Este script hace dos cosas:**
1. Crea el túnel SSH a Redis del backend
2. Configura automáticamente `prometheus.yml` con las IPs del `.env`

### 6. Levantar servicios

```bash
docker-compose up -d
```

### 7. Verificar

```bash
# Ver servicios
docker ps

# Acceder a Grafana
http://<PERFORMANCE_IP>:3000
Usuario: admin / Password: admin
```

## 📝 Ejecución de Pruebas

### Pruebas de API con JMeter

```bash
# Smoke test
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/smoke_test.jmx -l /scripts/smoke_results.jtl"

# Ramp-up test (100 usuarios)
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/ramp_up_test.jmx -l /scripts/ramp_up_100_users_results.jtl -Jusers=100"

# Sustained test (116 usuarios)
docker exec jmeter /bin/bash -c "jmeter -n -t /scripts/sustained_test.jmx -l /scripts/sustained_116_users_results.jtl -Jusers=116"
```

### Pruebas de Worker con Producer

```bash
# Prueba básica (20 videos)
docker exec producer python producer.py --num-videos 20 --no-wait

# Prueba de saturación (100 videos)
docker exec producer python producer.py --num-videos 100 --no-wait

# Prueba con videos grandes (100MB)
docker exec producer python producer.py --num-videos 10 --video-file ./assets/dummy_file_100mb.mp4 --no-wait
```

## 🐛 Troubleshooting

Ver la sección completa de troubleshooting en [DEPLOY.md](./DEPLOY.md).

## 📚 Recursos Adicionales

- [GET_STARTED.md](../GET_STARTED.md) - Guía de inicio rápido del proyecto
- [../../performance-testing/README.md](../../performance-testing/README.md) - Documentación completa de performance testing
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Arquitectura del sistema

---

**¿Necesitas ayuda?** Consulta [DEPLOY.md](./DEPLOY.md) para la guía completa paso a paso.
