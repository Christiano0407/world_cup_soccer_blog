-- ================================================================ ##### ================================================================
-- FIFA World Cup Platform — DML Completo
-- Data Manipulation Language: INSERT · UPDATE · DELETE · UPSERT
-- ================================================================
-- Propósito : Operaciones de manipulación de datos para todas
--             las tablas del modelo relacional.
-- Regla base: NUNCA SQL por concatenación de strings.
--             Toda query usa parámetros nombrados ($1, $2, :param)
-- Orden     : Seeds → Inserts → Upserts → Updates → Deletes → Purges
-- attendance: Asistentes
-- ================================================================ ##### ================================================================
 
 
-- ════════════════════════════════════════════════════════════════
-- SECCIÓN 1 — SEEDS (datos de referencia, run-once)
-- Seeds son idempotentes: ON CONFLICT DO NOTHING siempre.
-- ════════════════════════════════════════════════════════════════
 
-- ─── === 1.1 Equipos históricos del Mundial === ─────────────────────────
-- Cubre todos los equipos que aparecen en los 3 datasets CSV.
-- initials = código de 3 letras del CSV (puede diferir del FIFA actual)

INSERT INTO public.teams (initials, name, confederation, fifa_code, active)
VALUES 
  ('URU', 'Uruguay',            'CONMEBOL', 'URU', TRUE),
  ('ARG', 'Argentina',          'CONMEBOL', 'ARG', TRUE),
  ('USA', 'United States',      'CONCACAF', 'USA', TRUE),
  ('YUG', 'Yugoslavia',         'UEFA',     NULL,  FALSE),
  ('ITA', 'Italy',              'UEFA',     'ITA', TRUE),
  ('TCH', 'Czechoslovakia',     'UEFA',     NULL,  FALSE),  -- CZE→TCH, disuelta 1993
  ('GER', 'Germany',            'UEFA',     'GER', TRUE),
  ('AUT', 'Austria',            'UEFA',     'AUT', TRUE),
  ('HUN', 'Hungary',            'UEFA',     'HUN', TRUE),
  ('FRA', 'France',             'UEFA',     'FRA', TRUE),
  ('SWE', 'Sweden',             'UEFA',     'SWE', TRUE),
  ('BRA', 'Brazil',             'CONMEBOL', 'BRA', TRUE),
  ('ESP', 'Spain',              'UEFA',     'ESP', TRUE),
  ('CHI', 'Chile',              'CONMEBOL', 'CHI', TRUE),
  ('ENG', 'England',            'UEFA',     'ENG', TRUE),
  ('POR', 'Portugal',           'UEFA',     'POR', TRUE),
  ('URS', 'Soviet Union',       'UEFA',     NULL,  FALSE),
  ('MEX', 'Mexico',             'CONCACAF', 'MEX', TRUE),
  ('NED', 'Netherlands',        'UEFA',     'NED', TRUE),
  ('POL', 'Poland',             'UEFA',     'POL', TRUE),
  ('SUI', 'Switzerland',        'UEFA',     'SUI', TRUE),
  ('BEL', 'Belgium',            'UEFA',     'BEL', TRUE),
  ('BUL', 'Bulgaria',           'UEFA',     'BUL', TRUE),
  ('CRO', 'Croatia',            'UEFA',     'CRO', TRUE),
  ('TUR', 'Turkey',             'UEFA',     'TUR', TRUE),
  ('KOR', 'South Korea',        'AFC',      'KOR', TRUE),
  ('MAR', 'Morocco',            'CAF',      'MAR', TRUE),
  ('SEN', 'Senegal',            'CAF',      'SEN', TRUE),
  ('GHA', 'Ghana',              'CAF',      'GHA', TRUE),
  ('CMR', 'Cameroon',           'CAF',      'CMR', TRUE),
  ('AUS', 'Australia',          'AFC',      'AUS', TRUE),
  ('JPN', 'Japan',              'AFC',      'JPN', TRUE),
  ('CRC', 'Costa Rica',         'CONCACAF', 'CRC', TRUE),
  ('QAT', 'Qatar',              'AFC',      'QAT', TRUE)
ON CONFLICT (initials) DO NOTHING; 

-- ─── === 1.2 Árbitros históricos (muestra — ETL completa el resto) === ──
INSERT INTO public.referee (full_name, country_code, role)
VALUES
  ('LOMBARDI Domingo (URU)',          'URU', 'main'),
  ('CRISTOPHE Henry (BEL)',           'BEL', 'assistant'),
  ('REGO Gilberto (BRA)',             'BRA', 'assistant'),
  ('MACIAS Jose (ARG)',               'ARG', 'main'),
  ('MATEUCCI Francisco (URU)',        'URU', 'assistant'),
  ('WARNKEN Alberto (CHI)',           'CHI', 'assistant')
ON CONFLICT (full_name) DO NOTHING; 

-- 1.3 Estadios (tabla creada en 007_referees_stadiums.sql)
INSERT INTO public.stadiums (name, city, country, capacity)
VALUES
  ('Pocitos',               'Montevideo',   'Uruguay',   20000),
  ('Parque Central',        'Montevideo',   'Uruguay',   22000),
  ('Centenario',            'Montevideo',   'Uruguay',   65000),
  ('Wembley Stadium',       'London',       'England',   90000),
  ('Maracanã',              'Rio de Janeiro','Brazil',  78000),
  ('Azteca',                'Mexico City',  'Mexico',   87000),
  ('San Siro',              'Milan',        'Italy',     80000),
  ('Lusail Stadium',        'Lusail',       'Qatar',     89000),
  ('Khalifa International', 'Doha',         'Qatar',     45000)
ON CONFLICT (name, city) DO NOTHING; 

-- ════════════════════════════════════════════════════════════════
-- SECCIÓN 2 — INSERTS DE NEGOCIO (el ETL los usa como templates)
-- Estos son los patrones que W3 Load usa internamente.
-- Aquí sirven como referencia + para testing manual.
-- ════════════════════════════════════════════════════════════════

-- ─── 2.1 INSERT torneo (un Mundial completo) ────────────────────
-- Usado por W3 (load) en el ciclo de winners.
-- ON CONFLICT (year) DO UPDATE: si el CSV se re-procesa, actualiza. | Nunca actualizar datos que no cambian --
-- Nunca actualizar datos que no cambian
INSERT INTO public.tournaments(
  year, host_country, winner, runner_ups, 
  third_place, fourth_place, 
  goals_scored, qualified_teams, 
  matches_played, attendance_total
)
VALUES (
  1930,Uruguay,Uruguay,Argentina,USA,Yugoslavia,70,13,18,590.549
)
ON CONFLICT (year) DO UPDATE SET 
  winner            = EXCLUDED.winner,
  runners_up        = EXCLUDED.runners_up, 
  goals_scored      = EXCLUDED.goals_scored,
  attendance_total  = EXCLUDED.attendance_total,
  host_country      = EXCLUDED.host_country; 


-- ─── 2.2 INSERT partido (matches) ───────────────────────────────
-- ON CONFLICT (match_id) DO NOTHING: los IDs del CSV son inmutables.
INSERT INTO public.matches(
  match_id, tournament_id, round_id, match_datetime,
  stage, home_team_initials, away_team_initials, 
  home_goals, away_goals,
  ht_home_goals, ht_away_goals, 
  win_conditions, attendance, 
  referee, assistant_1, assistant_2 
)
VALUES (
  1096,
  (SELECT tournament_id FROM public.tournaments WHERE year = 1930),
  201,
  '1930-07-13 15:00:00+00',
  'Group 1',
  'FRA', 'MEX',
  4, 1,
  3, 0,
  NULL, 4444,
  'LOMBARDI Domingo (URU)',
  'CRISTOPHE Henry (BEL)',
  'REGO Gilberto (BRA)'
)
ON CONFLICT (match_id) DO NOTHING; 

-- ─── 2.3 INSERT jugador en partido (match_players) ──────────────
-- BIGSERIAL: surrogate key, no hay CONFLICT posible en player_match_id.
-- La combinación (match_id, team_initials, player_name, lineup_type)
-- es la clave natural — se usa para evitar duplicados en re-runs.

INSERT INTO public.match_players(
  match_id, round_id, team_initials,
  coach_name, lineup_type, shirt_number,
  player_name, position, event_code
)
SELECT (
      1096, 201, 'FRA',
      'CAUDRON Raoul (FRA)', 'S', NULL,
      'Alex THEPOT', 'GK', NULL)
WHERE NOT EXISTS(
      SELECT 1 FROM public.match_players
      WHERE match_id = 1069
        AND team_initials = 'FRA',
        AND player_name = 'Alex THEPOT',
        AND line_up = '5'
      ); 


-- ════════════════════════════════════════════════════════════════
-- SECCIÓN 3 — UPDATES DE NEGOCIO
-- ════════════════════════════════════════════════════════════════




-- ════════════════════════════════════════════════════════════════
-- SECCIÓN 4 — DELETES (con política explícita)
-- REGLA: datos históricos NUNCA se eliminan (matches, players, etc.)
--        Solo datos de operación (tokens, logs > 90 días).
-- ════════════════════════════════════════════════════════════════





-- ════════════════════════════════════════════════════════════════
-- SECCIÓN 5 — QUERIES DE AUDITORÍA Y VERIFICACIÓN
-- Para ejecutar manualmente en DataGrip / PgAdmin.
-- ════════════════════════════════════════════════════════════════