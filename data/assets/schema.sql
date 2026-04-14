-- =============================================================
--  Casino Royale Pro — Esquema de autenticación
--  Fichero : data/assets/schema.sql
--  Motor   : SQLite 3
--  Uso     : secciones/auth_db.py lo ejecuta automáticamente
--            la primera vez que arranca la aplicación.
-- =============================================================

PRAGMA journal_mode = WAL;   -- escrituras concurrentes más seguras
PRAGMA foreign_keys = ON;

-- -------------------------------------------------------------
-- Tabla principal de usuarios
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    username             TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash        TEXT    NOT NULL,          -- SHA-256 hex
    security_question    TEXT    NOT NULL,
    security_answer_hash TEXT    NOT NULL,          -- SHA-256 hex (en minúsculas)
    created_at           TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
    last_login           TEXT    NULL
);

-- Índice para búsquedas rápidas por username (ya cubierto por UNIQUE,
-- pero lo hacemos explícito para claridad)
CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios (username COLLATE NOCASE);

-- -------------------------------------------------------------
-- Tabla de intentos de login fallidos  (rate-limiting básico)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS login_attempts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT NOT NULL COLLATE NOCASE,
    attempt_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
    success    INTEGER NOT NULL DEFAULT 0   -- 0 = fallido, 1 = exitoso
);

CREATE INDEX IF NOT EXISTS idx_attempts_user ON login_attempts (username, attempt_at);

-- -------------------------------------------------------------
-- Vista de utilidad: últimos 5 intentos fallidos por usuario
-- -------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_intentos_recientes AS
SELECT
    username,
    COUNT(*)                               AS intentos_fallidos,
    MAX(attempt_at)                        AS ultimo_intento
FROM login_attempts
WHERE success = 0
  AND attempt_at >= strftime('%Y-%m-%d %H:%M:%S',
                             datetime('now', '-15 minutes', 'localtime'))
GROUP BY username;