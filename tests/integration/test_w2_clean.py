import pytest
import pytest_asyncio

from worker.cleaning.clean_w2 import CleanResults, clean_dataset

from .conftest import skip_if_no_pg, truncate_raw_tables

pytestmark = [skip_if_no_pg, pytest.mark.integration]


async def _seed_winners(pg_pool):
    async with pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO raw.wc_winners (_source_file, year, country, winner, runners_up, third, fourth,
                                         goals_scored, qualified_teams, matches_played, attendance)
            VALUES
            ('test.csv', '1930', 'Uruguay', 'Uruguay', 'Argentina', 'USA', 'Yugoslavia',
             '70', '13', '18', '590549'),
            ('test.csv', '1934', 'Italy', '', 'Czechoslovakia', 'Germany', 'Austria',
             '70', '16', '17', '363000')
            """
        )


async def _seed_matches(pg_pool):
    async with pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO raw.wc_matches (
                _source_file, year, datetime, stage, stadium, city,
                home_team_name, home_team_goals, away_team_goals, away_team_name,
                win_conditions, attendance, ht_home_goals, ht_away_goals,
                referee, assistant_1, assistant_2, round_id, match_id,
                home_team_initials, away_team_initials
            ) VALUES
            ('test.csv', '1930', '13 Jul 1930 - 15:00', 'Group 1', 'Pocitos', 'Montevideo',
             'Argentina', '1', '0', 'France', '', '4444', '0', '0',
             'Ref (PAR)', 'Asst1 (URU)', 'Asst2 (CHI)', '1', '1', 'ARG', 'FRA'),
            ('test.csv', '1930', '15 Jul 1930 - 16:00', '', 'Parque Central', 'Montevideo',
             'Argentina', '6', '3', 'Mexico', '', '3333', '3', '1',
             'Ref2 (FRA)', 'Asst1 (URU)', 'Asst2 (CHI)', '1', '2', 'ARG', 'MEX')
            """
        )


async def _seed_players(pg_pool):
    async with pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO raw.wc_players (
                _source_file, round_id, match_id, team_initials, coach_name,
                line_up, shirt_number, player_name, position, event
            ) VALUES
            ('test.csv', '1', '1', 'ARG', 'Coach', 'S', '0', 'Player A', 'GK', ''),
            ('test.csv', '1', '1', 'ARG', 'Coach', 'S', '10', 'Player B', 'FW', 'G'),
            ('test.csv', '1', '1', '', 'Coach', 'S', '5', 'Player C', 'MF', '')
            """
        )


# ─── WINNERS ────────────────────────────────────────────────────


class TestW2Winners:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, pg_pool):
        await _seed_winners(pg_pool)
        yield
        await truncate_raw_tables(pg_pool)

    async def test_valid_winners_marked(self, pg_pool, settings):
        result = await clean_dataset("winners", settings)
        assert isinstance(result, CleanResults)
        assert result.rows_checked == 2
        assert result.rows_valid == 1
        assert result.rows_rejected == 1
        assert result.rejection_rate == 50.0
        assert result.is_acceptable is False
        assert "MISSING_WINNER" in result.error_breakdown

    async def test_dead_letter_has_rejected(self, pg_pool, settings):
        await clean_dataset("winners", settings)
        async with pg_pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM raw.dead_letter")
            assert count >= 1

    async def test_valid_row_has_is_valid_true(self, pg_pool, settings):
        await clean_dataset("winners", settings)
        async with pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT _is_valid FROM raw.wc_winners WHERE year = '1930'"
            )
            assert row["_is_valid"] is True

    async def test_invalid_row_has_is_valid_false(self, pg_pool, settings):
        await clean_dataset("winners", settings)
        async with pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT _is_valid FROM raw.wc_winners WHERE year = '1934'"
            )
            assert row["_is_valid"] is False


# ─── MATCHES ────────────────────────────────────────────────────


class TestW2Matches:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, pg_pool):
        await _seed_matches(pg_pool)
        yield
        await truncate_raw_tables(pg_pool)

    async def test_valid_match_marked(self, pg_pool, settings):
        result = await clean_dataset("matches", settings)
        assert result.rows_checked == 2
        assert result.rows_valid >= 1
        assert result.rows_rejected >= 1

    async def test_match_missing_stage_rejected(self, pg_pool, settings):
        await clean_dataset("matches", settings)
        async with pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT _is_valid FROM raw.wc_matches WHERE match_id = '2'"
            )
            assert row["_is_valid"] is False


# ─── PLAYERS ────────────────────────────────────────────────────


class TestW2Players:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, pg_pool):
        await _seed_players(pg_pool)
        yield
        await truncate_raw_tables(pg_pool)

    async def test_valid_players_marked(self, pg_pool, settings):
        result = await clean_dataset("players", settings)
        assert result.rows_checked == 3
        assert result.rows_valid >= 2
        assert result.rows_rejected >= 1

    async def test_missing_initials_rejected(self, pg_pool, settings):
        await clean_dataset("players", settings)
        async with pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT _is_valid FROM raw.wc_players WHERE player_name = 'Player C'"
            )
            assert row["_is_valid"] is False

    async def test_player_event_code_preserved(self, pg_pool, settings):
        await clean_dataset("players", settings)
        async with pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT _is_valid FROM raw.wc_players WHERE player_name = 'Player B'"
            )
            assert row["_is_valid"] is True
