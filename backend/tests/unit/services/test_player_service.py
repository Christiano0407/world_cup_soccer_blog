from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.core.exceptions import NotFoundError
from tests.conftest import MockResult


def _make_appearance(**overrides: object) -> MagicMock:
    a = MagicMock()
    a.player_match_id = 1
    a.match_id = 1
    a.team_initials = "ARG"
    a.coach_name = "Scaloni"
    a.lineup_type = "S"
    a.shirt_number = 10
    a.player_name = "Lionel Messi"
    a.position = "FW"
    a.event_code = "G"
    for k, v in overrides.items():
        setattr(a, k, v)
    return a


class TestListAppearances:
    async def test_list_all(self, player_service, mock_db) -> None:
        items = [_make_appearance(), _make_appearance(player_name="Di Maria")]
        mock_db.execute.side_effect = [
            MockResult(scalar_one=len(items)),
            MockResult(scalars_list=items),
        ]

        result = await player_service.list_appearances()

        assert result.total == 2
        assert len(result.items) == 2

    async def test_list_with_filters(self, player_service, mock_db) -> None:
        mock_db.execute.side_effect = [
            MockResult(scalar_one=1),
            MockResult(scalars_list=[_make_appearance()]),
        ]

        result = await player_service.list_appearances(team="ARG", position="FW", year=2022)

        assert result.total == 1

    async def test_list_empty(self, player_service, mock_db) -> None:
        mock_db.execute.side_effect = [
            MockResult(scalar_one=0),
            MockResult(scalars_list=[]),
        ]

        result = await player_service.list_appearances()

        assert result.items == []


class TestSearchPlayers:
    async def test_search_returns_results(self, player_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(
            mappings_list=[
                {"player_match_id": 1, "match_id": 1, "team_initials": "ARG",
                 "coach_name": "Scaloni", "lineup_type": "S", "shirt_number": 10,
                 "player_name": "Lionel Messi", "position": "FW", "event_code": "G"}
            ]
        )

        result = await player_service.search_players("Messi", limit=10)

        assert len(result) == 1

    async def test_search_empty(self, player_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(mappings_list=[])

        result = await player_service.search_players("NonExistent", limit=10)

        assert result == []


class TestGetTopScorers:
    async def test_all_time(self, player_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(
            all_list=[
                {
                    "player_name": "Messi", "team_initials": "ARG",
                    "goals": 13, "own_goals": 0, "matches_played": 26,
                    "first_wc": 2006, "last_wc": 2022, "editions": 5,
                }
            ]
        )

        result = await player_service.get_top_scorers(top=10)

        assert len(result) == 1
        assert result[0].goals == 13

    async def test_filtered_by_team(self, player_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(all_list=[])

        result = await player_service.get_top_scorers(top=5, team="BRA")

        assert result == []

    async def test_filtered_by_position(self, player_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(
            all_list=[
                {
                    "player_name": "Neuer", "team_initials": "GER",
                    "goals": 0, "own_goals": 0, "matches_played": 20,
                    "first_wc": 2010, "last_wc": 2022, "editions": 4,
                }
            ]
        )

        result = await player_service.get_top_scorers(top=5, position="GK")

        assert result[0].goals == 0


class TestGetPlayerCareer:
    async def test_career_success(self, player_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(
            mappings_one={
                "player_name": "Lionel Messi",
                "team_initials": "ARG",
                "total_appearances": 26,
                "starts": 24,
                "substitutions": 2,
                "goals": 13,
                "yellow_cards": 0,
                "red_cards": 0,
                "editions": [2006, 2010, 2014, 2018, 2022],
            }
        )

        result = await player_service.get_player_career("Lionel Messi")

        assert result.total_appearances == 26
        assert 2006 in result.editions

    async def test_career_not_found(self, player_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(mappings_one=None)

        with pytest.raises(NotFoundError, match="Jugador"):
            await player_service.get_player_career("NonExistent Player")
