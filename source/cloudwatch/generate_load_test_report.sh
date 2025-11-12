#!/bin/bash
# Script para generar reporte de pruebas de carga usando métricas de CloudWatch
# Uso: ./generate_load_test_report.sh START_TIME END_TIME
# Ejemplo: ./generate_load_test_report.sh "2025-01-15T10:00:00Z" "2025-01-15T10:30:00Z"

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parámetros
START_TIME="${1:-$(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%SZ)}"
END_TIME="${2:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Nombres de servicios (compatibles con Auto Scaling - NO necesitas cambiar IDs)
BACKEND_SERVICE="${BACKEND_SERVICE:-API}"
WORKER_SERVICE="${WORKER_SERVICE:-VideoProcessor}"
QUEUE_NAME="${SQS_QUEUE_NAME:-video-processing-queue}"
DB_INSTANCE="${DB_INSTANCE_ID:-}"

# OPCIONAL: IDs de instancias específicas (solo para métricas EC2 individuales)
BACKEND_INSTANCE="${BACKEND_INSTANCE_ID:-}"
WORKER_INSTANCE="${WORKER_INSTANCE_ID:-}"

echo "============================================="
echo "    LOAD TEST REPORT - CloudWatch Metrics"
echo "============================================="
echo "Period: $START_TIME to $END_TIME"
echo "Region: $AWS_REGION"
echo ""

# Validar que AWS CLI está instalado
if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI no está instalado${NC}"
    exit 1
fi

# Validar credenciales AWS
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}ERROR: Credenciales AWS no configuradas o expiradas${NC}"
    exit 1
fi

echo "=== BACKEND METRICS ==="
echo ""

# Backend: p95 Latency (agregado de TODAS las instancias del servicio)
echo -n "✅ Backend p95 Latency (target: ≤1000ms): "
P95_LATENCY=$(aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name RequestDuration \
  --dimensions Name=Service,Value="$BACKEND_SERVICE" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 1800 \
  --statistics Average \
  --extended-statistics p95 \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].ExtendedStatistics.p95' \
  --output text 2>/dev/null || echo "N/A")

if [ "$P95_LATENCY" != "None" ] && [ "$P95_LATENCY" != "N/A" ]; then
    P95_INT=$(printf "%.0f" "$P95_LATENCY")
    if [ "$P95_INT" -le 1000 ]; then
        echo -e "${GREEN}${P95_LATENCY}ms PASS ✅${NC}"
    else
        echo -e "${RED}${P95_LATENCY}ms FAIL ❌${NC}"
    fi
else
    echo -e "${YELLOW}No data available${NC}"
fi
echo ""

# Backend: Error Rate (agregado de TODAS las instancias del servicio)
echo -n "✅ Backend Error Rate (target: ≤5%): "
ERRORS=$(aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name ErrorCount \
  --dimensions Name=Service,Value="$BACKEND_SERVICE" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 1800 \
  --statistics Sum \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Sum' \
  --output text 2>/dev/null || echo "0")

REQUESTS=$(aws cloudwatch get-metric-statistics \
  --namespace ANB/Backend \
  --metric-name RequestCount \
  --dimensions Name=Service,Value="$BACKEND_SERVICE" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 1800 \
  --statistics Sum \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Sum' \
  --output text 2>/dev/null || echo "0")

if [ "$ERRORS" != "None" ] && [ "$REQUESTS" != "None" ] && [ "$REQUESTS" != "0" ]; then
    ERROR_RATE=$(echo "scale=2; ($ERRORS / $REQUESTS) * 100" | bc)
    ERROR_RATE_INT=$(printf "%.0f" "$ERROR_RATE")
    if [ "$ERROR_RATE_INT" -le 5 ]; then
        echo -e "${GREEN}${ERROR_RATE}% ($ERRORS/$REQUESTS) PASS ✅${NC}"
    else
        echo -e "${RED}${ERROR_RATE}% ($ERRORS/$REQUESTS) FAIL ❌${NC}"
    fi
else
    echo -e "${YELLOW}No data available${NC}"
fi
echo ""

# Backend: CPU Peak
# Nota: EC2 metrics requieren InstanceId individual o usar Auto Scaling Group metrics
echo -n "🔍 Backend CPU Peak: "
if [ -n "$BACKEND_INSTANCE" ]; then
    # Modo instancia específica (útil si no hay Auto Scaling)
    CPU_PEAK=$(aws cloudwatch get-metric-statistics \
      --namespace AWS/EC2 \
      --metric-name CPUUtilization \
      --dimensions Name=InstanceId,Value="$BACKEND_INSTANCE" \
      --start-time "$START_TIME" \
      --end-time "$END_TIME" \
      --period 1800 \
      --statistics Maximum \
      --region "$AWS_REGION" \
      --query 'Datapoints[0].Maximum' \
      --output text 2>/dev/null || echo "N/A")
else
    # Modo Auto Scaling Group (agrega todas las instancias)
    echo -e "${YELLOW}InstanceId not set - use Auto Scaling Group metrics or set BACKEND_INSTANCE_ID${NC}"
    echo ""
    CPU_PEAK="N/A"
fi

if [ "$CPU_PEAK" != "None" ] && [ "$CPU_PEAK" != "N/A" ]; then
    CPU_INT=$(printf "%.0f" "$CPU_PEAK")
    if [ "$CPU_INT" -ge 80 ]; then
        echo -e "${RED}${CPU_PEAK}% (degraded) ⚠️${NC}"
    else
        echo -e "${GREEN}${CPU_PEAK}% (healthy) ✅${NC}"
    fi
    echo ""
fi

# Backend: S3 Throttling Errors
echo -n "✅ Backend S3 Errors (target: 0): "
S3_ERRORS=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name 5xxErrors \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 1800 \
  --statistics Sum \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Sum' \
  --output text 2>/dev/null || echo "0")

if [ "$S3_ERRORS" != "None" ]; then
    S3_ERRORS_INT=$(printf "%.0f" "$S3_ERRORS")
    if [ "$S3_ERRORS_INT" -eq 0 ]; then
        echo -e "${GREEN}0 errors PASS ✅${NC}"
    else
        echo -e "${RED}${S3_ERRORS} errors FAIL ❌${NC}"
    fi
else
    echo -e "${YELLOW}No data available (S3 metrics not enabled)${NC}"
fi
echo ""

echo "=== WORKER METRICS ==="
echo ""

# Worker: Queue Stability
echo "✅ Worker Queue Stability (target: trend ~0):"
START_DEPTH=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value="$QUEUE_NAME" \
  --start-time "$START_TIME" \
  --end-time "$(date -u -d "$START_TIME + 1 minute" +%Y-%m-%dT%H:%M:%SZ)" \
  --period 60 \
  --statistics Average \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Average' \
  --output text 2>/dev/null || echo "0")

END_DEPTH=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateNumberOfMessagesVisible \
  --dimensions Name=QueueName,Value="$QUEUE_NAME" \
  --start-time "$(date -u -d "$END_TIME - 1 minute" +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$END_TIME" \
  --period 60 \
  --statistics Average \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Average' \
  --output text 2>/dev/null || echo "0")

if [ "$START_DEPTH" != "None" ] && [ "$END_DEPTH" != "None" ]; then
    TREND=$(echo "$END_DEPTH - $START_DEPTH" | bc)
    TREND_INT=$(printf "%.0f" "$TREND")

    echo "  Start Queue Depth: $START_DEPTH"
    echo "  End Queue Depth: $END_DEPTH"
    echo -n "  Trend: $TREND "

    if [ "$TREND_INT" -le 10 ] && [ "$TREND_INT" -ge -10 ]; then
        echo -e "${GREEN}(stable) PASS ✅${NC}"
    else
        echo -e "${RED}(unstable) FAIL ❌${NC}"
    fi
else
    echo -e "${YELLOW}No data available${NC}"
fi
echo ""

# Worker: Throughput (agregado de TODAS las instancias del servicio)
echo -n "✅ Worker Throughput (MB/min): "
BYTES=$(aws cloudwatch get-metric-statistics \
  --namespace ANB/Worker \
  --metric-name VideoFileSize \
  --dimensions Name=Service,Value="$WORKER_SERVICE" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 1800 \
  --statistics Sum \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Sum' \
  --output text 2>/dev/null || echo "0")

if [ "$BYTES" != "None" ] && [ "$BYTES" != "0" ]; then
    # Calcular duración en minutos
    START_EPOCH=$(date -d "$START_TIME" +%s 2>/dev/null || echo "0")
    END_EPOCH=$(date -d "$END_TIME" +%s 2>/dev/null || echo "0")
    DURATION=$(echo "($END_EPOCH - $START_EPOCH) / 60" | bc)

    if [ "$DURATION" -eq 0 ]; then
        DURATION=1
    fi

    THROUGHPUT=$(echo "scale=2; ($BYTES / 1024 / 1024) / $DURATION" | bc)
    echo -e "${GREEN}${THROUGHPUT} MB/min${NC}"
else
    echo -e "${YELLOW}No data available${NC}"
fi
echo ""

# Worker: Failed Tasks (agregado de TODAS las instancias del servicio)
echo -n "✅ Worker Failed Tasks: "
FAILED_TASKS=$(aws cloudwatch get-metric-statistics \
  --namespace ANB/Worker \
  --metric-name TaskFailure \
  --dimensions Name=Service,Value="$WORKER_SERVICE" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 1800 \
  --statistics Sum \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Sum' \
  --output text 2>/dev/null || echo "0")

if [ "$FAILED_TASKS" != "None" ]; then
    FAILED_TASKS_INT=$(printf "%.0f" "$FAILED_TASKS")
    if [ "$FAILED_TASKS_INT" -eq 0 ]; then
        echo -e "${GREEN}0 failures PASS ✅${NC}"
    else
        echo -e "${YELLOW}${FAILED_TASKS} failures ⚠️${NC}"
    fi
else
    echo -e "${YELLOW}No data available${NC}"
fi
echo ""

echo "============================================="
echo "    END REPORT"
echo "============================================="
echo ""
echo "💡 Tips:"
echo "   - Métricas custom agregadas por Service (compatible con Auto Scaling)"
echo "   - Variables de entorno opcionales: BACKEND_INSTANCE_ID, WORKER_INSTANCE_ID (solo para CPU individual)"
echo "   - Para Auto Scaling Group CPU: usa AWS/EC2 metrics con dimensión AutoScalingGroupName"
echo "   - Para habilitar métricas S3: ver source/cloudwatch/README.md"
echo ""
echo "🔄 Auto Scaling Compatible:"
echo "   - Custom metrics (p95, error rate, throughput): ✅ Auto-agregadas por Service"
echo "   - SQS metrics: ✅ Auto-agregadas por QueueName"
echo "   - EC2 CPU: ⚠️  Requiere InstanceId específico o Auto Scaling Group metrics"
echo ""
