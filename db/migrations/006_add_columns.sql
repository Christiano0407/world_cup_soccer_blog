-- ## ========================================== ## ========================================== ## --
-- # Agregar Columnas que faltan dentro de nuestras tablas de datos 
-- # =========================================== # 
-- " La cláusula ON DELETE RESTRICT en SQL es una regla de integridad referencial que impide la eliminación de una fila 
--   en una tabla padre si existen filas relacionadas en una tabla hija.  Esta restricción protege la consistencia de los datos al evitar 
--   que se eliminen registros principales mientras sean referenciados por otros registros secundarios".
-- ## ========================================== ## ========================================== ## --

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

-- ----------- Table: public.tournaments -------------
ALTER TABLE public.tournaments
  ADD COLUMN IF NOT EXISTS  winner_team_id     INTEGER REFERENCES public.teams(team_id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS  runners_up_team_id INTEGER REFERENCES public.teams(team_id) ON DELETE RESTRICT, 
  ADD COLUMN IF NOT EXISTS  third_team_id      INTEGER REFERENCES public.teams(team_id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS  fourth_place_id    INTEGER REFERENCES public.teams(team_id) ON DELETE RESTRICT; 

