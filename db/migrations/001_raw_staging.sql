-- =============================================================
-- FIFA World Cup Platform — Migration 001: Raw Staging Tables
-- =============================================================
-- Schema   : raw
-- Anti SQLi: All queries use parameterized execution ($1..$N).
--            Never build queries via string concatenation.
-- raw: Datos 'Crudos', que vamos a usar.
-- =============================================================

-- ─── WINNERS STAGING ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw.wc_winners (
    _row_id         BIGSERIAL       PRIMARY KEY,
    _source_file    VARCHAR(255)    NOT NULL,               -- CSV filename
    _ingested_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    _is_valid       BOOLEAN         DEFAULT NULL,           -- set by W2 Clean

    -- Original CSV: columns (all TEXT — no casting in raw) 
    year            TEXT,
    country         TEXT,
    winner          TEXT,
    runners_up      TEXT,
    third           TEXT,
    fourth          TEXT,
    goals_scored    TEXT,
    qualified_teams TEXT,
    matches_played  TEXT,
    attendance      TEXT,
    _file_hash      TEXT
);

COMMENT ON TABLE  raw.wc_winners IS 'Staging: raw CSV data from wc_world_cup_winners.csv';
COMMENT ON COLUMN raw.wc_winners._file_hash IS 'SHA-256 of source file for reproducibility';

-- ─── MATCHES STAGING ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw.wc_matches (
    _row_id         BIGSERIAL       PRIMARY KEY,
    _source_file    VARCHAR(255)    NOT NULL,
    _ingested_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    _is_valid       BOOLEAN         DEFAULT NULL,

    year                TEXT,
    datetime            TEXT,
    stage               TEXT,
    stadium             TEXT,
    city                TEXT,
    home_team_name      TEXT,
    home_team_goals     TEXT,
    away_team_goals     TEXT,
    away_team_name      TEXT,
    win_conditions      TEXT,
    attendance          TEXT,
    ht_home_goals       TEXT,
    ht_away_goals       TEXT,
    referee             TEXT,
    assistant_1         TEXT,
    assistant_2         TEXT,
    round_id            TEXT,
    match_id            TEXT,
    home_team_initials  TEXT,
    away_team_initials  TEXT,
    _file_hash          TEXT
);

COMMENT ON TABLE  raw.wc_matches IS 'Staging: raw CSV data from wc_matches.csv';
COMMENT ON COLUMN raw.wc_matches._file_hash IS 'SHA-256 of source file for reproducibility';

-- ─── PLAYERS STAGING ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw.wc_players (
    _row_id         BIGSERIAL       PRIMARY KEY,
    _source_file    VARCHAR(255)    NOT NULL,
    _ingested_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    _is_valid       BOOLEAN         DEFAULT NULL,

    round_id        TEXT,
    match_id        TEXT,
    team_initials   TEXT,
    coach_name      TEXT,
    line_up         TEXT,
    shirt_number    TEXT,
    player_name     TEXT,
    position        TEXT,
    event           TEXT
);

COMMENT ON TABLE  raw.wc_players IS 'Staging: raw CSV data from wc_players.csv';

-- ─── DEAD LETTER QUEUE ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS raw.dead_letter (
    _dl_id          BIGSERIAL       PRIMARY KEY,
    _source_table   TEXT            NOT NULL,
    _source_row_id  BIGINT,
    _error_code     TEXT            NOT NULL,
    _error_detail   TEXT,
    _rejected_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  raw.dead_letter  IS 'Rejected rows from W2 validation with structured error codes';
