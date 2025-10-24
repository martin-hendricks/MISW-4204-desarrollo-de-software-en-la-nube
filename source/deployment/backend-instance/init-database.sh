#!/bin/bash
# ======================================================================
# Script de Inicialización de Base de Datos
# ======================================================================
# Ejecuta el archivo init.sql en la base de datos RDS PostgreSQL
#
# Uso:
#   ./init-database.sh
#
# Requisitos:
#   - postgresql-client instalado
#   - Archivo .env configurado con DATABASE_URL
# ======================================================================

set -e

echo "🗄️  Inicializador de Base de Datos ANB Rising Stars"
echo "=================================================="
echo ""

# ===== CONFIGURACIÓN =====
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_FILE="../../database/init.sql"

# Cargar variables de entorno
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "📝 Cargando configuración desde .env..."
    source "$SCRIPT_DIR/.env"
else
    echo "❌ Error: Archivo .env no encontrado"
    echo "   Por favor, crea el archivo .env primero"
    exit 1
fi

# Verificar que DATABASE_URL existe
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Error: DATABASE_URL no está configurado en .env"
    exit 1
fi

# Verificar que existe el archivo SQL
if [ ! -f "$SCRIPT_DIR/$SQL_FILE" ]; then
    echo "❌ Error: Archivo init.sql no encontrado en $SCRIPT_DIR/$SQL_FILE"
    exit 1
fi

# ===== VERIFICAR POSTGRESQL-CLIENT =====
if ! command -v psql &> /dev/null; then
    echo "⚠️  postgresql-client no está instalado"
    echo "   Instalando postgresql-client..."
    sudo apt update
    sudo apt install -y postgresql-client
    echo "✅ postgresql-client instalado"
fi

# ===== EXTRAER DATOS DE CONNECTION STRING =====
# Formato: postgresql://user:password@host:port/database
echo ""
echo "🔍 Parseando DATABASE_URL..."

# Regex para extraer componentes
if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
    DB_USER="${BASH_REMATCH[1]}"
    DB_PASS="${BASH_REMATCH[2]}"
    DB_HOST="${BASH_REMATCH[3]}"
    DB_PORT="${BASH_REMATCH[4]}"
    DB_NAME="${BASH_REMATCH[5]}"

    echo "   Usuario: $DB_USER"
    echo "   Host: $DB_HOST"
    echo "   Puerto: $DB_PORT"
    echo "   Base de datos: $DB_NAME"
else
    echo "❌ Error: DATABASE_URL tiene formato inválido"
    echo "   Formato esperado: postgresql://user:password@host:port/database"
    exit 1
fi

# ===== VERIFICAR CONECTIVIDAD =====
echo ""
echo "🔌 Verificando conectividad con la base de datos..."

if timeout 5 bash -c "echo > /dev/tcp/$DB_HOST/$DB_PORT" 2>/dev/null; then
    echo "✅ Conexión exitosa a $DB_HOST:$DB_PORT"
else
    echo "❌ Error: No se puede conectar a $DB_HOST:$DB_PORT"
    echo "   Verifica:"
    echo "   - El Security Group de RDS permite puerto 5432 desde esta instancia"
    echo "   - El endpoint de RDS es correcto"
    exit 1
fi

# ===== EJECUTAR INIT.SQL =====
echo ""
echo "🚀 Ejecutando init.sql..."
echo "   Archivo: $SQL_FILE"
echo ""
echo "⚠️  ADVERTENCIA: Este script creará las tablas en la base de datos."
echo "   Si las tablas ya existen, puede haber errores (esto es normal)."
echo ""
read -p "¿Continuar? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cancelado por el usuario"
    exit 0
fi

echo ""
echo "📊 Ejecutando SQL..."

# Ejecutar con PGPASSWORD para evitar prompt interactivo
PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -p "$DB_PORT" \
    -f "$SCRIPT_DIR/$SQL_FILE" \
    -v ON_ERROR_STOP=1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ¡Base de datos inicializada exitosamente!"
    echo ""
    echo "📋 Tablas creadas:"
    echo "   - players (jugadores)"
    echo "   - videos (videos)"
    echo "   - votes (votos)"
    echo ""
    echo "🎯 Siguiente paso: Levantar el backend con docker-compose up -d"
else
    echo ""
    echo "❌ Error al ejecutar init.sql"
    echo "   Revisa los mensajes de error arriba"
    exit 1
fi
