#!/bin/bash

# ============================================
# Script de Configuración IAM para SQS
# ANB Rising Stars Showcase
# ============================================
#
# Este script configura los permisos IAM necesarios para que las instancias EC2
# puedan acceder a las colas SQS
#
# Requisitos:
# - AWS CLI instalado y configurado
# - Credenciales AWS con permisos administrativos
# - Haber ejecutado setup-sqs.sh primero
#
# Uso:
#   ./setup-iam.sh
#
# ============================================

set -e  # Salir si hay error

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuración
POLICY_NAME="ANB-SQS-Access-Policy"
ROLE_NAME="ANB-EC2-SQS-Role"
INSTANCE_PROFILE_NAME="ANB-EC2-SQS-InstanceProfile"

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

# Cargar configuración de SQS
if [ ! -f "sqs-config.env" ]; then
    print_error "Archivo sqs-config.env no encontrado"
    echo "Ejecutar primero: ./setup-sqs.sh"
    exit 1
fi

source sqs-config.env
print_success "Configuración SQS cargada"

# ============================================
# Crear Política IAM
# ============================================

print_header "Creando Política IAM"

# Crear archivo de política
cat > iam-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowSQSAccess",
            "Effect": "Allow",
            "Action": [
                "sqs:SendMessage",
                "sqs:ReceiveMessage",
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "sqs:GetQueueUrl",
                "sqs:ChangeMessageVisibility",
                "sqs:ChangeMessageVisibilityBatch"
            ],
            "Resource": [
                "$SQS_QUEUE_ARN",
                "$SQS_DLQ_ARN"
            ]
        },
        {
            "Sid": "AllowListQueues",
            "Effect": "Allow",
            "Action": [
                "sqs:ListQueues"
            ],
            "Resource": "*"
        }
    ]
}
EOF

print_success "Archivo de política creado: iam-policy.json"

# Verificar si la política ya existe
if aws iam get-policy --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}" &> /dev/null; then
    print_warning "Política IAM '$POLICY_NAME' ya existe"

    # Actualizar política existente
    POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

    # Obtener versión actual
    CURRENT_VERSION=$(aws iam list-policy-versions \
        --policy-arn "$POLICY_ARN" \
        --query 'Versions[?IsDefaultVersion==`true`].VersionId' \
        --output text)

    # Crear nueva versión
    aws iam create-policy-version \
        --policy-arn "$POLICY_ARN" \
        --policy-document file://iam-policy.json \
        --set-as-default &> /dev/null || true

    print_success "Política IAM actualizada"
else
    # Crear nueva política
    POLICY_ARN=$(aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document file://iam-policy.json \
        --description "Permisos para acceder a colas SQS de ANB Rising Stars" \
        --query Policy.Arn \
        --output text)

    print_success "Política IAM creada: $POLICY_NAME"
fi

print_info "Policy ARN: $POLICY_ARN"

# ============================================
# Crear Role IAM
# ============================================

print_header "Creando Role IAM"

# Crear trust policy para EC2
cat > trust-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Verificar si el role ya existe
if aws iam get-role --role-name "$ROLE_NAME" &> /dev/null; then
    print_warning "Role IAM '$ROLE_NAME' ya existe"
    ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query Role.Arn --output text)
else
    # Crear role
    ROLE_ARN=$(aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file://trust-policy.json \
        --description "Role para instancias EC2 que acceden a SQS" \
        --query Role.Arn \
        --output text)

    print_success "Role IAM creado: $ROLE_NAME"
fi

print_info "Role ARN: $ROLE_ARN"

# ============================================
# Adjuntar Política al Role
# ============================================

print_header "Adjuntando Política al Role"

aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN" &> /dev/null || true

print_success "Política adjuntada al Role"

# ============================================
# Crear Instance Profile
# ============================================

print_header "Creando Instance Profile"

# Verificar si el instance profile ya existe
if aws iam get-instance-profile --instance-profile-name "$INSTANCE_PROFILE_NAME" &> /dev/null; then
    print_warning "Instance Profile '$INSTANCE_PROFILE_NAME' ya existe"
else
    # Crear instance profile
    aws iam create-instance-profile \
        --instance-profile-name "$INSTANCE_PROFILE_NAME" &> /dev/null

    print_success "Instance Profile creado: $INSTANCE_PROFILE_NAME"

    # Adjuntar role al instance profile
    aws iam add-role-to-instance-profile \
        --instance-profile-name "$INSTANCE_PROFILE_NAME" \
        --role-name "$ROLE_NAME" &> /dev/null

    print_success "Role adjuntado al Instance Profile"
fi

# ============================================
# Guardar configuración IAM
# ============================================

print_header "Guardando configuración IAM"

cat >> sqs-config.env <<EOF

# ============================================
# Configuración IAM
# ============================================
IAM_POLICY_NAME=$POLICY_NAME
IAM_POLICY_ARN=$POLICY_ARN
IAM_ROLE_NAME=$ROLE_NAME
IAM_ROLE_ARN=$ROLE_ARN
IAM_INSTANCE_PROFILE_NAME=$INSTANCE_PROFILE_NAME
EOF

print_success "Configuración IAM guardada en: sqs-config.env"

# ============================================
# Resumen
# ============================================

print_header "✅ Configuración IAM completada"

echo "📋 RESUMEN:"
echo ""
echo "  Política IAM:       $POLICY_NAME"
echo "  Policy ARN:         $POLICY_ARN"
echo ""
echo "  Role IAM:           $ROLE_NAME"
echo "  Role ARN:           $ROLE_ARN"
echo ""
echo "  Instance Profile:   $INSTANCE_PROFILE_NAME"
echo ""

print_header "🔐 Siguientes Pasos"

echo "1️⃣  Adjuntar Instance Profile a instancias EC2 existentes:"
echo ""
echo "   # Backend Instance"
echo "   aws ec2 associate-iam-instance-profile \\"
echo "     --instance-id i-XXXXXXXXX \\"
echo "     --iam-instance-profile Name=$INSTANCE_PROFILE_NAME"
echo ""
echo "   # Worker Instance"
echo "   aws ec2 associate-iam-instance-profile \\"
echo "     --instance-id i-YYYYYYYYY \\"
echo "     --iam-instance-profile Name=$INSTANCE_PROFILE_NAME"
echo ""
echo "2️⃣  O crear nuevas instancias con el Instance Profile:"
echo ""
echo "   aws ec2 run-instances \\"
echo "     --iam-instance-profile Name=$INSTANCE_PROFILE_NAME \\"
echo "     --image-id ami-XXXXXXXXX \\"
echo "     --instance-type t2.medium \\"
echo "     ..."
echo ""
echo "3️⃣  Verificar que las instancias tienen el perfil:"
echo ""
echo "   aws ec2 describe-instances \\"
echo "     --instance-ids i-XXXXXXXXX \\"
echo "     --query 'Reservations[0].Instances[0].IamInstanceProfile'"
echo ""
echo "4️⃣  Desde dentro de la instancia EC2, verificar permisos:"
echo ""
echo "   # Conectar a la instancia"
echo "   ssh -i key.pem ubuntu@<EC2_PUBLIC_IP>"
echo ""
echo "   # Verificar credenciales"
echo "   aws sts get-caller-identity"
echo ""
echo "   # Listar colas (debe funcionar)"
echo "   aws sqs list-queues"
echo ""

print_success "Configuración de IAM completada"
echo ""
