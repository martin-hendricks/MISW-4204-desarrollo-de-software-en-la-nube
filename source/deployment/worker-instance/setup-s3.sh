#!/bin/bash

###############################################################################
# Script para configurar S3 como almacenamiento en la instancia Worker
#
# NOTA: Este script es OPCIONAL si usas IAM Role (LabRole en AWS Academy)
#
# Opciones de configuración:
# 1. IAM Role (RECOMENDADO): Asigna LabRole a la instancia EC2
#    - No necesitas credenciales en .env
#    - No necesitas ejecutar este script
#    - Más seguro y automático
#
# 2. Credenciales manuales (AWS Academy): Ejecuta este script
#    - Necesitas AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY en .env
#    - Útil para desarrollo local
###############################################################################

set -e

echo "=========================================="
echo "  Configuración de S3 Storage - Worker   "
echo "=========================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ===== CARGAR VARIABLES =====
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: Archivo .env no encontrado${NC}"
    echo "Copia .env.example a .env y completa las variables"
    exit 1
fi

export $(grep -v '^#' .env | xargs)

# ===== VALIDAR =====
echo -e "${YELLOW}[1/3] Validando configuración...${NC}"

if [ "$STORAGE_TYPE" != "s3" ]; then
    echo -e "${RED}ERROR: STORAGE_TYPE debe ser 's3'${NC}"
    echo "Edita .env y cambia: STORAGE_TYPE=s3"
    exit 1
fi

if [ -z "$S3_BUCKET_NAME" ]; then
    echo -e "${RED}ERROR: Falta S3_BUCKET_NAME en .env${NC}"
    exit 1
fi

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo -e "${RED}ERROR: Faltan credenciales AWS en .env${NC}"
    echo "Configurar: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
    exit 1
fi

echo -e "${GREEN}✓ Configuración válida${NC}"
echo "  Bucket: $S3_BUCKET_NAME"
echo "  Región: $AWS_REGION"

# ===== INSTALAR AWS CLI =====
echo -e "${YELLOW}[2/3] Instalando AWS CLI...${NC}"

if ! command -v aws &> /dev/null; then
    echo "Instalando AWS CLI v2..."
    sudo apt-get update
    sudo apt-get install -y curl unzip
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf awscliv2.zip aws
else
    echo "AWS CLI ya está instalado"
fi

aws --version

# ===== CONFIGURAR =====
echo -e "${YELLOW}[3/3] Configurando credenciales...${NC}"
aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID"
aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
aws configure set default.region "$AWS_REGION"

# Configurar session token si existe (AWS Academy)
if [ ! -z "$AWS_SESSION_TOKEN" ]; then
    echo "Configurando AWS Session Token (AWS Academy)..."
    aws configure set aws_session_token "$AWS_SESSION_TOKEN"
fi

# ===== VERIFICAR ACCESO =====
echo "Verificando acceso al bucket..."
if aws s3 ls "s3://$S3_BUCKET_NAME/" &> /dev/null; then
    echo -e "${GREEN}✓ Acceso a S3 confirmado${NC}"
    echo ""
    echo "Contenido del bucket:"
    aws s3 ls "s3://$S3_BUCKET_NAME/"
else
    echo -e "${RED}✗ No se puede acceder al bucket${NC}"
    echo "Verifica que el bucket existe y las credenciales son correctas"
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "  ✓ Configuración S3 completada"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}IMPORTANTE:${NC} En docker-compose.yml, comentar:"
echo "  # - /mnt/nfs_uploads:/app/uploads"
echo ""
echo -e "${GREEN}Siguiente paso:${NC} Configurar assets (logo, intro, outro)"
echo "  mkdir -p assets"
echo "  # Copiar archivos anb_logo.png, intro.mp4, outro.mp4"
echo ""
echo -e "${GREEN}Luego:${NC} Levantar Docker Compose"
echo "  docker-compose up -d"
