from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.schemas import TeamIn, TeamUpdate
from tests.conftest import MockResult


def _make_team(**overrides: object) -> MagicMock:
    team = MagicMock()
    team.team_id = 1
    team.initials = "ARG"
    team.name = "Argentina"
    team.confederation = "CONMEBOL"
    team.fifa_code = "ARG"
    team.active = True
    for k, v in overrides.items():
        setattr(team, k, v)
    return team


class TestListTeams:
    async def test_list_all(self, team_service, mock_db) -> None:
        teams = [_make_team(initials="ARG"), _make_team(initials="BRA")]
        mock_db.execute.return_value = MockResult(scalars_list=teams)

        result = await team_service.list_teams()

        assert len(result) == 2
        assert result[0].initials == "ARG"

    async def test_list_active_only(self, team_service, mock_db) -> None:
        teams = [_make_team(initials="ARG")]
        mock_db.execute.return_value = MockResult(scalars_list=teams)

        result = await team_service.list_teams(active=True)

        assert len(result) == 1
        mock_db.execute.assert_awaited_once()

    async def test_list_empty(self, team_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalars_list=[])

        result = await team_service.list_teams()

        assert result == []


class TestCreateTeam:
    async def test_create_success(self, team_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)
        data = TeamIn(initials="COL", name="Colombia")

        result = await team_service.create_team(data)

        assert result.initials == "COL"
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

    async def test_create_duplicate_raises(self, team_service, mock_db) -> None:
        existing = _make_team(initials="COL")
        mock_db.execute.return_value = MockResult(scalar_one=existing)
        data = TeamIn(initials="COL", name="Colombia")

        with pytest.raises(ConflictError, match="ya existe"):
            await team_service.create_team(data)

    async def test_create_case_insensitive_duplicate(self, team_service, mock_db) -> None:
        existing = _make_team(initials="COL")
        mock_db.execute.return_value = MockResult(scalar_one=existing)
        data = TeamIn(initials="col", name="Colombia")

        with pytest.raises(ConflictError):
            await team_service.create_team(data)


class TestUpdateTeam:
    async def test_update_name(self, team_service, mock_db) -> None:
        team = _make_team()
        mock_db.execute.return_value = MockResult(scalar_one=team)
        data = TeamUpdate(name="New Name")

        result = await team_service.update_team("ARG", data)

        assert result.initials == "ARG"
        assert team.name == "New Name"

    async def test_update_not_found(self, team_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)

        with pytest.raises(NotFoundError, match="no encontrada"):
            await team_service.update_team("ZZZ", TeamUpdate(name="Test"))

    async def test_update_no_changes(self, team_service, mock_db) -> None:
        team = _make_team()
        mock_db.execute.return_value = MockResult(scalar_one=team)

        result = await team_service.update_team("ARG", TeamUpdate())

        assert result.initials == "ARG"


class TestGetTeamStats:
    async def test_stats_success(self, team_service, mock_db) -> None:
        team = _make_team()
        mock_db.execute.side_effect = [
            MockResult(scalar_one=team),
            MockResult(
                scalar_one={
                    "tournaments_played": 5,
                    "titles": 2,
                    "runner_ups": 1,
                    "total_matches": 20,
                    "wins": 12,
                    "draws": 4,
                    "losses": 4,
                    "goals_scored": 40,
                    "goals_conceded": 15,
                }
            ),
        ]

        result = await team_service.get_team_stats("ARG")

        assert result.initials == "ARG"
        assert result.titles == 2
        assert result.win_rate_pct == 60.0

    async def test_stats_team_not_found(self, team_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)

        with pytest.raises(NotFoundError):
            await team_service.get_team_stats("ZZZ")


class TestHeadToHead:
    async def test_head_to_head_returns_stats(self, team_service, mock_db) -> None:
        mock_db.execute.side_effect = [
            MockResult(scalar_one=_make_team(initials="ARG")),
            MockResult(scalar_one=_make_team(initials="FRA")),
            MockResult(
                scalar_one={
                    "total_matches": 4,
                    "draws": 1,
                    "team_a_wins": 2,
                    "team_b_wins": 1,
                    "team_a_goals": 7,
                    "team_b_goals": 6,
                    "first_encounter": 1930,
                    "last_encounter": 2022,
                }
            ),
        ]

        result = await team_service.head_to_head("ARG", "FRA")

        assert result.team_a == "ARG"
        assert result.team_b == "FRA"
        assert result.total_matches == 4
        assert result.team_a_wins == 2
        assert result.draws == 1


class TestGetRanking:
    async def test_ranking_returns_sorted_stats(self, team_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(
            all_list=[
                {
                    "initials": "BRA", "name": "Brazil", "confederation": "CONMEBOL",
                    "tournaments_played": 10, "titles": 5, "runner_ups": 2,
                    "total_matches": 50, "wins": 35, "draws": 8, "losses": 7,
                    "goals_scored": 100, "goals_conceded": 30,
                },
                {
                    "initials": "ARG", "name": "Argentina", "confederation": "CONMEBOL",
                    "tournaments_played": 8, "titles": 3, "runner_ups": 3,
                    "total_matches": 40, "wins": 25, "draws": 8, "losses": 7,
                    "goals_scored": 70, "goals_conceded": 25,
                },
            ]
        )

        result = await team_service.get_ranking(min_matches=0)

        assert len(result) == 2
        assert result[0].titles >= result[1].titles

    async def test_ranking_min_matches_filter(self, team_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(all_list=[])

        result = await team_service.get_ranking(min_matches=5)

        assert result == []

    async def test_ranking_empty(self, team_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(all_list=[])

        result = await team_service.get_ranking()

        assert result == []


class TestGetMatches:
    async def test_get_matches_returns_paginated(self, team_service, mock_db) -> None:
        mock_db.execute.side_effect = [
            MockResult(scalar_one=_make_team(initials="ARG")),
            MockResult(scalar_one=10),
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

        result = await team_service.get_matches("ARG")

        assert result.total == 10
        assert len(result.items) == 1
