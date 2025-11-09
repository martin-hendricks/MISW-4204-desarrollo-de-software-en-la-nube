#!/bin/bash

# ============================================
# Script de Configuración AWS SQS
# ANB Rising Stars Showcase
# ============================================
#
# Este script crea las colas SQS necesarias para el proyecto
# - Cola principal: anb-video-processing-queue
# - Dead Letter Queue: anb-video-processing-dlq
#
# Requisitos:
# - AWS CLI instalado y configurado
# - Credenciales AWS con permisos para SQS
#
# Uso:
#   ./setup-sqs.sh [AWS_REGION]
#
# Ejemplo:
#   ./setup-sqs.sh us-east-1
#
# ============================================

set -e  # Salir si hay error

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuración
AWS_REGION="${1:-us-east-1}"
DLQ_NAME="anb-video-processing-dlq"
QUEUE_NAME="anb-video-processing-queue"

# ============================================
# Funciones auxiliares
# ============================================

print_header() {
    echo ""
    echo "=================================================="
    echo "$1"
    echo "=================================================="
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "ℹ️  $1"
}

# ============================================
# Verificar prerequisitos
# ============================================

print_header "Verificando prerequisitos"

# Verificar AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI no está instalado"
    echo "Instalar AWS CLI: https://aws.amazon.com/cli/"
    exit 1
fi
print_success "AWS CLI instalado"

# Verificar credenciales AWS
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "Credenciales AWS no configuradas"
    echo "Ejecutar: aws configure"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_success "Credenciales AWS configuradas (Account: $ACCOUNT_ID)"
print_info "Región: $AWS_REGION"

# ============================================
# Crear Dead Letter Queue (DLQ)
# ============================================

print_header "Creando Dead Letter Queue (DLQ)"

# Verificar si DLQ ya existe
if aws sqs get-queue-url --queue-name "$DLQ_NAME" --region "$AWS_REGION" &> /dev/null; then
    print_warning "DLQ '$DLQ_NAME' ya existe"
    DLQ_URL=$(aws sqs get-queue-url --queue-name "$DLQ_NAME" --region "$AWS_REGION" --query QueueUrl --output text)
else
    # Crear DLQ
    DLQ_URL=$(aws sqs create-queue \
        --queue-name "$DLQ_NAME" \
        --region "$AWS_REGION" \
        --attributes '{
            "MessageRetentionPeriod": "1209600",
            "VisibilityTimeout": "3600"
        }' \
        --query QueueUrl \
        --output text)

    print_success "DLQ creada: $DLQ_NAME"
fi

# Obtener ARN de la DLQ
DLQ_ARN=$(aws sqs get-queue-attributes \
    --queue-url "$DLQ_URL" \
    --region "$AWS_REGION" \
    --attribute-names QueueArn \
    --query Attributes.QueueArn \
    --output text)

print_info "DLQ URL: $DLQ_URL"
print_info "DLQ ARN: $DLQ_ARN"

# ============================================
# Crear Cola Principal
# ============================================

print_header "Creando Cola Principal"

# Verificar si cola ya existe
if aws sqs get-queue-url --queue-name "$QUEUE_NAME" --region "$AWS_REGION" &> /dev/null; then
    print_warning "Cola '$QUEUE_NAME' ya existe"
    QUEUE_URL=$(aws sqs get-queue-url --queue-name "$QUEUE_NAME" --region "$AWS_REGION" --query QueueUrl --output text)
else
    # Crear cola principal con redrive policy
    QUEUE_URL=$(aws sqs create-queue \
        --queue-name "$QUEUE_NAME" \
        --region "$AWS_REGION" \
        --attributes "{
            \"MessageRetentionPeriod\": \"345600\",
            \"VisibilityTimeout\": \"3600\",
            \"ReceiveMessageWaitTimeSeconds\": \"20\",
            \"RedrivePolicy\": \"{\\\"deadLetterTargetArn\\\":\\\"$DLQ_ARN\\\",\\\"maxReceiveCount\\\":\\\"3\\\"}\"
        }" \
        --query QueueUrl \
        --output text)

    print_success "Cola principal creada: $QUEUE_NAME"
fi

# Obtener ARN de la cola principal
QUEUE_ARN=$(aws sqs get-queue-attributes \
    --queue-url "$QUEUE_URL" \
    --region "$AWS_REGION" \
    --attribute-names QueueArn \
    --query Attributes.QueueArn \
    --output text)

print_info "Queue URL: $QUEUE_URL"
print_info "Queue ARN: $QUEUE_ARN"

# ============================================
# Guardar configuración
# ============================================

print_header "Guardando configuración"

CONFIG_FILE="sqs-config.env"

cat > "$CONFIG_FILE" <<EOF
# ============================================
# Configuración AWS SQS - ANB Rising Stars
# Generado: $(date)
# ============================================

# Región AWS
AWS_REGION=$AWS_REGION

# Account ID
AWS_ACCOUNT_ID=$ACCOUNT_ID

# Cola Principal
SQS_QUEUE_NAME=$QUEUE_NAME
SQS_QUEUE_URL=$QUEUE_URL
SQS_QUEUE_ARN=$QUEUE_ARN

# Dead Letter Queue
SQS_DLQ_NAME=$DLQ_NAME
SQS_DLQ_URL=$DLQ_URL
SQS_DLQ_ARN=$DLQ_ARN

# ============================================
# Configuración para Backend (.env)
# ============================================
# Copiar estas líneas a: deployment/backend-instance/.env
#
# USE_SQS=true
# AWS_REGION=$AWS_REGION
# SQS_QUEUE_URL=$QUEUE_URL
# SQS_DLQ_URL=$DLQ_URL

# ============================================
# Configuración para Worker (.env)
# ============================================
# Copiar estas líneas a: deployment/worker-instance/.env
#
# USE_SQS=true
# AWS_REGION=$AWS_REGION
# SQS_QUEUE_URL=$QUEUE_URL
# SQS_DLQ_URL=$DLQ_URL
EOF

print_success "Configuración guardada en: $CONFIG_FILE"

# ============================================
# Resumen
# ============================================

print_header "✅ Colas SQS creadas exitosamente"

echo "📋 RESUMEN:"
echo ""
echo "  Región:           $AWS_REGION"
echo "  Account ID:       $ACCOUNT_ID"
echo ""
echo "  Cola Principal:   $QUEUE_NAME"
echo "  URL:              $QUEUE_URL"
echo ""
echo "  Dead Letter Queue: $DLQ_NAME"
echo "  URL:              $DLQ_URL"
echo ""
echo "📄 Archivo de configuración: $CONFIG_FILE"
echo ""

print_header "🔐 Siguientes Pasos"

echo "1️⃣  Configurar permisos IAM:"
echo "   ./setup-iam.sh"
echo ""
echo "2️⃣  Copiar variables a .env del Backend:"
echo "   cp sqs-config.env ../backend-instance/.env.sqs"
echo "   nano ../backend-instance/.env  # Agregar variables SQS"
echo ""
echo "3️⃣  Copiar variables a .env del Worker:"
echo "   cp sqs-config.env ../worker-instance/.env.sqs"
echo "   nano ../worker-instance/.env  # Agregar variables SQS"
echo ""
echo "4️⃣  Actualizar código y requirements.txt (ver README.md)"
echo ""
echo "5️⃣  Desplegar Backend y Worker con USE_SQS=true"
echo ""

print_success "Configuración de SQS completada"
echo ""
