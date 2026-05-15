-- =============================================================
-- FIFA World Cup Platform — Migration 004: Audit & Security
-- =============================================================
-- Schema   : audit
-- Purpose  : Row-level change history + DB-level security rules
-- =============================================================


-- === AUDIT: Generic Change Log (History) === 
CREATE TABLE IF NOT EXISTS audit.change_log(
  log_id          BIGSERIAL         PRIMARY KEY,
  schema_name     VARCHAR(60)       NOT NULL,
  table_name      VARCHAR(60)       NOT NULL,
  operation       CHAR(1)           NOT NULL,  -- I=insert U=update D=delete
  old_data        JSONB,
  new_data        JSONB,
  changed_by      TEXT              NOT NULL DEFAULT current_user,
  changed_at      TIMESTAMPTZ       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_table
    ON audit.change_log (schema_name, table_name, changed_at DESC);
 
COMMENT ON TABLE audit.change_log IS 'Row-level audit trail for all production tables';