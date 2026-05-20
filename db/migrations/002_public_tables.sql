-- =============================================================
-- FIFA World Cup Platform — Migration 002: Production Tables
-- =============================================================
-- Schema   : public
-- Anti SQLi: All inserts via parameterized queries ($1..$N)
--            Never build queries via string concatenation.
-- DDR / DDL [Entidad - Relación]
-- =============================================================

-- ─── LOOKUP: Teams ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.teams (
    team_id         SERIAL          PRIMARY KEY,
    initials        CHAR(3)         NOT NULL,
    name            VARCHAR(100)    NOT NULL,
    confederation   VARCHAR(20),    -- UEFA, CONMEBOL, CAF, AFC, CONCACAF, OFC

    CONSTRAINT uq_teams_initials UNIQUE (initials),
    CONSTRAINT chk_teams_initials CHECK (initials ~ '^[A-Z]{2,3}$')
);

COMMENT ON TABLE  public.teams          IS 'FIFA national teams lookup';
COMMENT ON COLUMN public.teams.initials IS '3-letter FIFA code, e.g. FRA, MEX';

-- ─── CORE: Tournaments ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.tournaments (
    tournament_id   SERIAL          PRIMARY KEY,
    year            SMALLINT        NOT NULL,
    host_country    VARCHAR(100)    NOT NULL,
    winner          VARCHAR(100)    NOT NULL,
    runners_up      VARCHAR(100)    NOT NULL,
    third_place     VARCHAR(100),
    fourth_place    VARCHAR(100),
    goals_scored    SMALLINT        NOT NULL,
    qualified_teams SMALLINT        NOT NULL,
    matches_played  SMALLINT        NOT NULL,
    attendance_total INTEGER,

    CONSTRAINT uq_tournament_year  UNIQUE (year),
    CONSTRAINT chk_year            CHECK (year >= 1930 AND year <= 2030),
    CONSTRAINT chk_goals           CHECK (goals_scored >= 0),
    CONSTRAINT chk_teams           CHECK (qualified_teams > 0),
    CONSTRAINT chk_matches         CHECK (matches_played > 0),
    CONSTRAINT chk_attendance      CHECK (attendance_total IS NULL OR attendance_total >= 0)
);

COMMENT ON TABLE public.tournaments IS 'One row per World Cup edition';

-- ─── CORE: Rounds ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.rounds (
    round_id        INTEGER         PRIMARY KEY,    -- from CSV RoundID
    tournament_id   INTEGER         NOT NULL,
    round_name      VARCHAR(60)     NOT NULL,

    CONSTRAINT fk_rounds_tournament
        FOREIGN KEY (tournament_id)
        REFERENCES public.tournaments (tournament_id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

COMMENT ON TABLE public.rounds IS 'FIFA internal RoundID mapped to tournament';

-- ─── CORE: Matches ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.matches (
    match_id            INTEGER         PRIMARY KEY,    -- from CSV MatchID
    tournament_id       INTEGER         NOT NULL,
    round_id            INTEGER         NOT NULL,
    match_datetime      TIMESTAMPTZ     NOT NULL,
    stage               VARCHAR(60)     NOT NULL,
    stadium             VARCHAR(120),
    city                VARCHAR(100),
    home_team_initials  CHAR(3)         NOT NULL,
    away_team_initials  CHAR(3)         NOT NULL,
    home_goals          SMALLINT        NOT NULL,
    away_goals          SMALLINT        NOT NULL,
    ht_home_goals       SMALLINT,
    ht_away_goals       SMALLINT,
    win_conditions      TEXT,           -- NULL = normal time win
    attendance          INTEGER,
    referee             VARCHAR(120),
    assistant_1         VARCHAR(120),
    assistant_2         VARCHAR(120),

    CONSTRAINT fk_matches_tournament
        FOREIGN KEY (tournament_id)
        REFERENCES public.tournaments (tournament_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_matches_round
        FOREIGN KEY (round_id)
        REFERENCES public.rounds (round_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_matches_home_team
        FOREIGN KEY (home_team_initials)
        REFERENCES public.teams (initials)
        ON DELETE RESTRICT,
    CONSTRAINT fk_matches_away_team
        FOREIGN KEY (away_team_initials)
        REFERENCES public.teams (initials)
        ON DELETE RESTRICT,
    CONSTRAINT chk_home_goals      CHECK (home_goals >= 0),
    CONSTRAINT chk_away_goals      CHECK (away_goals >= 0),
    CONSTRAINT chk_attendance      CHECK (attendance IS NULL OR attendance >= 0)
);

COMMENT ON TABLE public.matches IS 'One row per World Cup match';

-- ─── CORE: Match Players (Fact table) ────────────────────────
CREATE TABLE IF NOT EXISTS public.match_players (
    player_match_id BIGSERIAL       PRIMARY KEY,    -- surrogate key
    match_id        INTEGER         NOT NULL,
    round_id        INTEGER         NOT NULL,
    team_initials   CHAR(3)         NOT NULL,
    coach_name      VARCHAR(120),
    lineup_type     CHAR(1)         NOT NULL,        -- S=starter, N=sub
    shirt_number    SMALLINT,                        -- NULL if 0 in raw
    player_name     VARCHAR(160)    NOT NULL,
    position        VARCHAR(4),
    event_code      VARCHAR(20),

    CONSTRAINT fk_mp_match
        FOREIGN KEY (match_id)
        REFERENCES public.matches (match_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_mp_team
        FOREIGN KEY (team_initials)
        REFERENCES public.teams (initials)
        ON DELETE RESTRICT,
    CONSTRAINT chk_lineup_type
        CHECK (lineup_type IN ('S', 'N')),
    CONSTRAINT chk_position
        CHECK (position IS NULL OR position IN ('GK','DF','MF','FW','C')),
    CONSTRAINT chk_shirt
        CHECK (shirt_number IS NULL OR shirt_number >= 0)
);

COMMENT ON TABLE  public.match_players IS 'Fact: player appearance per match';
COMMENT ON COLUMN public.match_players.event_code IS
    'G=goal, Y=yellow card, R=red card, OG=own goal, SY=susp yellow, G40=goal 40+, etc.';

-- ─── AUTH: Users (landing page — placeholder) ────────────────
CREATE TABLE IF NOT EXISTS public.users (
    user_id         UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255)    NOT NULL,
    password_hash   VARCHAR(255)    NOT NULL,   -- argon2id
    display_name    VARCHAR(80),
    role            VARCHAR(20)     NOT NULL DEFAULT 'reader',
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_users_email   UNIQUE (email),
    CONSTRAINT chk_users_role   CHECK (role IN ('admin','editor','reader')),
    CONSTRAINT chk_users_email  CHECK (email ~* '^[^@]+@[^@]+\.[^@]+$')
);

COMMENT ON TABLE  public.users              IS 'Platform users — landing page registration';
COMMENT ON COLUMN public.users.password_hash IS 'argon2id hash — never store plaintext';

-- ─── INDEXES ─────────────────────────────────────────────────
-- Matches: tournament-based queries (most common)
CREATE INDEX IF NOT EXISTS idx_matches_tournament ON public.matches (tournament_id);
CREATE INDEX IF NOT EXISTS idx_matches_datetime   ON public.matches (match_datetime);
CREATE INDEX IF NOT EXISTS idx_matches_stage      ON public.matches (stage);

-- Players: lookup by player name (trigram for partial search)
CREATE INDEX IF NOT EXISTS idx_mp_player_name_trgm
    ON public.match_players USING gin (player_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_mp_match           ON public.match_players (match_id);
CREATE INDEX IF NOT EXISTS idx_mp_team            ON public.match_players (team_initials);

-- Users: email lookup
CREATE INDEX IF NOT EXISTS idx_users_email        ON public.users (email);
-- Partial: only active users (avoids scanning soft-deleted)
CREATE INDEX IF NOT EXISTS idx_users_active       ON public.users (email) WHERE is_active = TRUE;
