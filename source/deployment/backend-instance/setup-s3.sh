#!/bin/bash

###############################################################################
# Script para configurar S3 como almacenamiento en la instancia Backend
# Este script valida la configuración de S3 y crea el bucket si no existe
###############################################################################

set -e

echo "=========================================="
echo "  Configuración de S3 Storage - Backend  "
echo "=========================================="

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ===== CARGAR VARIABLES DE .env =====
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: Archivo .env no encontrado${NC}"
    echo "Copia .env.example a .env y completa las variables"
    exit 1
fi

# Cargar variables
export $(grep -v '^#' .env | xargs)

# ===== VALIDAR CONFIGURACIÓN =====
echo -e "${YELLOW}[1/4] Validando configuración...${NC}"

if [ "$FILE_STORAGE_TYPE" != "s3" ]; then
    echo -e "${RED}ERROR: FILE_STORAGE_TYPE debe ser 's3' en el archivo .env${NC}"
    echo "Edita .env y cambia: FILE_STORAGE_TYPE=s3"
    exit 1
fi

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$S3_BUCKET_NAME" ]; then
    echo -e "${RED}ERROR: Faltan variables AWS en .env${NC}"
    echo "Configurar: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME"
    exit 1
fi

echo -e "${GREEN}✓ Configuración válida${NC}"
echo "  Bucket: $S3_BUCKET_NAME"
echo "  Región: $AWS_REGION"

# ===== INSTALAR AWS CLI =====
echo -e "${YELLOW}[2/4] Verificando AWS CLI...${NC}"

if ! command -v aws &> /dev/null; then
    echo "Instalando AWS CLI..."
    sudo apt update
    sudo apt install -y awscli
fi

aws --version

# ===== CONFIGURAR AWS CLI =====
echo -e "${YELLOW}[3/4] Configurando credenciales AWS...${NC}"

aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID"
aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
aws configure set default.region "$AWS_REGION"

# ===== VERIFICAR/CREAR BUCKET =====
echo -e "${YELLOW}[4/4] Verificando bucket S3: $S3_BUCKET_NAME${NC}"

if aws s3 ls "s3://$S3_BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    echo "Bucket no existe, creando..."
    aws s3 mb "s3://$S3_BUCKET_NAME" --region "$AWS_REGION"
    echo -e "${GREEN}✓ Bucket creado${NC}"
else
    echo -e "${GREEN}✓ Bucket existe${NC}"
fi

# Crear estructura de carpetas
echo "Creando estructura de carpetas en S3..."
aws s3api put-object --bucket "$S3_BUCKET_NAME" --key original/ --content-length 0 || true
aws s3api put-object --bucket "$S3_BUCKET_NAME" --key processed/ --content-length 0 || true

echo -e "${GREEN}✓ Estructura creada${NC}"

# ===== VERIFICACIÓN FINAL =====
echo ""
echo -e "${GREEN}=========================================="
echo "  ✓ Configuración S3 completada"
echo "==========================================${NC}"
echo ""
echo "Bucket: s3://$S3_BUCKET_NAME"
echo "Región: $AWS_REGION"
echo ""
echo "Contenido del bucket:"
aws s3 ls "s3://$S3_BUCKET_NAME/"
echo ""
echo -e "${YELLOW}IMPORTANTE:${NC} En docker-compose.yml, comentar la línea:"
echo "  # - /mnt/nfs_uploads:/app/uploads"
echo ""
echo -e "${GREEN}Siguiente paso:${NC} Levantar Docker Compose"
echo "  docker-compose up -d"
