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
-- # Data Warehouse: "Un Data Warehouse (almacén de datos) es un sistema centralizado diseñado para recopilar, integrar y almacenar 
-- grandes volúmenes de datos provenientes de múltiples fuentes operativas, con el objetivo específico de facilitar el análisis, 
-- la generación de informes y la toma de decisiones empresariales".
-- # AVG() => "Calcular el promedio"
-- # La cláusula DISTINCT en SQL se utiliza junto con el comando SELECT para eliminar filas duplicadas y devolver únicamente valores únicos 
-- en el conjunto de resultados.
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
FROM public.tournaments t
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
    SUM(CASE
        WHEN m.home_goals = m.away_goals THEN 1
        ELSE 0 END)                                          AS draws,
    SUM(CASE
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
LEFT JOIN public.tournaments t ON t.tournament_id = m.tournament_id
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
JOIN public.tournaments t ON m.tournament_id = t.tournament_id
WHERE mp.event_code IS NOT NULL
GROUP BY mp.player_name, mp.team_initials
ORDER BY goals DESC;   

COMMENT ON MATERIALIZED VIEW warehouse.top_scored
    IS 'Dashboard: all-time goal scorers across all World Cups';


-- ─── VIEW: Goals by match stage ──────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS warehouse.goals_by_stage AS 
SELECT
    m.stage,
    t.year,
    COUNT(m.match_id)                                       AS matches,
    SUM(m.home_goals + m.away_goals)                        AS total_goals,
    ROUND(AVG(m.home_goals + m.away_goals)::NUMERIC, 2)     AS avg_goals,
    SUM(m.home_goals)                                       AS home_goals,
    SUM(m.away_goals)                                       AS away_goals,
    COUNT(*) FILTER (WHERE m.home_goals > m.away_goals)     AS home_wins,
    COUNT(*) FILTER (WHERE m.away_goals > m.home_goals)     AS away_wins,
    COUNT(*) FILTER (WHERE m.home_goals = m.away_goals)     AS draws,
    AVG(m.attendance)::INTEGER                              AS svg_attendance
FROM public.matches m
JOIN public.tournaments t ON m.tournament_id = t.tournament_id
GROUP BY m.stage, t.year
ORDER BY t.year, m.stage; 

COMMENT ON MATERIALIZED VIEW warehouse.goals_by_stage
    IS 'Dashboard: scoring and results breakdown by stage';


-- ─── VIEW: Attendance trends ─────────────────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS warehouse.attendance_trends AS
SELECT
    t.year, 
    t.host_country, 
    t.qualified_teams, 
    t.matches_played, 
    t.attendance_total,
    SUM(m.attendance)                                   AS sum_match_attendance, 
    MAX(m.attendance)                                   AS max_attendance,
    MIN(m.attendance) FILTER (WHERE m.attendance > 0)   AS min_attendance,
    AVG(m.attendance)::INTEGER                          AS avg_attendance
FROM public.tournaments t
LEFT JOIN public.matches m ON t.tournament_id = m.tournament_id
GROUP BY t.year, t.host_country, t.qualified_teams, t.matches_played, t.attendance_total
ORDER BY t.year; 

COMMENT ON MATERIALIZED VIEW warehouse.attendance_trends
    IS 'Dashboard: stadium attendance patterns across editions';

-- ─── VIEW: Player participation (positions) ──────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS warehouse.player_position AS
SELECT
    mp.position, 
    mp.team_initials,
    t.year,
    COUNT(DISTINCT mp.player_name)                  AS unique_players,
    COUNT(*) FILTER (WHERE mp.lineup_type = 'S')    AS starts,
    COUNT(*) FILTER (WHERE mp.lineup_type = 'N')    AS subs
FROM public.match_players mp
JOIN public.matches m           ON mp.match_id = m.match_id
JOIN public.tournaments t       ON m.tournament_id = t.tournament_id
GROUP BY mp.position, mp.team_initials, t.year
ORDER BY t.year, mp.position; 

COMMENT ON MATERIALIZED VIEW warehouse.player_position
    IS 'Dashboard: player participation by position and year';


-- ─── Refresh function (called post-ETL by W3 Load) ───────────
CREATE OR REPLACE FUNCTION warehouse.refresh_all()
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    REFRESH MATERIALIZED VIEW warehouse.goals_per_tournament; 
    REFRESH MATERIALIZED VIEW warehouse.team_performance; 
    REFRESH MATERIALIZED VIEW warehouse.top_scored; 
    REFRESH MATERIALIZED VIEW warehouse.goals_by_stage; 
    REFRESH MATERIALIZED VIEW warehouse.attendance_trends; 
    REFRESH MATERIALIZED VIEW warehouse.player_position;  
    RAISE NOTICE 'Warehouse view refresh at %', NOW();

END;
$$; 

 
COMMENT ON FUNCTION warehouse.refresh_all IS
    'Call after each ETL load cycle to refresh all materialized views';