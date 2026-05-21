"""
W3 — Load Worker | Transform & Load [ETL]
==========================================
Responsibility: Read validated raw.* (_is_valid = TRUE) → transform → upsert into public.*.

FLOW:
  raw.wc_winners (_is_valid = TRUE) → public.tournaments       (upsert by year)
  raw.wc_matches (_is_valid = TRUE) → public.rounds + public.matches (upsert)
  raw.wc_players (_is_valid = TRUE) → public.match_players     (upsert)
  (teams from matches + players)    → public.teams             (upsert by initials)
  → warehouse.refresh_all()
  → export public.* to Parquet → MinIO parquet/ bucket
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import asyncpg
import structlog

from worker.core.config import Settings
from worker.core.storage import ensure_bucket, get_minio_client
from worker.utils.helpers import (
    normalize_initials,
    normalize_team_names,
    normalize_text,
    parse_attendance,
    parse_datetime_csv,
    parse_int,
)

log = structlog.get_logger(__name__)
BATCH_SIZE = 500
TEMP_PARQUET_DIR = "/tmp/w3_parquet"  # noqa: S108


@dataclass
class LoadResult:
    teams_upserted: int = 0
    tournaments_upserted: int = 0
    rounds_upserted: int = 0
    matches_upserted: int = 0
    match_players_upserted: int = 0
    parquet_files: list[str] = field(default_factory=list)
    warehouse_refreshed: bool = False

    def log_summary(self) -> None:
        log.info(
            "w3.summary",
            teams_upserted=self.teams_upserted,
            tournaments_upserted=self.tournaments_upserted,
            rounds_upserted=self.rounds_upserted,
            matches_upserted=self.matches_upserted,
            match_players_upserted=self.match_players_upserted,
            parquet_files=len(self.parquet_files),
            warehouse_refreshed=self.warehouse_refreshed,
        )


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC ENTRYPOINT
# ─────────────────────────────────────────────────────────────────────────────


async def load_all(settings: Settings) -> LoadResult:
    """W3 main entrypoint. Orchestrates the full load pipeline."""
    log.info("w3.start")

    result = LoadResult()
    pool = await asyncpg.create_pool(
        settings.postgres_dsn,
        min_size=2,
        max_size=10,
        command_timeout=60,
    )

    try:
        async with pool.acquire() as conn:
            async with conn.transaction():
                result.teams_upserted = await _load_teams(conn)
                result.tournaments_upserted = await _load_tournaments(conn)
                result.rounds_upserted = await _load_rounds(conn)
                result.matches_upserted = await _load_matches(conn)
                result.match_players_upserted = await _load_match_players(conn)

        async with pool.acquire() as conn:
            await conn.execute("SELECT warehouse.refresh_all()")
            result.warehouse_refreshed = True

        result.parquet_files = await _export_parquet(pool, settings)

    finally:
        await pool.close()

    result.log_summary()
    log.info("w3.complete")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# TEAMS — extract distinct initials+names from valid matches & players
# ─────────────────────────────────────────────────────────────────────────────


async def _load_teams(conn: asyncpg.Connection) -> int:
    teams: dict[str, str] = {}

    rows = await conn.fetch("""
        SELECT DISTINCT home_team_initials AS initials, home_team_name AS name
        FROM raw.wc_matches WHERE _is_valid = TRUE AND home_team_initials IS NOT NULL
        UNION
        SELECT DISTINCT away_team_initials, away_team_name
        FROM raw.wc_matches WHERE _is_valid = TRUE AND away_team_initials IS NOT NULL
        UNION
        SELECT DISTINCT team_initials, NULL
        FROM raw.wc_players WHERE _is_valid = TRUE AND team_initials IS NOT NULL
    """)

    for r in rows:
        initials = normalize_initials(r["initials"])
        if not initials:
            continue
        name = normalize_team_names(r["name"]) if r["name"] else initials
        teams[initials] = name

    upserted = 0
    for initials, name in teams.items():
        await conn.execute(
            """
            INSERT INTO public.teams (initials, name)
            VALUES ($1, $2)
            ON CONFLICT (initials) DO UPDATE SET name = EXCLUDED.name
            """,
            initials,
            name,
        )
        upserted += 1

    log.info("w3.teams_loaded", count=upserted)
    return upserted


# ─────────────────────────────────────────────────────────────────────────────
# TOURNAMENTS — from valid winners rows
# ─────────────────────────────────────────────────────────────────────────────


async def _load_tournaments(conn: asyncpg.Connection) -> int:
    rows = await conn.fetch("""
        SELECT year, country, winner, runners_up, third, fourth,
               goals_scored, qualified_teams, matches_played, attendance
        FROM raw.wc_winners
        WHERE _is_valid = TRUE
        ORDER BY year
    """)

    upserted = 0
    for r in rows:
        year = parse_int(r["year"])
        if year is None:
            continue

        await conn.execute(
            """
            INSERT INTO public.tournaments (
                year, host_country, winner, runners_up,
                third_place, fourth_place, goals_scored,
                qualified_teams, matches_played, attendance_total
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (year) DO UPDATE SET
                host_country    = EXCLUDED.host_country,
                winner          = EXCLUDED.winner,
                runners_up      = EXCLUDED.runners_up,
                third_place     = EXCLUDED.third_place,
                fourth_place    = EXCLUDED.fourth_place,
                goals_scored    = EXCLUDED.goals_scored,
                qualified_teams = EXCLUDED.qualified_teams,
                matches_played  = EXCLUDED.matches_played,
                attendance_total = EXCLUDED.attendance_total
            """,
            year,
            normalize_text(str(r["country"]), max_length=100),
            normalize_text(str(r["winner"]), max_length=100),
            normalize_text(str(r["runners_up"]), max_length=100),
            normalize_text(str(r.get("third") or ""), max_length=100),
            normalize_text(str(r.get("fourth") or ""), max_length=100),
            parse_int(r["goals_scored"]),
            parse_int(r["qualified_teams"]),
            parse_int(r["matches_played"]),
            parse_attendance(r["attendance"]),
        )
        upserted += 1

    log.info("w3.tournaments_loaded", count=upserted)
    return upserted


# ─────────────────────────────────────────────────────────────────────────────
# ROUNDS — extract distinct round_id + stage per tournament
# ─────────────────────────────────────────────────────────────────────────────


async def _extract_tournament_id_map(conn: asyncpg.Connection) -> dict[int, int]:
    rows = await conn.fetch("SELECT year, tournament_id FROM public.tournaments")
    return {r["year"]: r["tournament_id"] for r in rows}


async def _load_rounds(conn: asyncpg.Connection) -> int:
    year_tid = await _extract_tournament_id_map(conn)

    rows = await conn.fetch("""
        SELECT DISTINCT year, round_id, stage
        FROM raw.wc_matches
        WHERE _is_valid = TRUE AND round_id IS NOT NULL
        ORDER BY year, round_id
    """)

    upserted = 0
    for r in rows:
        round_id = parse_int(r["round_id"])
        year = parse_int(r["year"])
        if round_id is None or year is None:
            continue
        tournament_id = year_tid.get(year)
        if tournament_id is None:
            continue

        await conn.execute(
            """
            INSERT INTO public.rounds (round_id, tournament_id, round_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (round_id) DO UPDATE SET
                tournament_id = EXCLUDED.tournament_id,
                round_name    = EXCLUDED.round_name
            """,
            round_id,
            tournament_id,
            normalize_text(str(r["stage"]), max_length=60),
        )
        upserted += 1

    log.info("w3.rounds_loaded", count=upserted)
    return upserted


# ─────────────────────────────────────────────────────────────────────────────
# MATCHES — from valid matches rows
# ─────────────────────────────────────────────────────────────────────────────


async def _load_matches(conn: asyncpg.Connection) -> int:
    year_tid = await _extract_tournament_id_map(conn)

    rows = await conn.fetch("""
        SELECT year, datetime, stage, stadium, city,
               home_team_name, home_team_goals, away_team_goals, away_team_name,
               win_conditions, attendance,
               ht_home_goals, ht_away_goals,
               referee, assistant_1, assistant_2,
               round_id, match_id,
               home_team_initials, away_team_initials
        FROM raw.wc_matches
        WHERE _is_valid = TRUE
        ORDER BY match_id
    """)

    upserted = 0
    for r in rows:
        match_id = parse_int(r["match_id"])
        year = parse_int(r["year"])
        round_id = parse_int(r["round_id"])
        if match_id is None or year is None or round_id is None:
            continue

        tournament_id = year_tid.get(year)
        if tournament_id is None:
            continue

        home_initials = normalize_initials(str(r["home_team_initials"]))
        away_initials = normalize_initials(str(r["away_team_initials"]))
        if not home_initials or not away_initials:
            continue

        match_dt = parse_datetime_csv(str(r["datetime"])) if r["datetime"] else None

        await conn.execute(
            """
            INSERT INTO public.matches (
                match_id, tournament_id, round_id, match_datetime,
                stage, stadium, city,
                home_team_initials, away_team_initials,
                home_goals, away_goals,
                ht_home_goals, ht_away_goals,
                win_conditions, attendance,
                referee, assistant_1, assistant_2
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18)
            ON CONFLICT (match_id) DO UPDATE SET
                tournament_id    = EXCLUDED.tournament_id,
                round_id         = EXCLUDED.round_id,
                match_datetime   = EXCLUDED.match_datetime,
                stage            = EXCLUDED.stage,
                stadium          = EXCLUDED.stadium,
                city             = EXCLUDED.city,
                home_team_initials = EXCLUDED.home_team_initials,
                away_team_initials = EXCLUDED.away_team_initials,
                home_goals       = EXCLUDED.home_goals,
                away_goals       = EXCLUDED.away_goals,
                ht_home_goals    = EXCLUDED.ht_home_goals,
                ht_away_goals    = EXCLUDED.ht_away_goals,
                win_conditions   = EXCLUDED.win_conditions,
                attendance       = EXCLUDED.attendance,
                referee          = EXCLUDED.referee,
                assistant_1      = EXCLUDED.assistant_1,
                assistant_2      = EXCLUDED.assistant_2
            """,
            match_id,
            tournament_id,
            round_id,
            match_dt,
            normalize_text(str(r["stage"]), max_length=60),
            normalize_text(str(r["stadium"] or ""), max_length=120),
            normalize_text(str(r["city"] or ""), max_length=100),
            home_initials,
            away_initials,
            parse_int(r["home_team_goals"]),
            parse_int(r["away_team_goals"]),
            parse_int(r["ht_home_goals"]),
            parse_int(r["ht_away_goals"]),
            normalize_text(str(r["win_conditions"] or ""), max_length=200),
            parse_attendance(r["attendance"]),
            normalize_text(str(r["referee"] or ""), max_length=120),
            normalize_text(str(r["assistant_1"] or ""), max_length=120),
            normalize_text(str(r["assistant_2"] or ""), max_length=120),
        )
        upserted += 1

    log.info("w3.matches_loaded", count=upserted)
    return upserted


# ─────────────────────────────────────────────────────────────────────────────
# MATCH PLAYERS — from valid players rows
# ─────────────────────────────────────────────────────────────────────────────


async def _load_match_players(conn: asyncpg.Connection) -> int:
    valid_match_ids = [
        parse_int(r["match_id"])
        for r in await conn.fetch(
            "SELECT DISTINCT match_id FROM raw.wc_players WHERE _is_valid = TRUE"
        )
        if parse_int(r["match_id"]) is not None
    ]
    if valid_match_ids:
        await conn.execute(
            "DELETE FROM public.match_players WHERE match_id = ANY($1::int[])",
            valid_match_ids,
        )

    rows = await conn.fetch("""
        SELECT round_id, match_id, team_initials, coach_name,
               line_up, shirt_number, player_name, position, event
        FROM raw.wc_players
        WHERE _is_valid = TRUE
        ORDER BY match_id, shirt_number
    """)

    upserted = 0
    for r in rows:
        round_id = parse_int(r["round_id"])
        match_id = parse_int(r["match_id"])
        if round_id is None or match_id is None:
            continue

        shirt_raw = parse_int(r["shirt_number"])
        shirt_number = None if shirt_raw == 0 else shirt_raw

        lineup_raw = normalize_text(str(r["line_up"] or ""), max_length=1)
        lineup_type = "S" if lineup_raw and lineup_raw.upper() == "S" else "N"

        await conn.execute(
            """
            INSERT INTO public.match_players (
                match_id, round_id, team_initials, coach_name,
                lineup_type, shirt_number, player_name, position, event_code
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            """,
            match_id,
            round_id,
            normalize_initials(str(r["team_initials"])),
            normalize_text(str(r["coach_name"] or ""), max_length=120),
            lineup_type,
            shirt_number,
            normalize_text(str(r["player_name"]), max_length=160),
            normalize_text(str(r["position"] or ""), max_length=4),
            normalize_text(str(r["event"] or ""), max_length=20),
        )
        upserted += 1

    log.info("w3.match_players_loaded", count=upserted)
    return upserted


# ─────────────────────────────────────────────────────────────────────────────
# PARQUET EXPORT → MinIO
# ─────────────────────────────────────────────────────────────────────────────


async def _export_parquet(pool: asyncpg.Pool, settings: Settings) -> list[str]:
    try:
        import pandas as pd
    except ImportError:
        log.warning("w3.parquet_skip", reason="pandas not available")
        return []

    Path(TEMP_PARQUET_DIR).mkdir(parents=True, exist_ok=True)
    exported: list[str] = []
    tables = [
        "public.teams",
        "public.tournaments",
        "public.rounds",
        "public.matches",
        "public.match_players",
    ]

    try:
        for table in tables:
            async with pool.acquire() as conn:
                rows = await conn.fetch(f"SELECT * FROM {table} ORDER BY 1")  # noqa: S608
            df = pd.DataFrame([dict(r) for r in rows])
            if df.empty:
                log.info("w3.parquet_empty", table=table)
                continue

            safe_name = table.replace(".", "_")
            parquet_path = f"{TEMP_PARQUET_DIR}/{safe_name}.parquet"
            df.to_parquet(parquet_path, index=False)

            client = get_minio_client()
            ensure_bucket(client, settings.minio_bucket_parquet)
            object_name = f"parquet/{safe_name}.parquet"
            client.fput_object(
                bucket_name=settings.minio_bucket_parquet,
                object_name=object_name,
                file_path=parquet_path,
            )
            exported.append(object_name)
            log.info("w3.parquet_uploaded", table=table, key=object_name)

    except Exception as exc:
        log.warning("w3.parquet_error", error=str(exc))

    return exported
