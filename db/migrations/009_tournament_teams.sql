-- ================================================================
--  ===== FIFA World Cup Platform ===== 
-- Tournaments Teams Tables
-- ================================================================

CREATE TABLE IF NOT EXISTS public.tournament_teams(
  tournament_id     INTEGER     NOT NULL REFERENCES public.tournaments(tournament_id) ON DELETE CASCADE,
  team_initials     CHAR(3)     NOT NULL REFERENCES public.teams(initials) ON DELETE RESTRICT,
  finish_position   SMALLINT,
  matches_played    SMALLINT    NOT NULL DEFAULT 0,
  wins              SMALLINT    NOT NULL DEFAULT 0,
  draws             SMALLINT    NOT NULL DEFAULT 0,
  losses            SMALLINT    NOT NULL DEFAULT 0,
  goals_for         SMALLINT    NOT NULL DEFAULT 0,
  goals_against     SMALLINT    NOT NULL DEFAULT 0, 
  PRIMARY KEY (tournament_id, team_initials)
); 
