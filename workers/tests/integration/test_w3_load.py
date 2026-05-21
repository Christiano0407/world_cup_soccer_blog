import pytest
import pytest_asyncio

from worker.loading.load_w3 import LoadResult, load_all

from .conftest import count_rows, skip_if_no_pg, truncate_public_tables, truncate_raw_tables

pytestmark = [skip_if_no_pg, pytest.mark.integration]


async def _seed_valid_data(pg_pool):
    """Insert valid raw data for a full W3 pipeline test."""
    async with pg_pool.acquire() as conn:
        # Winners
        await conn.execute(
            """
            INSERT INTO raw.wc_winners (
                _source_file, _is_valid, year, country, winner, runners_up, third, fourth,
                goals_scored, qualified_teams, matches_played, attendance
            ) VALUES
            ('test.csv', TRUE, '1930', 'Uruguay', 'Uruguay', 'Argentina', 'USA', 'Yugoslavia',
             '70', '13', '18', '590549')
            """
        )
        # Matches
        await conn.execute(
            """
            INSERT INTO raw.wc_matches (
                _source_file, _is_valid,
                year, datetime, stage, stadium, city,
                home_team_name, home_team_goals, away_team_goals, away_team_name,
                win_conditions, attendance, ht_home_goals, ht_away_goals,
                referee, assistant_1, assistant_2, round_id, match_id,
                home_team_initials, away_team_initials
            ) VALUES
            ('test.csv', TRUE,
             '1930', '13 Jul 1930 - 15:00', 'Group 1', 'Pocitos', 'Montevideo',
             'Argentina', '1', '0', 'France', '', '4444', '0', '0',
             'Ref (PAR)', 'Asst1 (URU)', 'Asst2 (CHI)', '1', '1', 'ARG', 'FRA'),
            ('test.csv', TRUE,
             '1930', '19 Jul 1930 - 15:00', 'Group 1', 'Parque Central', 'Montevideo',
             'Argentina', '6', '3', 'Mexico', '', '3333', '3', '1',
             'Ref2 (FRA)', 'Asst1 (URU)', 'Asst2 (CHI)', '1', '2', 'ARG', 'MEX')
            """
        )
        # Players
        await conn.execute(
            """
            INSERT INTO raw.wc_players (
                _source_file, _is_valid,
                round_id, match_id, team_initials, coach_name,
                line_up, shirt_number, player_name, position, event
            ) VALUES
            ('test.csv', TRUE, '1', '1', 'ARG', 'Coach Tramutola', 'S', '0',
             'Angel Bossio', 'GK', ''),
            ('test.csv', TRUE, '1', '1', 'ARG', 'Coach Tramutola', 'S', '4',
             'Alberto Chividini', 'DF', ''),
            ('test.csv', TRUE, '1', '2', 'ARG', 'Coach Tramutola', 'S', '10', 'Messi', 'FW', 'G')
            """
        )


class TestW3Pipeline:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, pg_pool):
        await truncate_public_tables(pg_pool)
        await truncate_raw_tables(pg_pool)
        await _seed_valid_data(pg_pool)
        yield
        await truncate_public_tables(pg_pool)
        await truncate_raw_tables(pg_pool)

    async def test_load_all_returns_result(self, pg_pool, settings):
        result = await load_all(settings)
        assert isinstance(result, LoadResult)

    async def test_teams_loaded(self, pg_pool, settings):
        await load_all(settings)
        teams = set()
        async with pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT initials FROM public.teams")
            teams = {r["initials"] for r in rows}
        assert "ARG" in teams
        assert "FRA" in teams
        assert "MEX" in teams

    async def test_tournament_loaded(self, pg_pool, settings):
        await load_all(settings)
        async with pg_pool.acquire() as conn:
            t = await conn.fetchrow(
                "SELECT year, winner, host_country FROM public.tournaments WHERE year = 1930"
            )
        assert t is not None
        assert t["winner"] == "Uruguay"
        assert t["host_country"] == "Uruguay"

    async def test_rounds_loaded(self, pg_pool, settings):
        await load_all(settings)
        async with pg_pool.acquire() as conn:
            r = await conn.fetchrow(
                """
                SELECT r.round_name, r.tournament_id
                FROM public.rounds r
                JOIN public.tournaments t ON r.tournament_id = t.tournament_id
                WHERE t.year = 1930
                """
            )
        assert r is not None
        assert r["round_name"] == "Group 1"

    async def test_matches_loaded(self, pg_pool, settings):
        await load_all(settings)
        async with pg_pool.acquire() as conn:
            m = await conn.fetchrow(
                "SELECT match_id, home_team_initials, away_team_initials, home_goals, away_goals "
                "FROM public.matches ORDER BY match_id LIMIT 1"
            )
        assert m is not None
        assert m["match_id"] == 1
        assert m["home_team_initials"] == "ARG"
        assert m["away_team_initials"] == "FRA"
        assert m["home_goals"] == 1
        assert m["away_goals"] == 0

    async def test_match_players_loaded(self, pg_pool, settings):
        await load_all(settings)
        async with pg_pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM public.match_players")
            assert count >= 2

    async def test_match_players_data(self, pg_pool, settings):
        await load_all(settings)
        async with pg_pool.acquire() as conn:
            mp = await conn.fetchrow(
                "SELECT player_name, position, team_initials, lineup_type "
                "FROM public.match_players ORDER BY player_name LIMIT 1"
            )
        assert mp is not None
        assert mp["player_name"] == "Alberto Chividini"
        assert mp["team_initials"] == "ARG"

    async def test_load_idempotent(self, pg_pool, settings):
        await load_all(settings)
        first_count = await count_rows(pg_pool, "public.teams")
        await load_all(settings)
        second_count = await count_rows(pg_pool, "public.teams")
        assert first_count == second_count

    async def test_parquet_exported(self, pg_pool, settings, minio_client):
        result = await load_all(settings)
        assert len(result.parquet_files) > 0
        for key in result.parquet_files:
            obj = minio_client.get_object(settings.minio_bucket_parquet, key)
            assert obj.read()
            obj.close()
            obj.release_conn()

    async def test_summary_logged(self, pg_pool, settings):
        result = await load_all(settings)
        assert result.teams_upserted >= 3
        assert result.tournaments_upserted == 1
        assert result.rounds_upserted >= 1
        assert result.matches_upserted == 2
        assert result.match_players_upserted >= 2
        assert result.warehouse_refreshed is True
