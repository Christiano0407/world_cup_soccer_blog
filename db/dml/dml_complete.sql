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