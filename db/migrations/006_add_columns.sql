-- ## ========================================== ## --
-- # Agregar Columnas que faltan dentro de nuestras tablas de datos 
-- ## ========================================== ## --

-- ----------- Table: public.teams -------------
ALTER TABLE public.teams 
  ADD COLUMN IF NOT EXISTS fifa_code CHAR(3),
  ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE; 

COMMENT ON COLUMN public.teams.fifa_code IS 'Official FIFA 3-letter code (may differ from initials for defunct teams)';
COMMENT ON COLUMN public.teams.active     IS 'FALSE if the federation is defunct/dissolved';