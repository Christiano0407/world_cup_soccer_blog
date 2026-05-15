-- =============================================================
-- FIFA World Cup Platform — Migration 003: Warehouse Layer
-- =============================================================
-- Schema   : warehouse
-- Purpose  : Pre-aggregated views for dashboards and analytics
--            Python (Pandas/Polars) + D3.js consume these views.
-- Strategy : MATERIALIZED VIEWS refresh after each ETL load.
--            Simple views stay live for ad-hoc queries.
-- # ============================================================ #
-- "Una View (vista) en SQL es una tabla virtual creada a partir del resultado de una consulta SELECT.  
-- No almacena datos físicamente, sino que guarda la definición de la consulta, lo que permite presentar datos de una o más tablas 
-- subyacentes de forma -- simplificada y personalizada ".
-- =============================================================

-- === VIEW: Goals per Tournament === 
CREATE MATERIALIZED VIEW IF NOT EXISTS warehouse.goals_per_tournament AS 
SELECT
    t.year,
    t.host_country, 
    t.winner, 
    t.goals_scored, 
    t.matches_played,
    ROUND(t.goals_scored::NUMERIC / NULLIF(t.matches_played, 0), 2) AS svg_goals_per_match,
    t.qualified_teams, 
    t.attendance_total,
    ROUND(t.attendance_total::NUMERIC / NULLIF(t.matches_played, 0), 0) AS svg_attendance_per_match
FROM public.tournament t
ORDER BY t.year; 

 
COMMENT ON MATERIALIZED VIEW warehouse.goals_per_tournament
    IS 'Dashboard: scoring stats per edition — refreshed post-ETL';


-- === VIEW: Team performance across all editions === 


-- ─── VIEW: Top scorers (by event_code = G / OG) ──────────────


-- ─── VIEW: Goals by match stage ──────────────────────────────


-- ─── VIEW: Attendance trends ─────────────────────────────────


-- ─── VIEW: Player participation (positions) ──────────────────


-- ─── Refresh function (called post-ETL by W3 Load) ───────────