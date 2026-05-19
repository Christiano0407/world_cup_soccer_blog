-- ================================================================
--  ===== FIFA World Cup Platform ===== 
-- players entity Tables
-- ================================================================

CREATE TABLE IF NOT EXISTS public.player(
  player_id     SERIAL        PRIMARY KEY,
  full_name     VARCHAR(160)  NOT NULL,
  known_as      VARCHAR(80),
  primary_team  CHAR(3)       REFERENCES public.teams(initials) ON DELETE RESTRICT,
  usual_position VARCHAR(4),
  created_from  VARCHAR(20)   DEFAULT 'etl_csv',
  CONSTRAINT    uq_player_name_team UNIQUE (full_name, primary_team)
); 

-- ----------- Table: public.matches_players -------------
ALTER TABLE public.match_players
  ADD COLUMN IF NOT EXISTS player_id   INTEGER REFERENCES public.player(player_id) ON DELETE SET NULL; 