from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.schemas import (
    AdminUserOut,
    AdminUserUpdate,
    ChangePasswordIn,
    LoginIn,
    RegisterIn,
    TeamIn,
    TeamUpdate,
    TournamentIn,
    TournamentUpdate,
    UserOut,
    UserUpdateIn,
)


class TestRegisterIn:
    def test_valid_registration(self) -> None:
        data = RegisterIn(email="user@example.com", password="SecurePass1", display_name="User")
        assert data.email == "user@example.com"
        assert data.display_name == "User"

    def test_password_without_digit_raises(self) -> None:
        with pytest.raises(ValidationError, match="(?i)dígito"):
            RegisterIn(email="user@example.com", password="NoDigitPass")

    def test_password_too_short_raises(self) -> None:
        with pytest.raises(ValidationError, match="at least 8"):
            RegisterIn(email="user@example.com", password="Sh0rt")

    def test_invalid_email_raises(self) -> None:
        with pytest.raises(ValidationError):
            RegisterIn(email="not-an-email", password="ValidP4ssword")

    def test_display_name_optional(self) -> None:
        data = RegisterIn(email="user@example.com", password="ValidP4ssword")
        assert data.display_name is None

    def test_display_name_max_length(self) -> None:
        long_name = "A" * 81
        with pytest.raises(ValidationError, match="at most 80"):
            RegisterIn(email="user@example.com", password="ValidP4ssword", display_name=long_name)


class TestLoginIn:
    def test_valid_login(self) -> None:
        data = LoginIn(email="test@example.com", password="mypassword")
        assert data.email == "test@example.com"

    def test_invalid_email_format(self) -> None:
        with pytest.raises(ValidationError):
            LoginIn(email="bad-email", password="pass")

    def test_empty_password_allowed(self) -> None:
        data = LoginIn(email="test@example.com", password="")
        assert data.password == ""


class TestChangePasswordIn:
    def test_valid_change(self) -> None:
        data = ChangePasswordIn(current_password="OldPass1", new_password="NewPass1")
        assert data.current_password == "OldPass1"

    def test_new_password_too_short(self) -> None:
        with pytest.raises(ValidationError, match="at least 8"):
            ChangePasswordIn(current_password="Old", new_password="Sh0rt")

    def test_new_password_without_digit(self) -> None:
        data = ChangePasswordIn(current_password="Old", new_password="NoDigitPass")
        assert data.new_password == "NoDigitPass"

    def test_new_password_max_length(self) -> None:
        long_pw = "A" * 129
        with pytest.raises(ValidationError, match="at most 128"):
            ChangePasswordIn(current_password="Old", new_password=long_pw)


class TestUserOut:
    def test_valid_user_out(self) -> None:
        now = datetime.now(UTC)
        data = UserOut(
            user_id=uuid.uuid4(),
            email="user@example.com",
            display_name="Test User",
            role="reader",
            is_active=True,
            created_at=now,
            update_at=now,
        )
        assert data.role == "reader"

    def test_invalid_role_raises(self) -> None:
        now = datetime.now(UTC)
        with pytest.raises(ValidationError):
            UserOut(
                user_id=uuid.uuid4(),
                email="user@example.com",
                role="superadmin",
                is_active=True,
                created_at=now,
                update_at=now,
            )

    def test_from_attributes(self) -> None:
        now = datetime.now(UTC)
        orm_obj = type("MockUser", (), {
            "user_id": uuid.uuid4(),
            "email": "orm@example.com",
            "display_name": "ORM User",
            "role": "editor",
            "is_active": True,
            "created_at": now,
            "update_at": now,
        })()
        user = UserOut.model_validate(orm_obj)
        assert user.email == "orm@example.com"
        assert user.role == "editor"


class TestAdminUserOut:
    def test_valid_admin_out(self) -> None:
        now = datetime.now(UTC)
        data = AdminUserOut(
            user_id=uuid.uuid4(),
            email="admin@fifa.com",
            display_name="Admin",
            role="admin",
            is_active=True,
            created_at=now,
            update_at=now,
        )
        assert data.role == "admin"

    def test_invalid_role_raises(self) -> None:
        now = datetime.now(UTC)
        with pytest.raises(ValidationError):
            AdminUserOut(
                user_id=uuid.uuid4(),
                email="admin@fifa.com",
                role="superadmin",
                is_active=True,
                created_at=now,
                update_at=now,
            )


class TestAdminUserUpdate:
    def test_valid_update(self) -> None:
        data = AdminUserUpdate(role="editor")
        assert data.role == "editor"

    def test_invalid_role_raises(self) -> None:
        with pytest.raises(ValidationError):
            AdminUserUpdate(role="superadmin")

    def test_is_active_optional(self) -> None:
        data = AdminUserUpdate(role="reader")
        assert data.is_active is None


class TestTeamIn:
    def test_valid_team(self) -> None:
        data = TeamIn(initials="ARG", name="Argentina")
        assert data.initials == "ARG"

    def test_initials_too_long(self) -> None:
        with pytest.raises(ValidationError, match="at most 3"):
            TeamIn(initials="ARGT", name="Test")

    def test_initials_too_short(self) -> None:
        with pytest.raises(ValidationError, match="at least 2"):
            TeamIn(initials="A", name="Test")

    def test_active_default_true(self) -> None:
        data = TeamIn(initials="BRA", name="Brazil")
        assert data.active is True


class TestTeamUpdate:
    def test_all_fields_optional(self) -> None:
        data = TeamUpdate()
        assert data.model_dump(exclude_none=True) == {}

    def test_partial_update(self) -> None:
        data = TeamUpdate(name="New Name")
        dumped = data.model_dump(exclude_none=True)
        assert "name" in dumped
        assert "active" not in dumped


class TestTournamentIn:
    def test_valid_tournament(self) -> None:
        data = TournamentIn(
            year=2022, host_country="Qatar", winner="Argentina",
            runners_up="France", goals_scored=100, qualified_teams=32, matches_played=64,
        )
        assert data.year == 2022

    def test_year_below_minimum(self) -> None:
        with pytest.raises(ValidationError):
            TournamentIn(
                year=1800, host_country="Test", winner="A",
                runners_up="B", goals_scored=10, qualified_teams=16, matches_played=32,
            )

    def test_year_above_maximum(self) -> None:
        with pytest.raises(ValidationError):
            TournamentIn(
                year=2100, host_country="Test", winner="A",
                runners_up="B", goals_scored=10, qualified_teams=16, matches_played=32,
            )

    def test_goals_scored_negative(self) -> None:
        with pytest.raises(ValidationError):
            TournamentIn(
                year=2022, host_country="Qatar", winner="A",
                runners_up="B", goals_scored=-1, qualified_teams=16, matches_played=32,
            )


class TestTournamentUpdate:
    def test_all_fields_optional(self) -> None:
        data = TournamentUpdate()
        assert data.model_dump(exclude_none=True) == {}

    def test_partial(self) -> None:
        data = TournamentUpdate(winner="New Winner")
        assert data.winner == "New Winner"
        assert data.runners_up is None


class TestUserUpdateIn:
    def test_valid_update(self) -> None:
        data = UserUpdateIn(display_name="New Name")
        assert data.display_name == "New Name"

    def test_empty_update(self) -> None:
        data = UserUpdateIn()
        assert data.display_name is None

    def test_display_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            UserUpdateIn(display_name="A" * 81)
