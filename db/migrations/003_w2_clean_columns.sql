-- ====================================================== --
  -- Workers & ETL [Extract Transform & Load]
  -- w2_clean Clean (Limpieza de datos antes de load)
-- ======================================================= --

-- ==== Paso 1 — Renombrar id → _row_id en raw.* ==== --
ALTER TABLE raw.wc_winners RENAME COLUMN id TO _row_id;
ALTER TABLE raw.wc_matches RENAME COLUMN id TO _row_id; 
ALTER TABLE raw.wc_players RENAME COLUMN id TO _row_id; 

-- ==== Paso 2 — Agregar _is_valid a raw.* ==== --
ALTER TABLE raw.wc_winners ADD COLUMN _is_valid BOOLEAN; 
ALTER TABLE raw.wc_matches ADD COLUMN _is_valid BOOLEAN;
ALTER TABLE raw.wc_players ADD COLUMN _is_valid BOOLEAN; 

CREATE INDEX IF NOT EXISTS idx_wc_winners_valid ON raw.wc_winners (_is_valid) WHERE _is_valid IS NULL; 
CREATE INDEX IF NOT EXISTS idx_wc_matches_valid ON raw.wc_matches (_is_valid) WHERE _is_valid IS NULL; 
CREATE INDEX IF NOT EXISTS idx_wc_players_valid ON raw.wc_players (_is_valid) WHERE _is_valid IS NULL; 

-- ====== Paso 3 — Recrear raw.dead_letter con columnas correctas ===== --

DROP TABLE IF EXISTS raw.dead_letter;

CREATE TABLE raw.dead_letter (
  id              BIGSERIAL     PRIMARY KEY,
  _source_table   TEXT          NOT NULL,
  _source_row_id  BIGINT,
  _error_code     TEXT          NOT NULL,
  _error_details  TEXT, 
  _rejected_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
); 

CREATE INDEX IF NOT EXIST idx_dead_letter_source ON raw.idx_dead_letter (_source_table); 