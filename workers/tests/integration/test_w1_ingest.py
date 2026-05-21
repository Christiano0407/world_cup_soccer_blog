import hashlib

import pytest
from minio.error import S3Error

from worker.ingestion.ingest_w1 import ingest_csv

from .conftest import count_rows, skip_if_no_pg, truncate_raw_tables

pytestmark = [skip_if_no_pg, pytest.mark.integration]


@pytest.fixture(autouse=True)
async def _cleanup(pg_pool):
    yield
    await truncate_raw_tables(pg_pool)


# ─── WINNERS ────────────────────────────────────────────────────


class TestW1Winners:
    @pytest.fixture
    def csv_file(self, tmp_path, sample_winners_csv) -> str:
        p = tmp_path / "wc_world_cup_winners.csv"
        p.write_bytes(sample_winners_csv)
        return p

    async def test_ingest_inserts_rows(self, pg_pool, csv_file, settings):
        result = await ingest_csv(csv_file, "winners", settings)
        assert result.rows_read == 2
        assert result.rows_inserted == 2
        assert result.dataset == "winners"
        assert result.sha256 == hashlib.sha256(open(csv_file, "rb").read()).hexdigest()
        assert await count_rows(pg_pool, "raw.wc_winners") == 2

    async def test_ingest_source_file_stored(self, pg_pool, csv_file, settings):
        await ingest_csv(csv_file, "winners", settings)
        async with pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT _source_file, year, winner FROM raw.wc_winners ORDER BY _row_id LIMIT 1"
            )
        assert row["_source_file"] == "wc_world_cup_winners.csv"
        assert row["year"] == "1930"
        assert row["winner"] == "Uruguay"

    async def test_ingest_idempotent(self, pg_pool, csv_file, settings):
        await ingest_csv(csv_file, "winners", settings)
        await ingest_csv(csv_file, "winners", settings)
        assert await count_rows(pg_pool, "raw.wc_winners") == 4

    async def test_ingest_minio_upload(self, csv_file, settings, minio_client):
        result = await ingest_csv(csv_file, "winners", settings)
        key = result.minio_key
        assert key.startswith("raw/winners/")
        try:
            obj = minio_client.get_object(settings.minio_bucket_raw, key)
            data = obj.read()
            obj.close()
            obj.release_conn()
            assert len(data) > 0
        except S3Error:
            pytest.fail(f"MinIO object not found: {key}")


# ─── MATCHES ────────────────────────────────────────────────────


class TestW1Matches:
    @pytest.fixture
    def csv_file(self, tmp_path, sample_matches_csv) -> str:
        p = tmp_path / "wc_matches.csv"
        p.write_bytes(sample_matches_csv)
        return p

    async def test_ingest_no_header_dataset(self, pg_pool, csv_file, settings):
        result = await ingest_csv(csv_file, "matches", settings)
        assert result.rows_read == 2
        assert result.rows_inserted == 2
        assert await count_rows(pg_pool, "raw.wc_matches") == 2

    async def test_ingest_columns_mapped_correctly(self, pg_pool, csv_file, settings):
        await ingest_csv(csv_file, "matches", settings)
        async with pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT home_team_name, away_team_name, match_id, round_id "
                "FROM raw.wc_matches ORDER BY _row_id LIMIT 1"
            )
        assert row["home_team_name"] == "Argentina"
        assert row["away_team_name"] == "France"
        assert row["match_id"] == "1"
        assert row["round_id"] == "1"


# ─── PLAYERS ────────────────────────────────────────────────────


class TestW1Players:
    @pytest.fixture
    def csv_file(self, tmp_path, sample_players_csv) -> str:
        p = tmp_path / "wc_players.csv"
        p.write_bytes(sample_players_csv)
        return p

    async def test_ingest_players(self, pg_pool, csv_file, settings):
        result = await ingest_csv(csv_file, "players", settings)
        assert result.rows_read == 2
        assert result.rows_inserted == 2
        assert await count_rows(pg_pool, "raw.wc_players") == 2

    async def test_ingest_players_data(self, pg_pool, csv_file, settings):
        await ingest_csv(csv_file, "players", settings)
        async with pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT player_name, position, team_initials FROM raw.wc_players ORDER BY _row_id LIMIT 1"  # noqa: E501
            )
        assert row["player_name"] == "Angel Bossio"
        assert row["position"] == "GK"
        assert row["team_initials"] == "ARG"
