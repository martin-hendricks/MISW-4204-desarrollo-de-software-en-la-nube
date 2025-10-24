#!/bin/bash

# ================================================================
# Script para configurar túnel SSH a Redis del backend remoto
# ================================================================
# Este script crea un túnel SSH que permite conectarse a Redis
# (puerto 6379) del servidor backend de tu compañero desde tu
# instancia de performance testing.
# ================================================================

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "  Configuración de Túnel SSH a Redis"
echo "=========================================="
echo ""

# Verificar que existe el archivo .env
if [ ! -f ".env" ]; then
    log_error "No se encontró el archivo .env"
    log_error "Por favor crea el archivo .env con las variables necesarias"
    log_error "Puedes usar .env.example como plantilla"
    exit 1
fi

# Cargar variables de entorno
log_info "Cargando variables de entorno desde .env..."
source .env

# Verificar que las variables necesarias están configuradas
if [ -z "$BACKEND_PUBLIC_IP" ]; then
    log_error "BACKEND_PUBLIC_IP no está configurado en .env"
    exit 1
fi

if [ -z "$BACKEND_SSH_USER" ]; then
    log_error "BACKEND_SSH_USER no está configurado en .env"
    exit 1
fi

if [ -z "$BACKEND_SSH_KEY" ]; then
    log_error "BACKEND_SSH_KEY no está configurado en .env"
    exit 1
fi

log_info "Configuración cargada:"
echo "  - Backend IP: $BACKEND_PUBLIC_IP"
echo "  - SSH User: $BACKEND_SSH_USER"
echo "  - SSH Key: $BACKEND_SSH_KEY"
echo ""

# Verificar que la clave SSH existe
if [ ! -f "$BACKEND_SSH_KEY" ]; then
    log_error "La clave SSH no existe en: $BACKEND_SSH_KEY"
    log_error "Por favor copia la clave SSH del backend a esta ubicación"
    exit 1
fi

# Verificar permisos de la clave SSH
PERMS=$(stat -c %a "$BACKEND_SSH_KEY" 2>/dev/null || stat -f %A "$BACKEND_SSH_KEY")
if [ "$PERMS" != "400" ]; then
    log_warning "Los permisos de la clave SSH no son 400 (actual: $PERMS)"
    log_info "Corrigiendo permisos..."
    chmod 400 "$BACKEND_SSH_KEY"
    log_success "Permisos corregidos a 400"
fi

# Verificar conectividad SSH al backend
log_info "Probando conexión SSH al backend..."
echo ""

if ssh -i "$BACKEND_SSH_KEY" \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=no \
    -o BatchMode=yes \
    "$BACKEND_SSH_USER@$BACKEND_PUBLIC_IP" \
    "echo 'Conexión SSH exitosa'" 2>/dev/null; then
    log_success "Conexión SSH al backend exitosa"
else
    log_error "No se pudo conectar al backend via SSH"
    echo ""
    log_error "Verifica lo siguiente:"
    echo "  1. La IP pública del backend es correcta: $BACKEND_PUBLIC_IP"
    echo "  2. La clave SSH es correcta: $BACKEND_SSH_KEY"
    echo "  3. El usuario SSH es correcto: $BACKEND_SSH_USER"
    echo "  4. El Security Group del backend permite SSH (22) desde tu IP"
    echo ""
    log_info "Intentando conexión con modo debug para más información..."
    ssh -vvv -i "$BACKEND_SSH_KEY" \
        -o ConnectTimeout=10 \
        -o StrictHostKeyChecking=no \
        "$BACKEND_SSH_USER@$BACKEND_PUBLIC_IP" \
        "echo test" 2>&1 | tail -20
    exit 1
fi

# Verificar que Redis está corriendo en el backend
log_info "Verificando que Redis está corriendo en el backend..."
if ssh -i "$BACKEND_SSH_KEY" \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=no \
    "$BACKEND_SSH_USER@$BACKEND_PUBLIC_IP" \
    "docker ps | grep redis" &>/dev/null; then
    log_success "Redis está corriendo en el backend"
else
    log_warning "No se pudo verificar que Redis esté corriendo"
    log_warning "Asegúrate de que Docker y Redis estén activos en el backend"
fi

echo ""
log_info "Cerrando cualquier túnel SSH existente al puerto 6379..."

# Cerrar cualquier túnel SSH existente
pkill -f "ssh.*$BACKEND_PUBLIC_IP.*6379" 2>/dev/null || true
sleep 2

# Verificar que el puerto 6379 no está en uso
if netstat -tuln 2>/dev/null | grep -q ":6379 " || \
   lsof -i :6379 2>/dev/null | grep -q LISTEN; then
    log_warning "El puerto 6379 ya está en uso"
    log_info "Intentando liberar el puerto..."

    # Intentar matar el proceso que está usando el puerto
    REDIS_PID=$(lsof -ti:6379 2>/dev/null || true)
    if [ -n "$REDIS_PID" ]; then
        kill -9 $REDIS_PID 2>/dev/null || true
        sleep 2
    fi
fi

echo ""
log_info "Creando túnel SSH a Redis (puerto 6379)..."
log_info "El túnel se ejecutará en segundo plano"

# Crear túnel SSH a Redis
# -f: ejecutar en background
# -N: no ejecutar comandos remotos (solo túnel)
# -L: port forwarding local (6379:localhost:6379)
# ServerAliveInterval: enviar paquete keep-alive cada 60 segundos
# ServerAliveCountMax: número máximo de paquetes sin respuesta antes de desconectar
# ExitOnForwardFailure: salir si no se puede crear el túnel
# StrictHostKeyChecking: no preguntar por hosts desconocidos
if ssh -f -N \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    -o StrictHostKeyChecking=no \
    -i "$BACKEND_SSH_KEY" \
    -L 6379:localhost:6379 \
    "$BACKEND_SSH_USER@$BACKEND_PUBLIC_IP"; then

    log_success "Túnel SSH creado exitosamente"
    echo ""

    # Esperar un momento para que el túnel se establezca
    log_info "Esperando a que el túnel se establezca..."
    sleep 3

    # Verificar que el puerto 6379 está escuchando
    if netstat -tuln 2>/dev/null | grep -q ":6379 " || \
       lsof -i :6379 2>/dev/null | grep -q LISTEN; then
        log_success "El puerto 6379 está abierto localmente"
        echo ""

        # Intentar hacer ping a Redis
        log_info "Verificando conexión a Redis..."
        if docker run --rm --network host redis:latest redis-cli -h localhost -p 6379 ping 2>/dev/null | grep -q PONG; then
            log_success "Redis responde correctamente"
        else
            log_warning "No se pudo hacer ping a Redis"
            log_warning "Es posible que Redis no esté aceptando conexiones externas"
        fi

        echo ""
        echo "=========================================="
        log_success "Túnel SSH configurado correctamente"
        echo "=========================================="
        echo ""
        log_info "Comandos útiles:"
        echo ""
        echo "  Ver el proceso del túnel SSH:"
        echo "    ps aux | grep 'ssh.*6379'"
        echo ""
        echo "  Verificar que el puerto 6379 está escuchando:"
        echo "    netstat -tuln | grep 6379"
        echo ""
        echo "  Probar conexión a Redis:"
        echo "    docker run --rm --network host redis:latest redis-cli -h localhost -p 6379 ping"
        echo ""
        echo "  Ver tamaño de la cola de videos:"
        echo "    docker run --rm --network host redis:latest redis-cli -h localhost -p 6379 LLEN video_processing"
        echo ""
        echo "  Cerrar el túnel:"
        echo "    pkill -f 'ssh.*6379'"
        echo ""
    else
        log_error "El puerto 6379 no está escuchando"
        log_error "El túnel SSH puede no haberse creado correctamente"

        echo ""
        log_info "Verificando logs de SSH..."
        ps aux | grep ssh | grep 6379

        exit 1
    fi
else
    log_error "No se pudo crear el túnel SSH"
    log_error "Verifica:"
    echo "  1. Que puedes conectarte por SSH al backend"
    echo "  2. Que el puerto 6379 no está bloqueado por firewall"
    echo "  3. Que tienes permisos suficientes"
    exit 1
fi

echo "=========================================="
echo ""
