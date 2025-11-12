#!/bin/bash
# Script para generar reporte de pruebas de carga usando SOLO métricas FREE
# Uso: ./generate_free_metrics_report.sh START_TIME END_TIME
# Ejemplo: ./generate_free_metrics_report.sh "2025-01-15T10:00:00Z" "2025-01-15T10:30:00Z"

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

# IDs de recursos (configurar según tu infraestructura)
BACKEND_INSTANCE="${BACKEND_INSTANCE_ID:-}"
WORKER_INSTANCE="${WORKER_INSTANCE_ID:-}"
QUEUE_NAME="${SQS_QUEUE_NAME:-video-processing-queue}"

echo "============================================="
echo "    FREE METRICS LOAD TEST REPORT"
echo "============================================="
echo "Period: $START_TIME to $END_TIME"
echo "Region: $AWS_REGION"
echo "Cost: $0 (100% FREE AWS Native Metrics)"
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

echo "=== BACKEND METRICS (EC2 - FREE) ==="
echo ""

# Backend: CPU Peak
if [ -n "$BACKEND_INSTANCE" ]; then
    echo -n "🔍 Backend CPU Peak: "
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

    if [ "$CPU_PEAK" != "None" ] && [ "$CPU_PEAK" != "N/A" ]; then
        CPU_INT=$(printf "%.0f" "$CPU_PEAK")
        if [ "$CPU_INT" -ge 80 ]; then
            echo -e "${RED}${CPU_PEAK}% (degraded) ⚠️${NC}"
        else
            echo -e "${GREEN}${CPU_PEAK}% (healthy) ✅${NC}"
        fi
    else
        echo -e "${YELLOW}No data available${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  BACKEND_INSTANCE_ID not set${NC}"
fi
echo ""

# Backend: Memory Peak (CWAgent)
if [ -n "$BACKEND_INSTANCE" ]; then
    echo -n "🔍 Backend Memory Peak: "
    MEM_PEAK=$(aws cloudwatch get-metric-statistics \
      --namespace CWAgent \
      --metric-name mem_used_percent \
      --dimensions Name=InstanceId,Value="$BACKEND_INSTANCE" \
      --start-time "$START_TIME" \
      --end-time "$END_TIME" \
      --period 1800 \
      --statistics Maximum \
      --region "$AWS_REGION" \
      --query 'Datapoints[0].Maximum' \
      --output text 2>/dev/null || echo "N/A")

    if [ "$MEM_PEAK" != "None" ] && [ "$MEM_PEAK" != "N/A" ]; then
        MEM_INT=$(printf "%.0f" "$MEM_PEAK")
        if [ "$MEM_INT" -ge 90 ]; then
            echo -e "${RED}${MEM_PEAK}% (degraded) ⚠️${NC}"
        else
            echo -e "${GREEN}${MEM_PEAK}% (healthy) ✅${NC}"
        fi
    else
        echo -e "${YELLOW}No data available (install CWAgent)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  BACKEND_INSTANCE_ID not set${NC}"
fi
echo ""

# Backend: Network In
if [ -n "$BACKEND_INSTANCE" ]; then
    echo -n "🔍 Backend Network In: "
    NET_IN=$(aws cloudwatch get-metric-statistics \
      --namespace AWS/EC2 \
      --metric-name NetworkIn \
      --dimensions Name=InstanceId,Value="$BACKEND_INSTANCE" \
      --start-time "$START_TIME" \
      --end-time "$END_TIME" \
      --period 1800 \
      --statistics Sum \
      --region "$AWS_REGION" \
      --query 'Datapoints[0].Sum' \
      --output text 2>/dev/null || echo "0")

    if [ "$NET_IN" != "None" ] && [ "$NET_IN" != "0" ]; then
        NET_IN_MB=$(echo "scale=2; $NET_IN / 1024 / 1024" | bc)
        echo -e "${GREEN}${NET_IN_MB} MB${NC}"
    else
        echo -e "${YELLOW}No data available${NC}"
    fi
fi
echo ""

echo "=== WORKER METRICS (SQS - FREE) ==="
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

# Worker: Messages Processed
echo -n "✅ Worker Messages Processed: "
PROCESSED=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name NumberOfMessagesDeleted \
  --dimensions Name=QueueName,Value="$QUEUE_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 1800 \
  --statistics Sum \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Sum' \
  --output text 2>/dev/null || echo "0")

if [ "$PROCESSED" != "None" ] && [ "$PROCESSED" != "0" ]; then
    echo -e "${GREEN}${PROCESSED} messages${NC}"
else
    echo -e "${YELLOW}No messages processed${NC}"
fi
echo ""

# Worker: Processing Latency
echo -n "✅ Worker Max Processing Latency: "
MAX_AGE=$(aws cloudwatch get-metric-statistics \
  --namespace AWS/SQS \
  --metric-name ApproximateAgeOfOldestMessage \
  --dimensions Name=QueueName,Value="$QUEUE_NAME" \
  --start-time "$START_TIME" \
  --end-time "$END_TIME" \
  --period 1800 \
  --statistics Maximum \
  --region "$AWS_REGION" \
  --query 'Datapoints[0].Maximum' \
  --output text 2>/dev/null || echo "0")

if [ "$MAX_AGE" != "None" ] && [ "$MAX_AGE" != "0" ]; then
    MAX_AGE_INT=$(printf "%.0f" "$MAX_AGE")
    MAX_AGE_MIN=$(echo "scale=2; $MAX_AGE / 60" | bc)

    if [ "$MAX_AGE_INT" -ge 900 ]; then
        echo -e "${RED}${MAX_AGE_MIN} minutes (slow) ⚠️${NC}"
    else
        echo -e "${GREEN}${MAX_AGE_MIN} minutes (healthy) ✅${NC}"
    fi
else
    echo -e "${YELLOW}No data available${NC}"
fi
echo ""

# Worker: CPU Peak
if [ -n "$WORKER_INSTANCE" ]; then
    echo -n "🔍 Worker CPU Peak: "
    CPU_PEAK=$(aws cloudwatch get-metric-statistics \
      --namespace AWS/EC2 \
      --metric-name CPUUtilization \
      --dimensions Name=InstanceId,Value="$WORKER_INSTANCE" \
      --start-time "$START_TIME" \
      --end-time "$END_TIME" \
      --period 1800 \
      --statistics Maximum \
      --region "$AWS_REGION" \
      --query 'Datapoints[0].Maximum' \
      --output text 2>/dev/null || echo "N/A")

    if [ "$CPU_PEAK" != "None" ] && [ "$CPU_PEAK" != "N/A" ]; then
        CPU_INT=$(printf "%.0f" "$CPU_PEAK")
        if [ "$CPU_INT" -ge 80 ]; then
            echo -e "${RED}${CPU_PEAK}% (degraded) ⚠️${NC}"
        else
            echo -e "${GREEN}${CPU_PEAK}% (healthy) ✅${NC}"
        fi
    else
        echo -e "${YELLOW}No data available${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  WORKER_INSTANCE_ID not set${NC}"
fi
echo ""

echo "=== S3 METRICS (FREE) ==="
echo ""

# S3 Throttling Errors
echo -n "✅ S3 Errors (target: 0): "
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
    echo -e "${YELLOW}No data available (S3 Request Metrics not enabled)${NC}"
fi
echo ""

echo "============================================="
echo "    END REPORT"
echo "============================================="
echo ""
echo "💡 Tips:"
echo "   - Configure variables: BACKEND_INSTANCE_ID, WORKER_INSTANCE_ID, SQS_QUEUE_NAME"
echo "   - Enable EC2 monitoring: aws ec2 monitor-instances --instance-ids i-XXXXX"
echo "   - Install CWAgent for memory metrics: see source/cloudwatch/README.md"
echo "   - Enable S3 Request Metrics: S3 Console → Bucket → Metrics → Request metrics"
echo ""
echo "📊 Cost Breakdown:"
echo "   - EC2 Metrics (CPUUtilization, NetworkIn): $0 (FREE)"
echo "   - CWAgent Metrics (mem_used_percent): $0 (FREE)"
echo "   - SQS Metrics (ApproximateNumberOfMessagesVisible): $0 (FREE)"
echo "   - S3 Metrics (5xxErrors): $0 (FREE)"
echo "   - TOTAL: $0"
echo ""
