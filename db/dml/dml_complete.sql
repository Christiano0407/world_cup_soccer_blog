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
INSERT INTO public.referees (full_name, country_code, role)
VALUES
  ('LOMBARDI Domingo (URU)',          'URU', 'main'),
  ('CRISTOPHE Henry (BEL)',           'BEL', 'assistant'),
  ('REGO Gilberto (BRA)',             'BRA', 'assistant'),
  ('MACIAS Jose (ARG)',               'ARG', 'main'),
  ('MATEUCCI Francisco (URU)',        'URU', 'assistant'),
  ('WARNKEN Alberto (CHI)',           'CHI', 'assistant')
ON CONFLICT (full_name) DO NOTHING; 

-- 1.3 Estadios (tabla creada en 007_referee_stadium.sql)
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
  year, host_country, winner, runners_up, 
  third_place, fourth_place, 
  goals_scored, qualified_teams, 
  matches_played, attendance_total
)
VALUES (
  1930, 'Uruguay', 'Uruguay', 'Argentina', 'USA', 'Yugoslavia', 70, 13, 18, 590549
)
ON CONFLICT (year) DO UPDATE SET 
  winner            = EXCLUDED.winner,
  runners_up        = EXCLUDED.runners_up, 
  goals_scored      = EXCLUDED.goals_scored,
  attendance_total  = EXCLUDED.attendance_total,
  host_country      = EXCLUDED.host_country; 


-- ─── 2.1.5 INSERT ronda (rounds) ────────────────────────────────
-- Necesaria para la FK de matches.
INSERT INTO public.rounds (round_id, tournament_id, round_name)
VALUES (
  201,
  (SELECT tournament_id FROM public.tournaments WHERE year = 1930),
  'Group 1'
)
ON CONFLICT (round_id) DO NOTHING;


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
SELECT 1096, 201, 'FRA',
       'CAUDRON Raoul (FRA)', 'S', NULL,
       'Alex THEPOT', 'GK', NULL
WHERE NOT EXISTS (
  SELECT 1 FROM public.match_players
  WHERE match_id = 1096
    AND team_initials = 'FRA'
    AND player_name = 'Alex THEPOT'
    AND lineup_type = 'S'
); 

-- ─── 2.4 INSERT participación de equipo en torneo ───────────────
INSERT INTO public.tournament_teams(
  tournament_id, team_initials, finish_position, 
  matches_played, wins, draws, losses,
  goals_for, goals_against
)
VALUES(
  (SELECT tournament_id FROM public.tournaments WHERE year = 1930),
  'URU', 1, 4, 4, 0, 0, 15, 3
)
ON CONFLICT (tournament_id, team_initials) DO UPDATE SET 
    finish_position = EXCLUDED.finish_position,
    wins            = EXCLUDED.wins, 
    draws           = EXCLUDED.draws, 
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
  token_hash, user_id, expires_at, issued_from_ip
)
SELECT
    encode(sha256('token_raw_aqui'), 'hex'),
    user_id,
    NOW() + INTERVAL '7 days',
    '192.168.1.1'::INET
FROM public.users WHERE email = 'user@example.com'; 

-- ─── 2.8 INSERT password reset token ────────────────────────────
INSERT INTO public.auth_password_resets(
  user_id, token_hash, expires_at
)
SELECT
    user_id,
    encode(sha256('reset_token_raw'), 'hex'),
    NOW() + INTERVAL '15 minutes'
FROM public.users WHERE email = 'user@example.com'; 

-- ─── 2.9 INSERT ETL run log (inicio de pipeline) ────────────────
INSERT INTO public.etl_run_log(
  dataset, worker, status, triggered_by
)
VALUES(
  'winners', 'load_w3', 'running', 'scheduler'
)
RETURNING run_id; 
-- W3 luego hace UPDATE con rows_loaded, finished_at, status='success'


-- ════════════════════════════════════════════════════════════════
-- SECCIÓN 3 — UPDATES DE NEGOCIO
-- ════════════════════════════════════════════════════════════════

-- ─── 3.1 Cerrar un run ETL (W3 lo llama al finalizar) ───────────
UPDATE public.etl_run_log
SET
    status          = 'success',        -- o 'failed' / 'partial'
    finished_at     = NOW(),
    rows_read       = 22,
    rows_valid      = 22,
    rows_rejected   = 0,
    rows_loaded     = 22,
    minio_parquet_key = 'processed/winners/winners_latest.parquet'
WHERE run_id = 1              -- $1 en la query parametrizada
  AND status  = 'running';    -- solo si sigue en running (idempotente)


-- ─── 3.2 Vincular FK de árbitro normalizado a partido ───────────
-- El ETL de W3 corre esto después de insertar referees.
UPDATE public.matches m
SET
    referee_id    = r.referee_id,
    assistant_1_id= a1.referee_id,
    assistant_2_id= a2.referee_id
FROM public.matches mx
LEFT JOIN public.referees r  ON r.full_name = mx.referee
LEFT JOIN public.referees a1 ON a1.full_name = mx.assistant_1
LEFT JOIN public.referees a2 ON a2.full_name = mx.assistant_2
WHERE m.match_id    = mx.match_id
  AND m.referee_id  IS NULL           -- solo los que aún no tienen FK
  AND mx.referee    IS NOT NULL;


-- ─── 3.3 Vincular FK de estadio normalizado a partido ───────────
UPDATE public.matches m
SET stadium_id = s.stadium_id
FROM public.stadiums s
WHERE LOWER(TRIM(m.stadium)) = LOWER(TRIM(s.name))
  AND m.stadium_id IS NULL;


-- ─── 3.4 Vincular player_id en match_players (post-seed players) ─
UPDATE public.match_players mp
SET player_id = p.player_id
FROM public.players p
WHERE UPPER(TRIM(mp.player_name)) = UPPER(TRIM(p.full_name))
  AND mp.team_initials             = p.primary_team
  AND mp.player_id                 IS NULL;


-- ─── 3.5 Actualizar FKs de campeones en tournaments ─────────────
-- Resuelve el gap: winner/runners_up eran VARCHAR libre.
UPDATE public.tournaments t
SET
    winner_team_id      = w.team_id,
    runners_up_team_id  = ru.team_id,
    third_team_id       = th.team_id,
    fourth_team_id      = fo.team_id
FROM public.tournaments tt
LEFT JOIN public.teams w  ON UPPER(w.name) = UPPER(tt.winner)
LEFT JOIN public.teams ru ON UPPER(ru.name) = UPPER(tt.runners_up)
LEFT JOIN public.teams th ON UPPER(th.name) = UPPER(tt.third_place)
LEFT JOIN public.teams fo ON UPPER(fo.name) = UPPER(tt.fourth_place)
WHERE t.tournament_id     = tt.tournament_id
  AND t.winner_team_id    IS NULL;


-- ─── 3.6 Bloquear usuario por intentos fallidos (API Auth) ───────
UPDATE public.users
SET
    failed_login_count  = failed_login_count + 1,
    locked_until        = CASE
        WHEN failed_login_count + 1 >= 5
        THEN NOW() + INTERVAL '15 minutes'
        ELSE locked_until
    END
WHERE email     = 'user@example.com'    -- $1 parametrization
  AND is_active = TRUE;


-- ─── 3.7 Reset contador en login exitoso ────────────────────────
UPDATE public.users
SET
    failed_login_count  = 0,
    locked_until        = NULL,
    last_login_at       = NOW(),
    last_login_ip       = '192.168.1.1'::INET   -- $2 parametrizado
WHERE user_id = (SELECT user_id FROM public.users WHERE email = 'user@example.com');


-- ─── 3.8 Revocar refresh token (logout) ─────────────────────────
UPDATE public.auth_refresh_tokens
SET
    revoked_at    = NOW(),
    revoke_reason = 'logout'
WHERE token_hash  = encode(sha256('token_raw_aqui'), 'hex')  -- $1 parametrizado
  AND revoked_at  IS NULL     -- idempotente: no re-revocar
  AND expires_at  > NOW();    -- solo tokens aún válidos


-- ─── 3.9 Marcar password reset como usado ───────────────────────
UPDATE public.auth_password_resets
SET used_at = NOW()
WHERE token_hash = encode(sha256('reset_token_raw'), 'hex')
  AND used_at    IS NULL
  AND expires_at > NOW()
RETURNING user_id;  -- la API usa el user_id para hashear la nueva pass


-- ─── 3.10 Modificar role de usuario (admin) ─────────────────────
UPDATE public.users
SET
    role        = 'editor',     -- $1 parametrizado
    updated_at  = NOW()
WHERE user_id   = (SELECT user_id FROM public.users WHERE email = 'user@example.com')  -- $2
  AND role      != 'admin';     -- un admin no puede degradar a otro admin sin confirmación


-- ─── 3.11 Verificar email de usuario ────────────────────────────
UPDATE public.users
SET
    email_verified      = TRUE,
    email_verified_at   = NOW(),
    updated_at          = NOW()
WHERE user_id           = (SELECT user_id FROM public.users WHERE email = 'user@example.com')
  AND email_verified    = FALSE;


-- ════════════════════════════════════════════════════════════════
-- SECCIÓN 4 — DELETES (con política explícita)
-- REGLA: datos históricos NUNCA se eliminan (matches, players, etc.)
--        Solo datos de operación (tokens, logs > 90 días).
-- ════════════════════════════════════════════════════════════════

-- ─── 4.1 Soft delete de usuario (admin) ─────────────────────────
-- Nunca DELETE físico — se pierde el historial de sesiones.
UPDATE public.users
SET
    is_active   = FALSE,
    updated_at  = NOW()
WHERE user_id = (SELECT user_id FROM public.users WHERE email = 'user@example.com');


-- ─── 4.2 Purge de refresh tokens expirados (cron diario) ────────
-- Únicamente tokens que ya expiraron Y están revocados.
-- Los expirados no revocados se mantienen 30 días para auditoría.
DELETE FROM public.auth_refresh_tokens
WHERE expires_at    < NOW() - INTERVAL '30 days'
  AND revoked_at    IS NOT NULL;   -- solo los ya revocados


-- ─── 4.3 Purge de password resets viejos (cron diario) ──────────
DELETE FROM public.auth_password_resets
WHERE expires_at < NOW() - INTERVAL '24 hours';


-- ─── 4.4 Purge de ETL run logs > 90 días (cron semanal) ─────────
-- Mantener los últimos 90 días para debugging y auditoría.
DELETE FROM public.etl_run_log
WHERE started_at < NOW() - INTERVAL '90 days'
  AND status     != 'failed';   -- los fallidos se guardan más tiempo


-- ─── 4.5 Purge de staging raw > 30 días (cron semanal) ──────────
-- raw.* es solo staging — se puede limpiar una vez validado en public.
DELETE FROM raw.wc_winners
WHERE _ingested_at < NOW() - INTERVAL '30 days'
  AND _is_valid     = TRUE;  -- solo los que ya pasaron a public

DELETE FROM raw.wc_matches
WHERE _ingested_at < NOW() - INTERVAL '30 days'
  AND _is_valid     = TRUE;

DELETE FROM raw.wc_players
WHERE _ingested_at < NOW() - INTERVAL '30 days'
  AND _is_valid     = TRUE;


-- ─── 4.6 Purge de dead letter procesados ────────────────────────
-- Eliminar rechazos que ya se resolvieron manualmente.
DELETE FROM raw.dead_letter
WHERE _rejected_at < NOW() - INTERVAL '60 days';


-- ════════════════════════════════════════════════════════════════
-- SECCIÓN 5 — QUERIES DE AUDITORÍA Y VERIFICACIÓN
-- Para ejecutar manualmente en DataGrip / PgAdmin.
-- ════════════════════════════════════════════════════════════════

-- ─── 5.1 Verificar integridad FK tournaments → teams ────────────
SELECT t.year, t.winner,
       CASE WHEN wt.team_id IS NULL THEN 'SIN FK' ELSE 'OK' END AS winner_fk_status
FROM public.tournaments t
LEFT JOIN public.teams wt ON t.winner_team_id = wt.team_id
ORDER BY t.year;


-- ─── 5.2 Partidos sin árbitro normalizado ───────────────────────
SELECT match_id, year, referee
FROM public.matches m
JOIN public.tournaments t ON m.tournament_id = t.tournament_id
WHERE m.referee_id IS NULL
  AND m.referee IS NOT NULL
ORDER BY year;


-- ─── 5.3 Jugadores sin player_id (entidad no resuelta) ──────────
SELECT team_initials, player_name, COUNT(*) AS apariciones
FROM public.match_players
WHERE player_id IS NULL
GROUP BY team_initials, player_name
ORDER BY apariciones DESC
LIMIT 20;


-- ─── 5.4 Tokens activos por usuario (monitoreo seguridad) ────────
SELECT
    u.email,
    COUNT(rt.token_id) AS active_sessions,
    MAX(rt.issued_at)  AS last_session
FROM public.users u
JOIN public.auth_refresh_tokens rt ON u.user_id = rt.user_id
WHERE rt.revoked_at IS NULL
  AND rt.expires_at > NOW()
GROUP BY u.email
ORDER BY active_sessions DESC;


-- ─── 5.5 Cuentas bloqueadas actualmente ─────────────────────────
SELECT email, failed_login_count, locked_until,
       EXTRACT(MINUTES FROM locked_until - NOW())::INT AS minutes_remaining
FROM public.users
WHERE locked_until > NOW()
ORDER BY locked_until;


-- ─── 5.6 Resumen de último ETL por dataset ───────────────────────
SELECT DISTINCT ON (dataset)
    dataset, worker, status,
    started_at, finished_at,
    rows_loaded, rows_rejected,
    EXTRACT(SECONDS FROM finished_at - started_at)::INT AS duration_s
FROM public.etl_run_log
ORDER BY dataset, started_at DESC;