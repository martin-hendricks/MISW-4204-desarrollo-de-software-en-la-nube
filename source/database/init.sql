-- ======================================================================
-- Script de Inicialización de Base de Datos ANB Rising Stars
-- Incluye optimizaciones de performance para soportar 500+ usuarios
-- ======================================================================

CREATE TYPE video_status AS ENUM ('uploaded', 'processed');

CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    status video_status NOT NULL DEFAULT 'uploaded',
    original_url VARCHAR(512),
    processed_url VARCHAR(512),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_vote UNIQUE (player_id, video_id)
);

-- ======================================================================
-- ÍNDICES DE OPTIMIZACIÓN DE PERFORMANCE
-- ======================================================================
-- Estos índices mejoran significativamente el rendimiento con 250+ usuarios

-- Índice en players.email (ya existe por UNIQUE, pero lo declaramos explícito)
CREATE INDEX IF NOT EXISTS idx_players_email ON players(email);

-- Índice en videos.player_id para JOIN rápido
CREATE INDEX IF NOT EXISTS idx_videos_player_id ON videos(player_id);

-- Índice en videos.status para filtrar videos processed
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);

-- Índice en videos.uploaded_at para ordenamiento
CREATE INDEX IF NOT EXISTS idx_videos_uploaded_at ON videos(uploaded_at DESC);

-- Índice compuesto en videos(status, uploaded_at) - cubre query completa
CREATE INDEX IF NOT EXISTS idx_videos_status_uploaded ON videos(status, uploaded_at DESC);

-- Índice en votes.video_id para conteo de votos
CREATE INDEX IF NOT EXISTS idx_votes_video_id ON votes(video_id);

-- Índice en votes.player_id para buscar votos de usuario
CREATE INDEX IF NOT EXISTS idx_votes_player_id ON votes(player_id);

-- Índice compuesto en votes(video_id, player_id) para verificación rápida
CREATE INDEX IF NOT EXISTS idx_votes_video_player ON votes(video_id, player_id);

-- ======================================================================
-- INFORMACIÓN
-- ======================================================================
-- Los índices mejoran:
--   - Listado de videos públicos (WHERE status='processed' ORDER BY uploaded_at)
--   - Conteo de votos por video (GROUP BY video_id)
--   - Verificación de voto duplicado (WHERE video_id=X AND player_id=Y)
--   - Rankings de jugadores (JOIN + agregaciones)
-- ======================================================================
