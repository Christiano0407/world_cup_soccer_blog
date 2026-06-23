from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.core.exceptions import NotFoundError
from tests.conftest import MockResult


def _make_match(**overrides: object) -> MagicMock:
    m = MagicMock()
    m.match_id = 1
    m.tournament_id = 1
    m.year = 2022
    m.stage = "Final"
    m.match_datetime = "2022-12-18 18:00:00+00:00"
    m.stadium = "Lusail Stadium"
    m.city = "Lusail"
    m.home_team_initials = "ARG"
    m.away_team_initials = "FRA"
    m.home_goals = 3
    m.away_goals = 3
    m.ht_home_goals = 2
    m.ht_away_goals = 0
    m.win_conditions = "Penalties"
    m.attendance = 88966
    m.referee = "Szymon Marciniak"
    m.home_team_name = "Argentina"
    m.away_team_name = "France"
    for k, v in overrides.items():
        setattr(m, k, v)
    return m


class TestListMatches:
    async def test_list_all(self, match_service, mock_db) -> None:
        matches = [_make_match(match_id=1), _make_match(match_id=2)]
        mock_db.execute.side_effect = [
            MockResult(scalar_one=len(matches)),
            MockResult(scalars_list=matches),
        ]

        result = await match_service.list_matches()

        assert result.total == 2
        assert len(result.items) == 2

    async def test_list_with_filters(self, match_service, mock_db) -> None:
        match_service._db.execute.side_effect = [
            MockResult(scalar_one=1),
            MockResult(scalars_list=[_make_match()]),
        ]

        result = await match_service.list_matches(year=2022, stage="Final", team="ARG", min_goals=3)

        assert result.total == 1

    async def test_list_empty(self, match_service, mock_db) -> None:
        mock_db.execute.side_effect = [
            MockResult(scalar_one=0),
            MockResult(scalars_list=[]),
        ]

        result = await match_service.list_matches()

        assert result.items == []


class TestSearchMatches:
    async def test_search_returns_results(self, match_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(
            mappings_list=[
                {"match_id": 1, "year": 2022, "stage": "Final", "match_datetime": "2022-12-18",
                 "home_team_initials": "ARG", "away_team_initials": "FRA",
                 "home_goals": 3, "away_goals": 3}
            ]
        )

        result = await match_service.search_matches("Lusail")

        assert len(result) >= 1
        assert result[0].match_id == 1

    async def test_search_empty(self, match_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(mappings_list=[])

        result = await match_service.search_matches("NonExistent")

        assert result == []


class TestGetMatch:
    async def test_get_success(self, match_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(
            mappings_one={"match_id": 1, "tournament_id": 1, "year": 2022, "stage": "Final",
                          "match_datetime": "2022-12-18 18:00:00+00:00",
                          "stadium": "Lusail", "city": "Lusail",
                          "home_team_initials": "ARG", "away_team_initials": "FRA",
                          "home_team_name": "Argentina", "away_team_name": "France",
                          "home_goals": 3, "away_goals": 3,
                          "ht_home_goals": 2, "ht_away_goals": 0,
                          "win_conditions": None, "attendance": 88966, "referee": "Szymon"}
        )

        result = await match_service.get_match(1)

        assert result.match_id == 1

    async def test_get_not_found(self, match_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(mappings_one=None)

        with pytest.raises(NotFoundError, match="9999"):
            await match_service.get_match(9999)


class TestGetMatchPlayers:
    async def test_get_players_success(self, match_service, mock_db) -> None:
        match = _make_match()
        mock_db.execute.side_effect = [
            MockResult(scalar_one=match),
            MockResult(
                scalars_list=[
                    MagicMock(
                        player_match_id=1, match_id=1, team_initials="ARG",
                        coach_name="Scaloni", lineup_type="S", shirt_number=10,
                        player_name="Messi", position="FW", event_code="G",
                    )
                ]
            ),
        ]

        result = await match_service.get_match_players(1)

        assert len(result) == 1
        assert result[0].player_name == "Messi"

    async def test_get_players_not_found(self, match_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)

        with pytest.raises(NotFoundError):
            await match_service.get_match_players(9999)
