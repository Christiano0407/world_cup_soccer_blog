from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.schemas import TournamentIn, TournamentUpdate
from tests.conftest import MockResult


def _make_tournament(**overrides: object) -> MagicMock:
    t = MagicMock()
    t.tournament_id = 1
    t.year = 2022
    t.host_country = "Qatar"
    t.winner = "Argentina"
    t.runners_up = "France"
    t.third_place = "Croatia"
    t.fourth_place = "Morocco"
    t.goals_scored = 100
    t.qualified_teams = 32
    t.matches_played = 64
    t.attendance_total = 1000000
    t.avg_goals_per_match = 2.5
    for k, v in overrides.items():
        setattr(t, k, v)
    return t


class TestListTournaments:
    async def test_list_all(self, tournament_service, mock_db) -> None:
        tournaments = [_make_tournament(year=2022), _make_tournament(year=2018)]
        mock_db.execute.side_effect = [
            MockResult(scalar_one=len(tournaments)),
            MockResult(scalars_list=tournaments),
        ]

        result = await tournament_service.list_tournaments()

        assert result.total == 2
        assert len(result.items) == 2

    async def test_list_empty(self, tournament_service, mock_db) -> None:
        mock_db.execute.side_effect = [
            MockResult(scalar_one=0),
            MockResult(scalars_list=[]),
        ]

        result = await tournament_service.list_tournaments()

        assert result.total == 0
        assert result.items == []

    async def test_list_with_year_filter(self, tournament_service, mock_db) -> None:
        mock_db.execute.side_effect = [
            MockResult(scalar_one=1),
            MockResult(scalars_list=[_make_tournament(year=2022)]),
        ]

        result = await tournament_service.list_tournaments(year_from=2020, year_to=2023)

        assert result.total == 1


class TestGetTournament:
    async def test_get_success(self, tournament_service, mock_db) -> None:
        t = _make_tournament(avg_goals_per_match=1.56)
        mock_db.execute.return_value = MockResult(scalar_one=t)

        result = await tournament_service.get_tournament(2022)

        assert result.year == 2022
        assert result.avg_goals_per_match == 1.56

    async def test_get_not_found(self, tournament_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)

        with pytest.raises(NotFoundError, match="Torneo"):
            await tournament_service.get_tournament(9999)


class TestCreateTournament:
    async def test_create_success(self, tournament_service, mock_db) -> None:
        mock_db.execute.side_effect = [
            MockResult(scalar_one=None),
        ]
        data = TournamentIn(
            year=2026, host_country="USA", winner="Argentina",
            runners_up="Brazil", goals_scored=100, qualified_teams=48, matches_played=80,
        )

        result = await tournament_service.create_tournament(data)

        assert result.year == 2026
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

    async def test_create_duplicate_raises(self, tournament_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=_make_tournament())
        data = TournamentIn(
            year=2022, host_country="Qatar", winner="Argentina",
            runners_up="France", goals_scored=100, qualified_teams=32, matches_played=64,
        )

        with pytest.raises(ConflictError, match="ya existe"):
            await tournament_service.create_tournament(data)


class TestUpdateTournament:
    async def test_update_success(self, tournament_service, mock_db) -> None:
        t = _make_tournament()
        mock_db.execute.return_value = MockResult(scalar_one=t)
        data = TournamentUpdate(winner="Brazil")

        result = await tournament_service.update_tournament(2022, data)

        assert result.winner == t.winner

    async def test_update_not_found(self, tournament_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)

        with pytest.raises(NotFoundError):
            await tournament_service.update_tournament(9999, TournamentUpdate())


class TestDeleteTournament:
    async def test_delete_success(self, tournament_service, mock_db) -> None:
        t = _make_tournament()
        mock_db.execute.return_value = MockResult(scalar_one=t)

        await tournament_service.delete_tournament(2022)

        mock_db.delete.assert_called_once_with(t)

    async def test_delete_not_found(self, tournament_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)

        with pytest.raises(NotFoundError):
            await tournament_service.delete_tournament(9999)


class TestGetMatches:
    async def test_get_matches_paginated(self, tournament_service, mock_db) -> None:
        t = _make_tournament()
        mock_db.execute.side_effect = [
            MockResult(scalar_one=t),
            MockResult(scalar_one=5),
            MockResult(
                scalars_list=[
                    MagicMock(
                        match_id=1, year=2022, stage="Final",
                        match_datetime="2022-12-18",
                        home_team_initials="ARG", away_team_initials="FRA",
                        home_goals=3, away_goals=3,
                    )
                ]
            ),
        ]

        result = await tournament_service.get_matches(2022)

        assert result.total == 5
        assert len(result.items) == 1


class TestGetTopScorers:
    async def test_top_scorers_success(self, tournament_service, mock_db) -> None:
        t = _make_tournament()
        mock_db.execute.side_effect = [
            MockResult(scalar_one=t),
            MockResult(
                all_list=[
                    {
                        "player_name": "Messi",
                        "team_initials": "ARG",
                        "goals": 7,
                        "own_goals": 0,
                        "matches_played": 7,
                        "first_wc": 2022,
                        "last_wc": 2022,
                        "editions": 1,
                    }
                ]
            ),
        ]

        result = await tournament_service.get_top_scorers(2022, top=10)

        assert len(result) == 1
        assert result[0].player_name == "Messi"


class TestGetTeams:
    async def test_get_teams_success(self, tournament_service, mock_db) -> None:
        t = _make_tournament()
        mock_db.execute.side_effect = [
            MockResult(scalar_one=t),
            MockResult(
                mappings_list=[
                    {"team_id": 1, "initials": "ARG", "name": "Argentina", "confederation": "CONMEBOL", "fifa_code": "ARG", "active": True}
                ]
            ),
        ]

        result = await tournament_service.get_teams(2022)

        assert len(result) == 1
        assert result[0].initials == "ARG"
