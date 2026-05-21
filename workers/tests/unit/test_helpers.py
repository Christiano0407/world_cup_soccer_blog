from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from worker.utils.helpers import (
    clean_cell,
    format_s3_key,
    normalize_initials,
    normalize_player_position,
    normalize_team_names,
    normalize_text,
    normalized_event_football_players_code,
    normalized_lineup_type,
    now_utc,
    parse_attendance,
    parse_bool,
    parse_date,
    parse_datetime_csv,
    parse_decimal,
    parse_int,
    slugify,
)


# ═══════════════════════════════════════════════════════════════
# parse_bool
# ═══════════════════════════════════════════════════════════════


class TestParseBool:
    def test_true_values(self):
        for v in ["true", "TRUE", "True", "1", "yes", "YES", "SI", "S", "Y"]:
            assert parse_bool(v) is True

    def test_false_values(self):
        for v in ["false", "FALSE", "False", "0", "no", "NO", "N"]:
            assert parse_bool(v) is False

    def test_ambiguous_returns_none(self):
        for v in [None, "", "maybe", "unknown", "2", "t"]:
            assert parse_bool(v) is None

    def test_whitespace_handling(self):
        assert parse_bool("  true  ") is True
        assert parse_bool("  false  ") is False
        assert parse_bool("  1  ") is True


# ═══════════════════════════════════════════════════════════════
# parse_decimal
# ═══════════════════════════════════════════════════════════════


class TestParseDecimal:
    def test_normal_decimal(self):
        assert parse_decimal("123.45") == Decimal("123.45")

    def test_comma_as_decimal_separator(self):
        assert parse_decimal("123,45") == Decimal("123.45")

    def test_integer_string(self):
        assert parse_decimal("123") == Decimal("123")

    def test_none_returns_none(self):
        assert parse_decimal(None) is None

    def test_empty_string_returns_none(self):
        assert parse_decimal("") is None

    def test_whitespace_only_returns_none(self):
        assert parse_decimal("   ") is None

    def test_invalid_returns_none(self):
        assert parse_decimal("abc") is None

    def test_negative(self):
        assert parse_decimal("-5.5") == Decimal("-5.5")


# ═══════════════════════════════════════════════════════════════
# parse_int
# ═══════════════════════════════════════════════════════════════


class TestParseInt:
    def test_normal_int(self):
        assert parse_int("123") == 123

    def test_negative_int(self):
        assert parse_int("-5") == -5

    def test_leading_zeros(self):
        assert parse_int("007") == 7

    def test_none_returns_none(self):
        assert parse_int(None) is None

    def test_empty_returns_none(self):
        assert parse_int("") is None

    def test_whitespace_returns_none(self):
        assert parse_int("  ") is None

    def test_invalid_returns_none(self):
        assert parse_int("abc") is None

    def test_float_string_raises_valueerror(self):
        assert parse_int("12.5") is None

    def test_strips_whitespace(self):
        assert parse_int("  42  ") == 42


# ═══════════════════════════════════════════════════════════════
# parse_attendance
# ═══════════════════════════════════════════════════════════════


class TestParseAttendance:
    def test_european_dot_thousands(self):
        assert parse_attendance("590.549") == 590549

    def test_multiple_dots(self):
        assert parse_attendance("1.045.246") == 1045246

    def test_small_dot_number(self):
        assert parse_attendance("363.000") == 363000

    def test_plain_integer(self):
        assert parse_attendance("4444") == 4444

    def test_comma_thousands(self):
        assert parse_attendance("590,549") == 590549

    def test_none_returns_none(self):
        assert parse_attendance(None) is None

    def test_empty_returns_none(self):
        assert parse_attendance("") is None

    def test_whitespace_returns_none(self):
        assert parse_attendance("  ") is None

    def test_invalid_returns_none(self):
        assert parse_attendance("abc") is None

    def test_negative_returns_none(self):
        assert parse_attendance("-100") is None


# ═══════════════════════════════════════════════════════════════
# parse_date
# ═══════════════════════════════════════════════════════════════


class TestParseDate:
    def test_iso_format(self):
        assert parse_date("2023-01-15") == date(2023, 1, 15)

    def test_dmy_slash(self):
        assert parse_date("15/01/2023") == date(2023, 1, 15)

    def test_mdy_slash(self):
        assert parse_date("01/15/2023") == date(2023, 1, 15)

    def test_compact_format(self):
        assert parse_date("20230115") == date(2023, 1, 15)

    def test_none_returns_none(self):
        assert parse_date(None) is None

    def test_empty_returns_none(self):
        assert parse_date("") is None

    def test_invalid_returns_none(self):
        assert parse_date("not-a-date") is None


# ═══════════════════════════════════════════════════════════════
# parse_datetime_csv
# ═══════════════════════════════════════════════════════════════


class TestParseDatetimeCsv:
    def test_main_csv_format(self):
        result = parse_datetime_csv("13 Jul 1930 - 15:00")
        assert result == datetime(1930, 7, 13, 15, 0)

    def test_with_seconds(self):
        result = parse_datetime_csv("13 Jul 1930 - 15:00:00")
        assert result == datetime(1930, 7, 13, 15, 0, 0)

    def test_iso_format(self):
        result = parse_datetime_csv("1930-07-13 15:00:00")
        assert result == datetime(1930, 7, 13, 15, 0, 0)

    def test_iso_t_format(self):
        result = parse_datetime_csv("1930-07-13T15:00:00")
        assert result == datetime(1930, 7, 13, 15, 0, 0)

    def test_none_returns_none(self):
        assert parse_datetime_csv(None) is None

    def test_empty_returns_none(self):
        assert parse_datetime_csv("") is None

    def test_whitespace_returns_none(self):
        assert parse_datetime_csv("  ") is None

    def test_invalid_returns_none(self):
        assert parse_datetime_csv("not a date") is None

    def test_strips_whitespace(self):
        result = parse_datetime_csv("  13 Jul 1930 - 15:00  ")
        assert result == datetime(1930, 7, 13, 15, 0)


# ═══════════════════════════════════════════════════════════════
# normalize_text
# ═══════════════════════════════════════════════════════════════


class TestNormalizeText:
    def test_strips_whitespace(self):
        assert normalize_text("  hello  ") == "hello"

    def test_truncates_to_max_length(self):
        assert normalize_text("hello world", max_length=5) == "hello"

    def test_no_truncation_if_none(self):
        assert normalize_text("hello world") == "hello world"

    def test_none_returns_none(self):
        assert normalize_text(None) is None

    def test_empty_after_strip_returns_none(self):
        assert normalize_text("   ") is None

    def test_empty_string_returns_none(self):
        assert normalize_text("") is None

    def test_truncation_keeps_correct_chars(self):
        assert normalize_text("abcdefgh", max_length=3) == "abc"


# ═══════════════════════════════════════════════════════════════
# normalize_team_names
# ═══════════════════════════════════════════════════════════════


class TestNormalizeTeamNames:
    def test_title_case(self):
        assert normalize_team_names("  germany fr  ") == "Germany Fr"

    def test_already_clean(self):
        assert normalize_team_names("Brazil") == "Brazil"

    def test_lowercase_input(self):
        assert normalize_team_names("england") == "England"

    def test_uppercase_input(self):
        assert normalize_team_names("FRANCE") == "France"

    def test_none_returns_none(self):
        assert normalize_team_names(None) is None

    def test_empty_returns_none(self):
        assert normalize_team_names("") is None

    def test_whitespace_returns_none(self):
        assert normalize_team_names("  ") is None


# ═══════════════════════════════════════════════════════════════
# normalize_initials
# ═══════════════════════════════════════════════════════════════


class TestNormalizeInitials:
    def test_uppercases_and_strips(self):
        assert normalize_initials(" fra ") == "FRA"

    def test_already_uppercase(self):
        assert normalize_initials("BRA") == "BRA"

    def test_two_letter(self):
        assert normalize_initials("us") == "US"

    def test_none_returns_none(self):
        assert normalize_initials(None) is None

    def test_empty_returns_none(self):
        assert normalize_initials("") is None

    def test_too_long_returns_none(self):
        assert normalize_initials("ABCD") is None

    def test_whitespace_returns_none(self):
        assert normalize_initials("   ") is None


# ═══════════════════════════════════════════════════════════════
# normalized_event_football_players_code
# ═══════════════════════════════════════════════════════════════


class TestNormalizedEventCode:
    def test_uppercases(self):
        assert normalized_event_football_players_code("g") == "G"

    def test_preserves_suffix(self):
        assert normalized_event_football_players_code("G40") == "G40"

    def test_with_plus(self):
        assert normalized_event_football_players_code("G45+1") == "G45+1"

    def test_own_goal(self):
        assert normalized_event_football_players_code("og") == "OG"

    def test_none_returns_none(self):
        assert normalized_event_football_players_code(None) is None

    def test_empty_after_strip_returns_empty(self):
        assert normalized_event_football_players_code("  ") == ""


# ═══════════════════════════════════════════════════════════════
# normalized_lineup_type
# ═══════════════════════════════════════════════════════════════


class TestNormalizedLineupType:
    def test_starter_lowercase(self):
        assert normalized_lineup_type("s") == "S"

    def test_starter_uppercase(self):
        assert normalized_lineup_type("S") == "S"

    def test_non_starter(self):
        assert normalized_lineup_type("N") == "N"

    def test_invalid_returns_none(self):
        assert normalized_lineup_type("X") is None

    def test_none_returns_none(self):
        assert normalized_lineup_type(None) is None

    def test_empty_returns_none(self):
        assert normalized_lineup_type("") is None


# ═══════════════════════════════════════════════════════════════
# normalize_player_position
# ═══════════════════════════════════════════════════════════════


class TestNormalizePlayerPosition:
    def test_gk_lowercase(self):
        assert normalize_player_position("gk") == "GK"

    def test_df(self):
        assert normalize_player_position("DF") == "DF"

    def test_mf(self):
        assert normalize_player_position("mf") == "MF"

    def test_fw(self):
        assert normalize_player_position("FW") == "FW"

    def test_captain_not_valid(self):
        assert normalize_player_position("C") is None

    def test_none_returns_none(self):
        assert normalize_player_position(None) is None

    def test_empty_returns_none(self):
        assert normalize_player_position("") is None

    def test_invalid_returns_none(self):
        assert normalize_player_position("XYZ") is None


# ═══════════════════════════════════════════════════════════════
# slugify
# ═══════════════════════════════════════════════════════════════


class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars_removed(self):
        assert slugify("Hello! World?") == "hello-world"

    def test_multiple_spaces(self):
        assert slugify("hello   world") == "hello-world"

    def test_leading_trailing_dashes(self):
        assert slugify("  hello world  ") == "hello-world"

    def test_already_slug(self):
        assert slugify("hello-world") == "hello-world"


# ═══════════════════════════════════════════════════════════════
# now_utc
# ═══════════════════════════════════════════════════════════════


class TestNowUtc:
    def test_returns_datetime(self):
        assert isinstance(now_utc(), datetime)

    def test_is_utc(self):
        assert now_utc().tzinfo is UTC


# ═══════════════════════════════════════════════════════════════
# format_s3_key
# ═══════════════════════════════════════════════════════════════


class TestFormatS3Key:
    def test_format_with_custom_ts(self):
        ts = datetime(2024, 1, 15, 14, 30, 22, tzinfo=UTC)
        result = format_s3_key("products", "data.csv", ts=ts)
        assert result == "products/20240115_143022_data.csv"

    def test_uses_now_when_no_ts(self):
        result = format_s3_key("raw", "file.csv")
        assert result.startswith("raw/")
        assert result.endswith("_file.csv")


# ═══════════════════════════════════════════════════════════════
# clean_cell
# ═══════════════════════════════════════════════════════════════


class TestCleanCell:
    def test_none_returns_none(self):
        assert clean_cell(None) is None

    def test_empty_string_returns_none(self):
        assert clean_cell("") is None

    def test_whitespace_returns_none(self):
        assert clean_cell("   ") is None

    def test_nan_string_returns_none(self):
        assert clean_cell("nan") is None

    def test_none_string_returns_none(self):
        assert clean_cell("None") is None

    def test_null_string_returns_none(self):
        assert clean_cell("null") is None

    def test_na_string_returns_none(self):
        assert clean_cell("n/a") is None

    def test_na_without_slash_returns_none(self):
        assert clean_cell("na") is None

    def test_valid_string_returned(self):
        assert clean_cell("hello") == "hello"

    def test_strips_whitespace(self):
        assert clean_cell("  hello  ") == "hello"

    def test_mixed_case_nan_returns_none(self):
        assert clean_cell("NaN") is None

    def test_integer_value(self):
        assert clean_cell(42) == "42"
