-- ================================================================
--  ===== FIFA World Cup Platform ===== 
-- Tournaments Teams Tables
-- ================================================================

CREATE TABLES IF NOT EXISTS public.tournament_teams(
  tournament_id     INTEGER     NOT NULL REFERENCES public.tournaments(tournament_id) ON DELETE CASCADE,
  team_initials     CHAR(3)     NOT NULL REFERENCES public.teams(initials) ON DELETE RESTRICT,
  finish_position   SMALLINT,
  matches_played    SMALLINT    NOT NULL DEFAULT 0,
  wins              SMALLINT    NOT NULL DEFAULT 0,
  draw              SMALLINT    NOT NULL DEFAULT 0,
  losses            SMALLINT    NOT NULL DEFAULT 0,
  goals_for         SMALLINT    NOT NULL DEFAULT 0,
  goals_against     SMALLINT    NOT NULL DEFAULT 0, 
  PRIMARY KEY (tournament_id, team_initials)
); 


-- ----------- Table: public.tournaments -------------
ALTER TABLE public.tournaments
  ADD COLUMN IF NOT EXISTS  winner_team_id     INTEGER REFERENCES public.teams(team_id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS  runners_up_team_id INTEGER REFERENCES public.teams(team_id) ON DELETE RESTRICT, 
  ADD COLUMN IF NOT EXISTS  third_team_id      INTEGER REFERENCES public.teams(team_id) ON DELETE RESTRICT,
  ADD COLUMN IF NOT EXISTS  fourth_place_id    INTEGER REFERENCES public.teams(team_id) ON DELETE RESTRICT; 