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
-- ## =============================================================== ##
-- ON CONFLICT en PostgreSQL permite manejar inserciones que violarían una restricción única o de clave primaria.
-- ON CONFLICT: "Esto evita errores de duplicidad y permite actualizar datos automáticamente si ya existen. 
--  |  no se inserta un nuevo registro, sino que se actualizan los campos existentes con los nuevos valores (los definidos en SET)"
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

-- ─── 2.4 INSERT participación de equipo en torneo ───────────────
INSERT INTO public.tournament_teams(
  tournament_id, team_initials, finish_position, 
  matches_played, wins, draw, losses,
  goals_for, goals_against
)
VALUES(
  (SELECT tournament_id FROM public.tournaments WHERE year = 1930),
  'URU', 1, 4, 4, 0, 0, 15, 3
)
ON CONFLICT (tournament_id, team_initials) DO UPDATE SET 
    finish_position = EXCLUDED.finish_position,
    wins            = EXCLUDED.wins, 
    draw            = EXCLUDED.draw, 
    losses          = EXCLUDED.losses, 
    goals_for       = EXCLUDED.goals_for, 
    goals_against   = EXCLUDED.goals_against;  

 
-- ─── 2.5 INSERT jugador (entidad normalizada) ───────────────────
INSERT INTO public.players (
    full_name, known_as, primary_team, usual_position, created_from
)
VALUES (
   'Alex THEPOT', 'THEPOT', 'FRA', 'GK', 'etl_csv'
)
ON CONFLICT (full_name, primary_team) DO NOTHING;


-- ─── 2.6 INSERT usuario (registro desde landing page) ───────────
-- La API llama este INSERT via asyncpg con parámetros $1..$N.
-- Aquí como referencia del patrón.
INSERT INTO public.users(
  email, password_hash, display_name, role
)
VALUES (
  'user@example.com',
  '$argon2id$v=19$m=65536,t=3,p=4$...hash_aqui...',
  'Fan del Mundial',
  'reader'
)
ON CONFLICT (email) DO NOTHING
RETURNING user_id, email, role, created_at; 


-- ─── 2.7 INSERT refresh token (login/register) ──────────────────
INSERT INTO public.auth_refresh_tokens(
  token_hash, user_id, expired_at, issued_at
)
VALUES (
    encode(sha256('token_raw_aqui'), 'hex'),
    '00000000-0000-0000-0000-000000000001',
    NOW() + INTERVAL '7 days',
    '192.168.1.1'::INET
); 

-- ─── 2.8 INSERT password reset token ────────────────────────────
INSERT INTO public.auth_password_resets(
  user_id, token_hash, expired_at
)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    encode(sha256('reset_token_raw'), 'hex'),
    NOW() + INTERVAL '15 minutes'
); 

-- ─── 2.9 INSERT ETL run log (inicio de pipeline) ────────────────
INSERT INTO public.etl_run_log(
  datasets, worker, status, triggered_at
)
VALUES(
  'wc_winners', "load_w3", 'running', 'scheduler'
)
RETURNING run_id; 
-- W3 luego hace UPDATE con rows_loaded, finished_at, status='success'


-- ════════════════════════════════════════════════════════════════
-- SECCIÓN 3 — UPDATES DE NEGOCIO
-- ════════════════════════════════════════════════════════════════

-- ─── 3.1 Cerrar un run ETL (W3 lo llama al finalizar) ───────────

-- ─── 3.2 Vincular FK de árbitro normalizado a partido ───────────

-- ─── 3.3 Vincular FK de estadio normalizado a partido ───────────

-- ─── 3.4 Vincular player_id en match_players (post-seed players) ─

-- ─── 3.5 Actualizar FKs de campeones en tournaments ─────────────

-- ─── 3.6 Bloquear usuario por intentos fallidos (API Auth) ───────

-- ─── 3.7 Reset contador en login exitoso ────────────────────────

-- ─── 3.8 Revocar refresh token (logout) ─────────────────────────

-- ─── 3.9 Marcar password reset como usado ───────────────────────

-- ─── 3.10 Modificar role de usuario (admin) ─────────────────────

-- ─── 3.11 Verificar email de usuario ────────────────────────────

-- ════════════════════════════════════════════════════════════════
-- SECCIÓN 4 — DELETES (con política explícita)
-- REGLA: datos históricos NUNCA se eliminan (matches, players, etc.)
--        Solo datos de operación (tokens, logs > 90 días).
-- ════════════════════════════════════════════════════════════════





-- ════════════════════════════════════════════════════════════════
-- SECCIÓN 5 — QUERIES DE AUDITORÍA Y VERIFICACIÓN
-- Para ejecutar manualmente en DataGrip / PgAdmin.
-- ════════════════════════════════════════════════════════════════