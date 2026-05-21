import pytest
from pydantic import ValidationError

from worker.validators.schemas import (
    CleanMatchesRow,
    CleanPlayersRow,
    CleanRoundRow,
    CleanTeamRow,
    CleanWinnersRow,
    RawMatchesRow,
    RawPlayersRow,
    RawWinnersRow,
)

# ═══════════════════════════════════════════════════════════════
# RawWinnersRow
# ═══════════════════════════════════════════════════════════════


class TestRawWinnersRow:
    def test_all_fields_default_to_none(self):
        row = RawWinnersRow()
        assert row.year is None
        assert row.country is None
        assert row.winner is None

    def test_accepts_valid_data(self):
        row = RawWinnersRow(
            year="1930",
            country="Uruguay",
            winner="Uruguay",
            runners_up="Argentina",
        )
        assert row.year == "1930"

    def test_strips_whitespace(self):
        row = RawWinnersRow(year="  1930  ")
        assert row.year == "1930"


# ═══════════════════════════════════════════════════════════════
# CleanWinnersRow
# ═══════════════════════════════════════════════════════════════


class TestCleanWinnersRow:
    def test_valid_row(self):
        row = CleanWinnersRow(
            year=1930,
            winner="Uruguay",
            runners_up="Argentina",
            goals_scored=70,
            qualified_teams=13,
            matches_played=18,
        )
        assert row.year == 1930
        assert row.winner == "Uruguay"

    def test_year_below_min_raises(self):
        with pytest.raises(ValidationError):
            CleanWinnersRow(
                year=1929,
                winner="Uruguay",
                runners_up="Argentina",
                goals_scored=70,
                qualified_teams=13,
                matches_played=18,
            )

    def test_year_above_max_raises(self):
        with pytest.raises(ValidationError):
            CleanWinnersRow(
                year=2031,
                winner="Uruguay",
                runners_up="Argentina",
                goals_scored=70,
                qualified_teams=13,
                matches_played=18,
            )

    def test_winner_empty_raises(self):
        with pytest.raises(ValidationError):
            CleanWinnersRow(
                year=1930,
                winner="",
                runners_up="Argentina",
                goals_scored=70,
                qualified_teams=13,
                matches_played=18,
            )

    def test_goals_scored_negative_raises(self):
        with pytest.raises(ValidationError):
            CleanWinnersRow(
                year=1930,
                winner="Uruguay",
                runners_up="Argentina",
                goals_scored=-1,
                qualified_teams=13,
                matches_played=18,
            )

    def test_goals_coherent_with_match_raises_on_low_avg(self):
        with pytest.raises(ValidationError, match="avg"):
            CleanWinnersRow(
                year=1930,
                winner="Uruguay",
                runners_up="Argentina",
                goals_scored=4,
                qualified_teams=13,
                matches_played=18,
            )

    def test_qualified_teams_below_min_raises(self):
        with pytest.raises(ValidationError):
            CleanWinnersRow(
                year=1930,
                winner="Uruguay",
                runners_up="Argentina",
                goals_scored=70,
                qualified_teams=0,
                matches_played=18,
            )

    def test_qualified_teams_above_max_raises(self):
        with pytest.raises(ValidationError):
            CleanWinnersRow(
                year=1930,
                winner="Uruguay",
                runners_up="Argentina",
                goals_scored=70,
                qualified_teams=49,
                matches_played=18,
            )


# ═══════════════════════════════════════════════════════════════
# CleanTeamRow
# ═══════════════════════════════════════════════════════════════


class TestCleanTeamRow:
    def test_valid_team(self):
        row = CleanTeamRow(initials="BRA", name="Brazil")
        assert row.initials == "BRA"
        assert row.name == "Brazil"

    def test_invalid_initials_raises(self):
        with pytest.raises(ValidationError):
            CleanTeamRow(initials="ABCD")

    def test_initials_normalized(self):
        row = CleanTeamRow(initials="bra")
        assert row.initials == "BRA"

    def test_name_optional(self):
        row = CleanTeamRow(initials="ARG")
        assert row.name is None


# ═══════════════════════════════════════════════════════════════
# CleanRoundRow
# ═══════════════════════════════════════════════════════════════


class TestCleanRoundRow:
    def test_valid_round(self):
        row = CleanRoundRow(round_id=1, tournament_id=1, round_name="Group 1")
        assert row.round_id == 1
        assert row.round_name == "Group 1"

    def test_round_id_below_one_raises(self):
        with pytest.raises(ValidationError):
            CleanRoundRow(round_id=0, tournament_id=1, round_name="Group 1")


# ═══════════════════════════════════════════════════════════════
# RawMatchesRow
# ═══════════════════════════════════════════════════════════════


class TestRawMatchesRow:
    def test_all_fields_default_to_none(self):
        row = RawMatchesRow()
        assert row.match_id is None
        assert row.stage is None

    def test_accepts_valid_data(self):
        row = RawMatchesRow(
            match_id="1",
            year="1930",
            stage="Group 1",
            home_team_initials="ARG",
            away_team_initials="FRA",
        )
        assert row.match_id == "1"

    def test_strips_whitespace(self):
        row = RawMatchesRow(year="  1930  ")
        assert row.year == "1930"


# ═══════════════════════════════════════════════════════════════
# CleanMatchesRow
# ═══════════════════════════════════════════════════════════════


class TestCleanMatchesRow:
    @pytest.fixture
    def valid_data(self) -> dict:
        return {
            "match_id": 1,
            "tournament_id": 1,
            "round_id": 1,
            "year": 1930,
            "stage": "Group 1",
            "home_goals": 1,
            "away_goals": 0,
            "home_team_initials": "ARG",
            "away_team_initials": "FRA",
        }

    def test_valid_row(self, valid_data: dict):
        row = CleanMatchesRow(**valid_data)
        assert row.match_id == 1
        assert row.home_team_initials == "ARG"

    def test_teams_must_differ(self, valid_data: dict):
        valid_data["home_team_initials"] = "BRA"
        valid_data["away_team_initials"] = "BRA"
        with pytest.raises(ValidationError, match="no pueden ser el mismo equipo"):
            CleanMatchesRow(**valid_data)

    def test_halftime_home_goals_not_exceed_total(self, valid_data: dict):
        valid_data["ht_home_goals"] = 5
        valid_data["home_goals"] = 2
        with pytest.raises(ValidationError, match="ht_home_goals"):
            CleanMatchesRow(**valid_data)

    def test_halftime_away_goals_not_exceed_total(self, valid_data: dict):
        valid_data["ht_away_goals"] = 5
        valid_data["away_goals"] = 2
        with pytest.raises(ValidationError, match="ht_away_goals"):
            CleanMatchesRow(**valid_data)

    def test_ht_both_or_neither(self, valid_data: dict):
        valid_data["ht_home_goals"] = 1
        valid_data["ht_away_goals"] = None
        with pytest.raises(ValidationError, match="ambos None"):
            CleanMatchesRow(**valid_data)

    def test_initials_invalid_raises(self, valid_data: dict):
        valid_data["home_team_initials"] = "ABCD"
        with pytest.raises(ValidationError):
            CleanMatchesRow(**valid_data)

    def test_year_out_of_range_raises(self, valid_data: dict):
        valid_data["year"] = 1900
        with pytest.raises(ValidationError):
            CleanMatchesRow(**valid_data)

    def test_attendance_over_max_warns(self, valid_data: dict):
        valid_data["attendance"] = 300_000
        with pytest.raises(ValidationError):
            CleanMatchesRow(**valid_data)


# ═══════════════════════════════════════════════════════════════
# RawPlayersRow
# ═══════════════════════════════════════════════════════════════


class TestRawPlayersRow:
    def test_all_fields_default_to_none(self):
        row = RawPlayersRow()
        assert row.player_name is None
        assert row.position is None

    def test_accepts_valid_data(self):
        row = RawPlayersRow(
            round_id="1",
            match_id="1",
            team_initials="ARG",
            player_name="Messi",
        )
        assert row.team_initials == "ARG"

    def test_strips_whitespace(self):
        row = RawPlayersRow(player_name="  Messi  ")
        assert row.player_name == "Messi"


# ═══════════════════════════════════════════════════════════════
# CleanPlayersRow
# ═══════════════════════════════════════════════════════════════


class TestCleanPlayersRow:
    @pytest.fixture
    def valid_data(self) -> dict:
        return {
            "round_id": 1,
            "match_id": 1,
            "team_initials": "ARG",
            "lineup_type": "S",
            "player_name": "Lionel Messi",
        }

    def test_valid_row(self, valid_data: dict):
        row = CleanPlayersRow(**valid_data)
        assert row.match_id == 1
        assert row.team_initials == "ARG"
        assert row.player_name == "Lionel Messi"

    def test_invalid_initials_raises(self, valid_data: dict):
        valid_data["team_initials"] = "ABCD"
        with pytest.raises(ValidationError):
            CleanPlayersRow(**valid_data)

    def test_invalid_lineup_type_raises(self, valid_data: dict):
        valid_data["lineup_type"] = "X"
        with pytest.raises(ValidationError):
            CleanPlayersRow(**valid_data)

    def test_empty_player_name_raises(self, valid_data: dict):
        valid_data["player_name"] = ""
        with pytest.raises(ValidationError):
            CleanPlayersRow(**valid_data)

    def test_player_name_stripped(self, valid_data: dict):
        valid_data["player_name"] = "  Angel Di Maria  "
        row = CleanPlayersRow(**valid_data)
        assert row.player_name == "Angel Di Maria"

    def test_shirt_number_range(self, valid_data: dict):
        valid_data["shirt_number"] = 100
        with pytest.raises(ValidationError):
            CleanPlayersRow(**valid_data)

    def test_optional_position(self, valid_data: dict):
        valid_data["position"] = "FW"
        row = CleanPlayersRow(**valid_data)
        assert row.position == "FW"

    def test_invalid_event_code_returns_none(self, valid_data: dict):
        valid_data["event_code"] = "ZZZ"
        row = CleanPlayersRow(**valid_data)
        assert row.event_code is None

    def test_valid_event_code(self, valid_data: dict):
        valid_data["event_code"] = "G"
        row = CleanPlayersRow(**valid_data)
        assert row.event_code == "G"

    def test_goal_with_minute(self, valid_data: dict):
        valid_data["event_code"] = "G40"
        row = CleanPlayersRow(**valid_data)
        assert row.event_code == "G40"
