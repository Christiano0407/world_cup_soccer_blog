-- =============================================================
-- FIFA World Cup Platform — Migration 004: Audit & Security
-- ## =============================================================== ##
-- Schema   : audit
-- Purpose  : Row-level change history + DB-level security rules
-- log: History [Paso a paso del Proceso]
-- ## ================================================================ ##
-- COALESCE: "La función COALESCE en SQL devuelve el primer valor no nulo de una lista de expresiones 
-- evaluadas secuencialmente.  Si todos los argumentos proporcionados son nulos, la función devuelve NULL".
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


-- ─── AUDIT trigger function ───────────────────────────────────
CREATE OR REPLACE FUNCTION audit.log_change()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  INSERT INTO audit.log_change (schema_name, table_name, operation, old_data, new_data)
  VALUES (
    TG_TABLE_SCHEMA,
    TG_TABLE_NAME,
    LEFT(TG_OP, 1),
    CASE WHEN TG_OP != 'INSERT' THEN to_jsonb(OLD) ELSE NULL END,
    CASE WHEN TG_OP != 'DELETE' THEN to_jsonb(NEW) ELSE NULL END
  ); 
  RETURN COALESCE(NEW, OLD);
END; 
$$; 


-- === Apply audit trigger to production tables ===
CREATE OR REPLACE TRIGGER trg_audit_tournaments
  AFTER INSERT OR UPDATE OR DELETE ON public.tournaments
  FOR EACH ROW EXECUTE FUNCTION audit.log_change(); 

CREATE OR REPLACE TRIGGER trg_audit_users
  AFTER INSERT OR UPDATE OR DELETE ON public.users
  FOR EACH ROW EXECUTE FUNCTION audit.log_change(); 


-- ─── SECURITY: DB Roles ───────────────────────────────────────

-- === etl_worker: write access to raw + public, no access to audit ===


-- === api_reader: SELECT only on public + warehouse (used by FastAPI) ===

-- === Revoke public schema default access ===