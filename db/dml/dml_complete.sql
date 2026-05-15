-- ================================================================
-- FIFA World Cup Platform — DML Completo
-- Data Manipulation Language: INSERT · UPDATE · DELETE · UPSERT
-- ================================================================
-- Propósito : Operaciones de manipulación de datos para todas
--             las tablas del modelo relacional.
-- Regla base: NUNCA SQL por concatenación de strings.
--             Toda query usa parámetros nombrados ($1, $2, :param)
-- Orden     : Seeds → Inserts → Upserts → Updates → Deletes → Purges
-- ================================================================
 
 
-- ════════════════════════════════════════════════════════════════
-- SECCIÓN 1 — SEEDS (datos de referencia, run-once)
-- Seeds son idempotentes: ON CONFLICT DO NOTHING siempre.
-- ════════════════════════════════════════════════════════════════
 