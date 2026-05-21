import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from collections.abc import AsyncGenerator

import asyncpg
import pytest
import pytest_asyncio

from worker.core.config import Settings
from worker.core.storage import get_minio_client


# ── Skip if services not available ──────────────────────────────
def _pg_available() -> bool:
    import os

    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5434")
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(2)
        s.connect((host, int(port)))
        return True
    except (OSError, ValueError):
        return False
    finally:
        s.close()


skip_if_no_pg = pytest.mark.skipif(not _pg_available(), reason="PostgreSQL not reachable")


# ── Settings ────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(
        _env_file=None,
        postgres_host="localhost",
        postgres_port="5434",
        postgres_user="champion07",
        postgres_password="change_me_in_production",  # noqa: S106
        postgres_db="data-world-cup",
        minio_endpoint="localhost:9000",
        minio_access_key="admin",
        minio_secret_key="change_me_in_production",  # noqa: S106
    )


# ── PostgreSQL Pool ─────────────────────────────────────────────
@pytest_asyncio.fixture
async def pg_pool(settings: Settings) -> AsyncGenerator[asyncpg.Pool, None]:
    pool = await asyncpg.create_pool(
        settings.postgres_dsn,
        min_size=1,
        max_size=2,
        command_timeout=10,
    )
    yield pool
    await pool.close()


# ── MinIO Client ────────────────────────────────────────────────
@pytest.fixture
def minio_client():
    return get_minio_client()


# ── Sample CSV Data ─────────────────────────────────────────────
@pytest.fixture
def sample_winners_csv() -> bytes:
    return (
        b"Year,Country,Winner,Runners-Up,Third,Fourth,GoalsScored,QualifiedTeams,MatchesPlayed,Attendance\n"
        b"1930,Uruguay,Uruguay,Argentina,USA,Yugoslavia,70,13,18,590549\n"
        b"1934,Italy,Italy,Czechoslovakia,Germany,Austria,70,16,17,363000\n"
    )


@pytest.fixture
def sample_matches_csv() -> bytes:
    return (
        b"1930,13 Jul 1930 - 15:00,Group 1,Pocitos,Montevideo,"
        b"Argentina,1,0,France,,4444,0,0,"
        b"LARGO CABALLERO Juan (PAR),MATEUCCI Francisco (URU),WARNKEN Alberto (CHI),"
        b"1,1,ARG,FRA\n"
        b"1930,15 Jul 1930 - 16:00,Group 1,Parque Central,Montevideo,"
        b"Argentina,6,3,Mexico,,3333,3,1,"
        b"Another Ref (FRA),Asst 1 (URU),Asst 2 (CHI),"
        b"1,2,ARG,MEX\n"
    )


@pytest.fixture
def sample_players_csv() -> bytes:
    return (
        b"RoundID,MatchID,Team Initials,Coach Name,Line-up,Shirt Number,Player Name,Position,Event\n"  # noqa: E501
        b"1,1,ARG,Juan Jose Tramutola,S,0,Angel Bossio,GK,\n"
        b"1,1,ARG,Juan Jose Tramutola,S,4,Alberto Chividini,DF,\n"
    )


# ── Helpers ─────────────────────────────────────────────────────
async def count_rows(pool: asyncpg.Pool, table: str) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(f"SELECT COUNT(*) FROM {table}")  # noqa: S608


async def truncate_raw_tables(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        for t in ("raw.wc_winners", "raw.wc_matches", "raw.wc_players", "raw.dead_letter"):
            await conn.execute(f"DELETE FROM {t}")  # noqa: S608


async def truncate_public_tables(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        for t in (
            "public.match_players",
            "public.matches",
            "public.rounds",
            "public.tournaments",
            "public.teams",
        ):
            await conn.execute(f"DELETE FROM {t}")  # noqa: S608
