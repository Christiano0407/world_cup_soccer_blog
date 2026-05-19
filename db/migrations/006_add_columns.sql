-- ## ========================================== ## --
-- # Agregar Columnas que faltan dentro de nuestras tablas de datos 
-- ## ========================================== ## --

-- ----------- Table: public.teams -------------
ALTER TABLE public.teams 
  ADD COLUMN IF NOT EXISTS fifa_code CHAR(3),
  ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE; 

COMMENT ON COLUMN public.teams.fifa_code IS 'Official FIFA 3-letter code (may differ from initials for defunct teams)';
COMMENT ON COLUMN public.teams.active     IS 'FALSE if the federation is defunct/dissolved';

-- ----------- Table: public.users -------------
ALTER TABLE public.users
  ADD COLUMN IF NOT EXISTS failed_login_count   INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS locked_until         TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_login_at        TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS last_login_ip        INET,
  ADD COLUMN IF NOT EXISTS email_verified       BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS email_verified_at    TIMESTAMPTZ; 

-- ----------- Table: public.matches -------------
ALTER TABLE public.matches
  ADD COLUMN IF NOT EXISTS referee_id     INTEGER REFERENCES public.referees(referee_id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS assistant_1_id INTEGER REFERENCES public.referees(referee_id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS assistant_2_id INTEGER REFERENCES public.referees(referee_id) ON DELETE SET NULL, 
  ADD COLUMN IF NOT EXISTS stadium_id     INTEGER REFERENCES public.stadium(stadium_id)  ON DELETE SET NULL; 


-- ----------- Table: public.matches_players -------------


-- ----------- Table: public.tournaments -------------

