-- ================================================================
-- FIFA World Cup Platform 
-- referee & stadium Tables
-- ================================================================

-- referee
CREATE TABLE IF NOT EXISTS public.referees( 
  referee_id    SERIAL        PRIMARY KEY,
  full_name     VARCHAR(150)  NOT NULL,
  country_code  CHAR(3)       REFERENCES public.teams(initials) ON DELETE RESTRICT,
  role          VARCHAR(20)   NOT NULL DEFAULT 'main', 
  CONSTRAINT    uq_referees_name UNIQUE (full_name)
); 

-- stadium 
CREATE TABLE IF NOT EXISTS public.stadium(
  stadium_id    SERIAL        PRIMARY KEY,
  name          VARCHAR(150)  NOT NULL,
  city          VARCHAR(100),
  country       VARCHAR(100),
  capacity      INTEGER, 
  CONSTRAINT    uq_stadium_name_city  UNIQUE (name, city)
); 

-- ----------- Table: public.matches -------------
ALTER TABLE public.matches
  ADD COLUMN IF NOT EXISTS referee_id     INTEGER REFERENCES public.referees(referee_id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS assistant_1_id INTEGER REFERENCES public.referees(referee_id) ON DELETE SET NULL,
  ADD COLUMN IF NOT EXISTS assistant_2_id INTEGER REFERENCES public.referees(referee_id) ON DELETE SET NULL, 
  ADD COLUMN IF NOT EXISTS stadium_id     INTEGER REFERENCES public.stadium(stadium_id)  ON DELETE SET NULL; 