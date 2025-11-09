#!/bin/bash

# ============================================
# Script de Limpieza AWS SQS
# ANB Rising Stars Showcase
# ============================================
#
# Este script ELIMINA las colas SQS y recursos IAM creados
# ⚠️ USAR CON PRECAUCIÓN - Esta acción NO es reversible
#
# Mensajes en las colas se perderán permanentemente
#
# Uso:
#   ./cleanup-sqs.sh [--confirm]
#
# ============================================

set -e  # Salir si hay error

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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
# Verificar confirmación
# ============================================

if [ "$1" != "--confirm" ]; then
    print_warning "⚠️  ADVERTENCIA: Este script eliminará TODAS las colas SQS y recursos IAM"
    echo ""
    echo "Recursos que serán eliminados:"
    echo "  - Cola: anb-video-processing-queue"
    echo "  - Dead Letter Queue: anb-video-processing-dlq"
    echo "  - Política IAM: ANB-SQS-Access-Policy"
    echo "  - Role IAM: ANB-EC2-SQS-Role"
    echo "  - Instance Profile: ANB-EC2-SQS-InstanceProfile"
    echo ""
    print_error "Los mensajes en las colas se perderán PERMANENTEMENTE"
    echo ""
    echo "Para confirmar, ejecutar:"
    echo "  ./cleanup-sqs.sh --confirm"
    echo ""
    exit 1
fi

# ============================================
# Verificar prerequisitos
# ============================================

print_header "Verificando prerequisitos"

# Verificar AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI no está instalado"
    exit 1
fi
print_success "AWS CLI instalado"

# Verificar credenciales AWS
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "Credenciales AWS no configuradas"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
print_success "Credenciales AWS configuradas (Account: $ACCOUNT_ID)"

# Cargar configuración si existe
if [ -f "sqs-config.env" ]; then
    source sqs-config.env
    print_success "Configuración SQS cargada"
else
    print_warning "Archivo sqs-config.env no encontrado, usando valores por defecto"
    SQS_QUEUE_NAME="anb-video-processing-queue"
    SQS_DLQ_NAME="anb-video-processing-dlq"
    IAM_POLICY_NAME="ANB-SQS-Access-Policy"
    IAM_ROLE_NAME="ANB-EC2-SQS-Role"
    IAM_INSTANCE_PROFILE_NAME="ANB-EC2-SQS-InstanceProfile"
fi

# ============================================
# Eliminar Colas SQS
# ============================================

print_header "Eliminando Colas SQS"

# Eliminar cola principal
if aws sqs get-queue-url --queue-name "$SQS_QUEUE_NAME" --region "$AWS_REGION" &> /dev/null; then
    QUEUE_URL=$(aws sqs get-queue-url --queue-name "$SQS_QUEUE_NAME" --region "$AWS_REGION" --query QueueUrl --output text)

    aws sqs delete-queue --queue-url "$QUEUE_URL" --region "$AWS_REGION"
    print_success "Cola eliminada: $SQS_QUEUE_NAME"
else
    print_warning "Cola '$SQS_QUEUE_NAME' no existe"
fi

# Eliminar DLQ
if aws sqs get-queue-url --queue-name "$SQS_DLQ_NAME" --region "$AWS_REGION" &> /dev/null; then
    DLQ_URL=$(aws sqs get-queue-url --queue-name "$SQS_DLQ_NAME" --region "$AWS_REGION" --query QueueUrl --output text)

    aws sqs delete-queue --queue-url "$DLQ_URL" --region "$AWS_REGION"
    print_success "DLQ eliminada: $SQS_DLQ_NAME"
else
    print_warning "DLQ '$SQS_DLQ_NAME' no existe"
fi

# ============================================
# Eliminar Instance Profile
# ============================================

print_header "Eliminando Instance Profile"

if aws iam get-instance-profile --instance-profile-name "$IAM_INSTANCE_PROFILE_NAME" &> /dev/null; then
    # Remover role del instance profile
    aws iam remove-role-from-instance-profile \
        --instance-profile-name "$IAM_INSTANCE_PROFILE_NAME" \
        --role-name "$IAM_ROLE_NAME" &> /dev/null || true

    # Eliminar instance profile
    aws iam delete-instance-profile \
        --instance-profile-name "$IAM_INSTANCE_PROFILE_NAME" &> /dev/null

    print_success "Instance Profile eliminado: $IAM_INSTANCE_PROFILE_NAME"
else
    print_warning "Instance Profile '$IAM_INSTANCE_PROFILE_NAME' no existe"
fi

# ============================================
# Eliminar Role IAM
# ============================================

print_header "Eliminando Role IAM"

if aws iam get-role --role-name "$IAM_ROLE_NAME" &> /dev/null; then
    # Desadjuntar todas las políticas del role
    ATTACHED_POLICIES=$(aws iam list-attached-role-policies \
        --role-name "$IAM_ROLE_NAME" \
        --query 'AttachedPolicies[*].PolicyArn' \
        --output text)

    for policy_arn in $ATTACHED_POLICIES; do
        aws iam detach-role-policy \
            --role-name "$IAM_ROLE_NAME" \
            --policy-arn "$policy_arn" &> /dev/null || true
        print_info "Política desadjuntada: $policy_arn"
    done

    # Eliminar role
    aws iam delete-role --role-name "$IAM_ROLE_NAME" &> /dev/null
    print_success "Role IAM eliminado: $IAM_ROLE_NAME"
else
    print_warning "Role '$IAM_ROLE_NAME' no existe"
fi

# ============================================
# Eliminar Política IAM
# ============================================

print_header "Eliminando Política IAM"

POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${IAM_POLICY_NAME}"

if aws iam get-policy --policy-arn "$POLICY_ARN" &> /dev/null; then
    # Eliminar todas las versiones no-default
    VERSIONS=$(aws iam list-policy-versions \
        --policy-arn "$POLICY_ARN" \
        --query 'Versions[?IsDefaultVersion==`false`].VersionId' \
        --output text)

    for version in $VERSIONS; do
        aws iam delete-policy-version \
            --policy-arn "$POLICY_ARN" \
            --version-id "$version" &> /dev/null || true
        print_info "Versión eliminada: $version"
    done

    # Eliminar política
    aws iam delete-policy --policy-arn "$POLICY_ARN" &> /dev/null
    print_success "Política IAM eliminada: $IAM_POLICY_NAME"
else
    print_warning "Política '$IAM_POLICY_NAME' no existe"
fi

# ============================================
# Limpiar archivos locales
# ============================================

print_header "Limpiando archivos locales"

rm -f sqs-config.env
rm -f iam-policy.json
rm -f trust-policy.json

print_success "Archivos de configuración eliminados"

# ============================================
# Resumen
# ============================================

print_header "✅ Limpieza completada"

echo "📋 Recursos eliminados:"
echo ""
echo "  ✅ Cola SQS: $SQS_QUEUE_NAME"
echo "  ✅ DLQ: $SQS_DLQ_NAME"
echo "  ✅ Instance Profile: $IAM_INSTANCE_PROFILE_NAME"
echo "  ✅ Role IAM: $IAM_ROLE_NAME"
echo "  ✅ Política IAM: $IAM_POLICY_NAME"
echo "  ✅ Archivos de configuración locales"
echo ""

print_warning "Nota: Las instancias EC2 que tenían el Instance Profile asignado"
print_warning "      necesitarán ser reconfiguradas si vuelves a crear los recursos"
echo ""

print_success "Limpieza completada exitosamente"
echo ""
