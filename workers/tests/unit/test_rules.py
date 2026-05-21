import pytest

from worker.utils.constants import MAX_WC_YEAR, MIN_WC_YEAR
from worker.validators.rules import (
    validate_matches_row,
    validate_players_row,
    validate_round_row,
    validate_team_row,
    validate_winners_row,
)
from worker.validators.schemas import (
    RawMatchesRow,
    RawPlayersRow,
    RawWinnersRow,
)


# ═══════════════════════════════════════════════════════════════
# Fixtures compartidas
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def valid_winners_raw() -> RawWinnersRow:
    return RawWinnersRow(
        year="1930",
        country="Uruguay",
        winner="Uruguay",
        runners_up="Argentina",
        third="USA",
        fourth="Yugoslavia",
        goals_scored="70",
        qualified_teams="13",
        matches_played="18",
        attendance="590549",
    )


@pytest.fixture
def valid_matches_raw() -> RawMatchesRow:
    return RawMatchesRow(
        match_id="1",
        datetime="13 Jul 1930 - 15:00",
        stage="Group 1",
        stadium="Pocitos",
        city="Montevideo",
        home_team_name="Argentina",
        home_team_goals="1",
        away_team_goals="0",
        away_team_name="France",
        win_conditions="",
        attendance="4444",
        ht_home_goals="0",
        ht_away_goals="0",
        referee="LARGO CABALLERO Juan (PAR)",
        assistant_1="MATEUCCI Francisco (URU)",
        assistant_2="WARNKEN Alberto (CHI)",
        round_id="1",
        year="1930",
        home_team_initials="ARG",
        away_team_initials="FRA",
    )


@pytest.fixture
def valid_players_raw() -> RawPlayersRow:
    return RawPlayersRow(
        round_id="1",
        match_id="1",
        team_initials="ARG",
        coach_name="Juan Jose Tramutola",
        line_up="S",
        shirt_number="0",
        player_name="Angel Bossio",
        position="GK",
        event="",
    )


# ═══════════════════════════════════════════════════════════════
# validate_winners_row
# ═══════════════════════════════════════════════════════════════


class TestValidateWinnersRow:
    def test_valid_row(self, valid_winners_raw: RawWinnersRow):
        result = validate_winners_row(valid_winners_raw, raw_row_id=1)
        assert result.is_valid is True
        assert result.clean_row is not None
        assert result.clean_row.year == 1930
        assert result.clean_row.host_country == "Uruguay"
        assert result.clean_row.winner == "Uruguay"

    def test_missing_year(self, valid_winners_raw: RawWinnersRow):
        valid_winners_raw.year = ""
        result = validate_winners_row(valid_winners_raw)
        assert result.is_valid is False
        assert result.first_error_code == "MISSING_YEAR"

    def test_year_out_of_range_low(self, valid_winners_raw: RawWinnersRow):
        valid_winners_raw.year = "1929"
        result = validate_winners_row(valid_winners_raw)
        assert result.is_valid is False
        assert result.first_error_code == "INVALID_YEAR_RANGE (1930 - 2030)"

    def test_year_out_of_range_high(self, valid_winners_raw: RawWinnersRow):
        valid_winners_raw.year = "2031"
        result = validate_winners_row(valid_winners_raw)
        assert result.is_valid is False
        assert "INVALID_YEAR_RANGE" in result.first_error_code

    def test_missing_country(self, valid_winners_raw: RawWinnersRow):
        valid_winners_raw.country = ""
        result = validate_winners_row(valid_winners_raw)
        assert result.is_valid is False
        assert result.first_error_code == "MISSING_HOST_WINNER"

    def test_missing_winner(self, valid_winners_raw: RawWinnersRow):
        valid_winners_raw.winner = ""
        result = validate_winners_row(valid_winners_raw)
        assert result.is_valid is False
        assert result.first_error_code == "MISSING_WINNER"

    def test_missing_runners_up(self, valid_winners_raw: RawWinnersRow):
        valid_winners_raw.runners_up = ""
        result = validate_winners_row(valid_winners_raw)
        assert result.is_valid is False
        assert result.first_error_code == "MISSING_RUNNERS_UP"

    def test_missing_third_and_fourth_is_warning(self, valid_winners_raw: RawWinnersRow):
        valid_winners_raw.third = ""
        valid_winners_raw.fourth = ""
        result = validate_winners_row(valid_winners_raw)
        assert result.is_valid is True
        assert result.has_warning is True
        assert any(e.code == "MISSING_PODIUM" for e in result.errors)

    def test_negative_goals(self, valid_winners_raw: RawWinnersRow):
        valid_winners_raw.goals_scored = "-5"
        result = validate_winners_row(valid_winners_raw)
        assert result.is_valid is False
        assert result.first_error_code == "NEGATIVE_GOALS_SCORED"

    def test_qualified_teams_out_of_range(self, valid_winners_raw: RawWinnersRow):
        valid_winners_raw.qualified_teams = "100"
        result = validate_winners_row(valid_winners_raw)
        assert result.is_valid is False
        assert result.first_error_code == "NEGATIVE_QUALIFIED_TEAMS"

    def test_low_goals_avg_rejected_by_schema(self, valid_winners_raw: RawWinnersRow):
        valid_winners_raw.goals_scored = "4"
        with pytest.raises(Exception):
            validate_winners_row(valid_winners_raw)

    def test_high_goals_avg_is_warning(self, valid_winners_raw: RawWinnersRow):
        valid_winners_raw.goals_scored = "200"
        valid_winners_raw.matches_played = "18"
        result = validate_winners_row(valid_winners_raw)
        assert result.is_valid is True
        assert result.has_warning is True

    def test_raw_row_id_preserved(self, valid_winners_raw: RawWinnersRow):
        result = validate_winners_row(valid_winners_raw, raw_row_id=42)
        assert result.raw_row_id == 42

    def test_invalid_year_type(self, valid_winners_raw: RawWinnersRow):
        valid_winners_raw.year = "abc"
        result = validate_winners_row(valid_winners_raw)
        assert result.is_valid is False
        assert result.first_error_code == "MISSING_YEAR"


# ═══════════════════════════════════════════════════════════════
# validate_matches_row
# ═══════════════════════════════════════════════════════════════


class TestValidateMatchesRow:
    TOURNAMENT_ID = 1

    def test_valid_row(self, valid_matches_raw: RawMatchesRow):
        result = validate_matches_row(valid_matches_raw, self.TOURNAMENT_ID, raw_row_id=1)
        assert result.is_valid is True
        assert result.clean_row is not None
        assert result.clean_row.match_id == 1
        assert result.clean_row.home_team_initials == "ARG"
        assert result.clean_row.away_team_initials == "FRA"

    def test_invalid_match_id(self, valid_matches_raw: RawMatchesRow):
        valid_matches_raw.match_id = ""
        result = validate_matches_row(valid_matches_raw, self.TOURNAMENT_ID)
        assert result.is_valid is False
        assert result.first_error_code == "INVALID_MATCH_ID"

    def test_invalid_round_id(self, valid_matches_raw: RawMatchesRow):
        valid_matches_raw.round_id = "0"
        result = validate_matches_row(valid_matches_raw, self.TOURNAMENT_ID)
        assert result.is_valid is False
        assert result.first_error_code == "INVALID_ROUND_ID"

    def test_missing_stage(self, valid_matches_raw: RawMatchesRow):
        valid_matches_raw.stage = ""
        result = validate_matches_row(valid_matches_raw, self.TOURNAMENT_ID)
        assert result.is_valid is False
        assert result.first_error_code == "MISSING_STAGE"

    def test_negative_home_goals(self, valid_matches_raw: RawMatchesRow):
        valid_matches_raw.home_team_goals = "-1"
        result = validate_matches_row(valid_matches_raw, self.TOURNAMENT_ID)
        assert result.is_valid is False
        assert result.first_error_code == "INVALID_HOME_GOALS"

    def test_negative_away_goals(self, valid_matches_raw: RawMatchesRow):
        valid_matches_raw.away_team_goals = "-1"
        result = validate_matches_row(valid_matches_raw, self.TOURNAMENT_ID)
        assert result.is_valid is False
        assert result.first_error_code == "INVALID_AWAY_GOALS"

    def test_missing_home_initials(self, valid_matches_raw: RawMatchesRow):
        valid_matches_raw.home_team_initials = ""
        result = validate_matches_row(valid_matches_raw, self.TOURNAMENT_ID)
        assert result.is_valid is False
        assert result.first_error_code == "MISSING_HOME_INITIALS"

    def test_missing_away_initials(self, valid_matches_raw: RawMatchesRow):
        valid_matches_raw.away_team_initials = ""
        result = validate_matches_row(valid_matches_raw, self.TOURNAMENT_ID)
        assert result.is_valid is False
        assert result.first_error_code == "MISSING_AWAY_INITIALS"

    def test_year_out_of_range(self, valid_matches_raw: RawMatchesRow):
        valid_matches_raw.year = "1900"
        result = validate_matches_row(valid_matches_raw, self.TOURNAMENT_ID)
        assert result.is_valid is False
        assert result.first_error_code == "INVALID_YEAR_RANGE"

    def test_unparseable_attendance_is_warning(self, valid_matches_raw: RawMatchesRow):
        valid_matches_raw.attendance = "abc"
        result = validate_matches_row(valid_matches_raw, self.TOURNAMENT_ID)
        assert result.is_valid is True
        assert result.has_warning is True
        assert any(e.code == "UNPARSEABLE_ATTENDANCE" for e in result.errors)

    def test_datetime_parsed(self, valid_matches_raw: RawMatchesRow):
        result = validate_matches_row(valid_matches_raw, self.TOURNAMENT_ID)
        assert result.is_valid is True
        assert result.clean_row is not None
        assert result.clean_row.match_datetime is not None
        assert "1930-07-13" in result.clean_row.match_datetime

    def test_multiple_errors(self, valid_matches_raw: RawMatchesRow):
        valid_matches_raw.match_id = ""
        valid_matches_raw.round_id = ""
        valid_matches_raw.stage = ""
        result = validate_matches_row(valid_matches_raw, self.TOURNAMENT_ID)
        assert result.is_valid is False
        assert len(result.error_code) >= 3


# ═══════════════════════════════════════════════════════════════
# validate_players_row
# ═══════════════════════════════════════════════════════════════


class TestValidatePlayersRow:
    def test_valid_row(self, valid_players_raw: RawPlayersRow):
        result = validate_players_row(valid_players_raw, raw_row_id=1)
        assert result.is_valid is True
        assert result.clean_row is not None
        assert result.clean_row.match_id == 1
        assert result.clean_row.team_initials == "ARG"

    def test_invalid_round_id(self, valid_players_raw: RawPlayersRow):
        valid_players_raw.round_id = ""
        result = validate_players_row(valid_players_raw)
        assert result.is_valid is False
        assert result.first_error_code == "INVALID_ROUND_ID"

    def test_invalid_match_id(self, valid_players_raw: RawPlayersRow):
        valid_players_raw.match_id = ""
        result = validate_players_row(valid_players_raw)
        assert result.is_valid is False
        assert result.first_error_code == "INVALID_MATCH_ID"

    def test_missing_team_initials(self, valid_players_raw: RawPlayersRow):
        valid_players_raw.team_initials = ""
        result = validate_players_row(valid_players_raw)
        assert result.is_valid is False
        assert result.first_error_code == "MISSING_TEAM_INITIALS"

    def test_invalid_lineup_type(self, valid_players_raw: RawPlayersRow):
        valid_players_raw.line_up = "X"
        result = validate_players_row(valid_players_raw)
        assert result.is_valid is False
        assert result.first_error_code == "INVALID_LINEUP_TYPE"

    def test_missing_player_name(self, valid_players_raw: RawPlayersRow):
        valid_players_raw.player_name = ""
        result = validate_players_row(valid_players_raw)
        assert result.is_valid is False
        assert result.first_error_code == "MISSING_PLAYER_NAME"

    def test_unknown_position_is_warning(self, valid_players_raw: RawPlayersRow):
        valid_players_raw.position = "XYZ"
        result = validate_players_row(valid_players_raw)
        assert result.is_valid is True
        assert result.has_warning is True
        assert any(e.code == "UNKNOWN_POSITION" for e in result.errors)

    def test_unknown_event_is_warning(self, valid_players_raw: RawPlayersRow):
        valid_players_raw.event = "   "
        result = validate_players_row(valid_players_raw)
        assert result.is_valid is True
        assert result.has_warning is True
        assert any(e.code == "UNKNOWN_EVENT_CODE" for e in result.errors)

    def test_shirt_number_zero_converted_to_none(self, valid_players_raw: RawPlayersRow):
        result = validate_players_row(valid_players_raw)
        assert result.is_valid is True
        assert result.clean_row is not None
        assert result.clean_row.shirt_number is None

    def test_shirt_number_positive(self, valid_players_raw: RawPlayersRow):
        valid_players_raw.shirt_number = "10"
        result = validate_players_row(valid_players_raw)
        assert result.is_valid is True
        assert result.clean_row is not None
        assert result.clean_row.shirt_number == 10

    def test_valid_position_accepted(self, valid_players_raw: RawPlayersRow):
        for pos in ["GK", "DF", "MF", "FW"]:
            valid_players_raw.position = pos
            result = validate_players_row(valid_players_raw)
            assert result.is_valid is True
            assert result.clean_row is not None
            assert result.clean_row.position == pos


# ═══════════════════════════════════════════════════════════════
# validate_team_row
# ═══════════════════════════════════════════════════════════════


class TestValidateTeamRow:
    def test_valid_team(self):
        result = validate_team_row("BRA", name="Brazil", confederation="CONMEBOL")
        assert result.is_valid is True
        assert result.clean_row is not None
        assert result.clean_row.initials == "BRA"
        assert result.clean_row.name == "Brazil"

    def test_valid_without_name(self):
        result = validate_team_row("ARG")
        assert result.is_valid is True
        assert result.clean_row is not None
        assert result.clean_row.initials == "ARG"
        assert result.clean_row.name is None

    def test_missing_initials(self):
        result = validate_team_row("")
        assert result.is_valid is False
        assert result.first_error_code == "MISSING_TEAM_INITIALS"

    def test_none_initials(self):
        result = validate_team_row(None)
        assert result.is_valid is False
        assert result.first_error_code == "MISSING_TEAM_INITIALS"

    def test_normalizes_initials(self):
        result = validate_team_row(" bra ")
        assert result.is_valid is True
        assert result.clean_row is not None
        assert result.clean_row.initials == "BRA"

    def test_too_long_initials(self):
        result = validate_team_row("ABCD")
        assert result.is_valid is False


# ═══════════════════════════════════════════════════════════════
# validate_round_row
# ═══════════════════════════════════════════════════════════════


class TestValidateRoundRow:
    def test_valid_round(self):
        result = validate_round_row("1", "1", "Group 1")
        assert result.is_valid is True
        assert result.clean_row is not None
        assert result.clean_row.round_id == 1
        assert result.clean_row.tournament_id == 1
        assert result.clean_row.round_name == "Group 1"

    def test_invalid_round_id(self):
        result = validate_round_row("0", "1", "Group 1")
        assert result.is_valid is False
        assert result.first_error_code == "INVALID_ROUND_ID"

    def test_missing_round_id(self):
        result = validate_round_row(None, "1", "Group 1")
        assert result.is_valid is False
        assert result.first_error_code == "INVALID_ROUND_ID"

    def test_invalid_tournament_id(self):
        result = validate_round_row("1", "0", "Group 1")
        assert result.is_valid is False
        assert result.first_error_code == "INVALID_TOURNAMENT_ID"

    def test_missing_round_name(self):
        result = validate_round_row("1", "1", "")
        assert result.is_valid is False
        assert result.first_error_code == "MISSING_ROUND_NAME"
