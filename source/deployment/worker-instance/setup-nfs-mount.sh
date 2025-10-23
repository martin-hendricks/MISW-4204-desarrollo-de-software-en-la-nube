#!/bin/bash

###############################################################################
# Script para montar NFS en la instancia Worker
# Este script monta el volumen NFS compartido donde se almacenan los videos
###############################################################################

set -e  # Salir si hay errores

echo "=========================================="
echo "  Configuración de NFS Client - Worker   "
echo "=========================================="

# ===== CONFIGURACIÓN =====
# IMPORTANTE: Reemplazar con la IP privada de tu servidor NFS
NFS_SERVER_IP="REPLACE_WITH_NFS_PRIVATE_IP"
NFS_EXPORT_PATH="/var/nfs/shared_folder/uploads"
LOCAL_MOUNT_POINT="/mnt/nfs_uploads"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ===== VALIDACIÓN =====
if [ "$NFS_SERVER_IP" = "REPLACE_WITH_NFS_PRIVATE_IP" ]; then
    echo -e "${RED}ERROR: Debes editar este script y reemplazar NFS_SERVER_IP con la IP privada real${NC}"
    echo "Edita el archivo: nano setup-nfs-mount.sh"
    echo "Reemplaza 'REPLACE_WITH_NFS_PRIVATE_IP' con la IP privada del servidor NFS"
    exit 1
fi

# ===== INSTALACIÓN DE NFS CLIENT =====
echo -e "${YELLOW}[1/5] Instalando cliente NFS...${NC}"
sudo apt update
sudo apt install -y nfs-common

# ===== CREACIÓN DEL PUNTO DE MONTAJE =====
echo -e "${YELLOW}[2/5] Creando punto de montaje: $LOCAL_MOUNT_POINT${NC}"
sudo mkdir -p $LOCAL_MOUNT_POINT

# ===== PROBAR CONECTIVIDAD CON EL SERVIDOR NFS =====
echo -e "${YELLOW}[3/5] Probando conectividad con servidor NFS: $NFS_SERVER_IP${NC}"
if ping -c 2 $NFS_SERVER_IP > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Servidor NFS alcanzable${NC}"
else
    echo -e "${RED}✗ No se puede alcanzar el servidor NFS${NC}"
    echo "Verifica:"
    echo "  1. Que la IP es correcta"
    echo "  2. Que el Security Group permite tráfico desde esta instancia"
    echo "  3. Que el servidor NFS está en ejecución"
    exit 1
fi

# ===== VERIFICAR QUE EL EXPORT ESTÁ DISPONIBLE =====
echo -e "${YELLOW}[4/5] Verificando exports NFS disponibles...${NC}"
if showmount -e $NFS_SERVER_IP > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Exports NFS encontrados:${NC}"
    showmount -e $NFS_SERVER_IP
else
    echo -e "${RED}✗ No se pueden listar los exports NFS${NC}"
    echo "Verifica en el servidor NFS:"
    echo "  sudo exportfs -v"
    exit 1
fi

# ===== MONTAR NFS =====
echo -e "${YELLOW}[5/5] Montando NFS...${NC}"

# Desmontar si ya está montado
if mountpoint -q $LOCAL_MOUNT_POINT; then
    echo "NFS ya está montado, desmontando primero..."
    sudo umount $LOCAL_MOUNT_POINT
fi

# Montar
sudo mount -t nfs -o rw,soft,timeo=30,retrans=2 $NFS_SERVER_IP:$NFS_EXPORT_PATH $LOCAL_MOUNT_POINT

# Verificar
if mountpoint -q $LOCAL_MOUNT_POINT; then
    echo -e "${GREEN}✓ NFS montado correctamente${NC}"
    echo "Verificando contenido:"
    ls -la $LOCAL_MOUNT_POINT
else
    echo -e "${RED}✗ Error al montar NFS${NC}"
    exit 1
fi

# ===== CONFIGURACIÓN DE MONTAJE AUTOMÁTICO =====
echo ""
echo -e "${YELLOW}Configurando montaje automático en /etc/fstab...${NC}"

# Backup de fstab
sudo cp /etc/fstab /etc/fstab.backup.$(date +%F_%T)

# Verificar si la entrada ya existe
if grep -q "$NFS_SERVER_IP:$NFS_EXPORT_PATH" /etc/fstab; then
    echo "Entrada ya existe en /etc/fstab"
else
    # Agregar entrada a fstab
    echo "$NFS_SERVER_IP:$NFS_EXPORT_PATH $LOCAL_MOUNT_POINT nfs rw,soft,timeo=30,retrans=2,_netdev 0 0" | sudo tee -a /etc/fstab
    echo -e "${GREEN}✓ Entrada agregada a /etc/fstab${NC}"
fi

# ===== VERIFICACIÓN FINAL =====
echo ""
echo -e "${GREEN}=========================================="
echo "  ✓ Configuración NFS completada"
echo "==========================================${NC}"
echo ""
echo "Información del montaje:"
df -h $LOCAL_MOUNT_POINT
echo ""
echo "Contenido del directorio:"
ls -la $LOCAL_MOUNT_POINT
echo ""
echo -e "${YELLOW}IMPORTANTE: Verifica que puedes ver los mismos archivos que en el Backend${NC}"
echo ""
echo -e "${GREEN}Siguiente paso:${NC} Configurar assets de video (logo, intro, outro)"
echo "  mkdir -p $(dirname $0)/assets"
echo "  # Copiar archivos anb_logo.png, intro.mp4, outro.mp4 a la carpeta assets/"
echo ""
echo -e "${GREEN}Luego:${NC} Levantar Docker Compose"
echo "  cd $(dirname $0)"
echo "  docker-compose up -d"
