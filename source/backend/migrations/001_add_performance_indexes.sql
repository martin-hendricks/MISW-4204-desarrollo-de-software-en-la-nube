-- ======================================================================
-- Migración 001: Índices de Optimización de Performance
-- ======================================================================
-- IDEMPOTENTE: Puede ejecutarse múltiples veces sin causar errores
-- Uso:
--   psql -d fileprocessing -f 001_add_performance_indexes.sql
-- ======================================================================

BEGIN;

-- Verificar si ya se aplicó esta migración
DO $$
BEGIN
    -- Crear tabla de migraciones si no existe
    CREATE TABLE IF NOT EXISTS schema_migrations (
        version VARCHAR(50) PRIMARY KEY,
        applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        description TEXT
    );

    -- Verificar si esta migración ya se ejecutó
    IF EXISTS (SELECT 1 FROM schema_migrations WHERE version = '001') THEN
        RAISE NOTICE 'Migración 001 ya fue aplicada anteriormente. Verificando índices...';
    ELSE
        RAISE NOTICE 'Aplicando migración 001: Índices de optimización de performance';
    END IF;
END $$;

-- ======================================================================
-- ÍNDICES DE OPTIMIZACIÓN (idempotentes con IF NOT EXISTS)
-- ======================================================================

-- 1. Índice en players.email (ya existe por UNIQUE)
CREATE INDEX IF NOT EXISTS idx_players_email ON players(email);

-- 2. Índice en videos.player_id para JOIN rápido
CREATE INDEX IF NOT EXISTS idx_videos_player_id ON videos(player_id);

-- 3. Índice en videos.status para optimizar filtros
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);

-- 4. Índice en videos.uploaded_at para ordenamiento
CREATE INDEX IF NOT EXISTS idx_videos_uploaded_at ON videos(uploaded_at DESC);

-- 5. Índice compuesto en videos(status, uploaded_at) - cubre query completa
CREATE INDEX IF NOT EXISTS idx_videos_status_uploaded ON videos(status, uploaded_at DESC);

-- 6. Índice en votes.video_id para conteo de votos
CREATE INDEX IF NOT EXISTS idx_votes_video_id ON votes(video_id);

-- 7. Índice en votes.player_id para buscar votos de usuario
CREATE INDEX IF NOT EXISTS idx_votes_player_id ON votes(player_id);

-- 8. Índice compuesto en votes(video_id, player_id) para verificación rápida
CREATE INDEX IF NOT EXISTS idx_votes_video_player ON votes(video_id, player_id);

-- Registrar migración como aplicada
INSERT INTO schema_migrations (version, description)
VALUES ('001', 'Índices de optimización de performance para soportar 500+ usuarios')
ON CONFLICT (version) DO NOTHING;

COMMIT;

-- ======================================================================
-- VERIFICACIÓN
-- ======================================================================
\echo ''
\echo '✅ Migración 001 completada'
\echo ''
\echo '📋 Índices creados:'

SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('videos', 'votes', 'players')
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

\echo ''
\echo '📊 Historial de migraciones:'
SELECT version, description, applied_at FROM schema_migrations ORDER BY version;
