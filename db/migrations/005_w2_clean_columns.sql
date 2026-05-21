-- ====================================================== --
  -- Workers & ETL [Extract Transform & Load]
  -- w2_clean Clean (Limpieza de datos antes de load)
-- ======================================================= --

-- Estos ALTER ya están cubiertos en 001_raw_staging.sql.
-- Solo aseguramos índices y la tabla dead_letter con schema correcto.

CREATE INDEX IF NOT EXISTS idx_wc_winners_valid ON raw.wc_winners (_is_valid) WHERE _is_valid IS NULL; 
CREATE INDEX IF NOT EXISTS idx_wc_matches_valid ON raw.wc_matches (_is_valid) WHERE _is_valid IS NULL; 
CREATE INDEX IF NOT EXISTS idx_wc_players_valid ON raw.wc_players (_is_valid) WHERE _is_valid IS NULL; 

-- Aseguramos dead_letter con columnas que coinciden con clean_w2.py

CREATE TABLE IF NOT EXISTS raw.dead_letter (
  _dl_id          BIGSERIAL     PRIMARY KEY,
  _source_table   TEXT          NOT NULL,
  _source_row_id  BIGINT,
  _error_code     TEXT          NOT NULL,
  _error_detail   TEXT, 
  _rejected_at    TIMESTAMPTZ   NOT NULL DEFAULT NOW()
); 

CREATE INDEX IF NOT EXISTS idx_dead_letter_source ON raw.dead_letter (_source_table); 