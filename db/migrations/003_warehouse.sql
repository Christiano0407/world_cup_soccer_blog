-- =====================================================================================================================================
-- FIFA World Cup Platform — Migration 003: Warehouse Layer
-- # ============================================================= #
-- Schema   : warehouse
-- Purpose  : Pre-aggregated views for dashboards and analytics
--            Python (Pandas/Polars) + D3.js consume these views.
-- Strategy : MATERIALIZED VIEWS refresh after each ETL load.
--            Simple views stay live for ad-hoc queries.
-- # ============================================================ #
-- "Una View (vista) en SQL es una tabla virtual creada a partir del resultado de una consulta SELECT.  
-- No almacena datos físicamente, sino que guarda la definición de la consulta, lo que permite presentar datos de una o más tablas 
-- subyacentes de forma -- simplificada y personalizada ".
-- # ============================================================= #
-- Data Warehouse: "Un Data Warehouse (almacén de datos) es un sistema centralizado diseñado para recopilar, integrar y almacenar 
-- grandes volúmenes de datos provenientes de múltiples fuentes operativas, con el objetivo específico de facilitar el análisis, 
-- la generación de informes y la toma de decisiones empresariales".
-- ====================================================================================================================================

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
CREATE MATERIALIZED VIEW IF NOT EXISTS warehouse.team_performance AS 
SELECT
    tm.initials, 
    tm.name                                                  AS team_name,
    COUNT(DISTINCT  t.tournament_id)                         AS tournament_played,
    SUM(CASE WHEN t.winner = tm.name THEN 1 ELSE 0 END)      AS titles,
    SUM(CASE WHEN t.runners_up = tm.name THEN 1 ELSE 0 END)  AS runner_ups,
    SUM(CASE WHEN t.third_place = tm.name THEN 1 ELSE 0 END) AS third_place,
    --  Match Result
    COUNT(DISTINCT m.match_id)                               AS total_matches,
    SUM(CASE 
        WHEN m.home_team_initials = tm.initials AND m.home_goals > m.away_goals THEN 1
        WHEN m.away_team_initials = tm.initials AND m.away_goals > m.home_goals THEN 1
        ELSE 0 END)                                          AS wins,
    SUM(
        WHEN m.home_goals = m.away_goals then 1
        ELSE 0 END)                                          AS draws,
    SUM(
        WHEN m.home_team_initials = tm.initials AND m.home_goals < m.away_goals THEN 1
        WHEN m.away_team_initials = tm.initials AND m.away_goals < m.home_goals THEN 1
        ELSE 0 END)                                          AS losses,
    --  Goals
    SUM(CASE WHEN m.home_team_initials = tm.initials THEN m.home_goals
             WHEN m.away_team_initials = tm.initials THEN m.away_goals 
             ELSE 0 END)                                     AS goals_scored,
    SUM(CASE WHEN m.home_team_initials = tm.initials THEN m.away_goals
             WHEN m.away_team_initials = tm.initials THEN m.home_goals
             ELSE 0 END)                                     AS goals_conceded
FROM public.teams tm
LEFT JOIN public.matches m
    ON tm.initials IN (m.home_team_initials, m.away_team_initials)
LEFT JOIN public.tournament t
GROUP BY tm.initials, tm.name
ORDER BY titles DESC, wins DESC; 

COMMENT ON MATERIALIZED VIEW warehouse.team_performance
    IS 'Dashboard: all-time team stats — titles, W/D/L, goals';


-- ─── VIEW: Top scorers (by event_code = G / OG) ──────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS warehouse.top_scored AS 
SELECT 
    mp.player_name,
    mp.team_initials,
    COUNT(*) FILTER (WHERE mp.event_code LIKE 'G%')    AS goals,
    COUNT(*) FILTER (WHERE mp.event_code = 'OG')       AS own_goals,
    COUNT(DISTINCT mp.match_id)                        AS matches_played,
    MIN(t.year)                                        AS first_wc,
    MAX(t.year)                                        AS last_wc,
    COUNT(DISTINCT m.tournament_id)                    AS editions
FROM public.match_players mp
JOIN public.matches m     ON mp.match_id = m.match_id
JOIN public.tournament t  ON m.tournament_id = t.tournament_id
WHERE mp.event_code IS NOT NULL
GROUP BY mp.player_name, mp.team_initials
ORDER BY goals DESC;   

COMMENT ON MATERIALIZED VIEW warehouse.top_scorers
    IS 'Dashboard: all-time goal scorers across all World Cups';


-- ─── VIEW: Goals by match stage ──────────────────────────────


-- ─── VIEW: Attendance trends ─────────────────────────────────


-- ─── VIEW: Player participation (positions) ──────────────────


-- ─── Refresh function (called post-ETL by W3 Load) ───────────