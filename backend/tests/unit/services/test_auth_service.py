from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Response

from app.core.exceptions import AuthenticationError, ConflictError, BusinessLogicError
from app.schemas.schemas import (
    ChangePasswordIn,
    LoginIn,
    RegisterIn,
    TokenOut,
    UserUpdateIn,
)
from tests.conftest import MockResult


def _make_user(**overrides: object) -> MagicMock:
    user = MagicMock()
    user.user_id = uuid.uuid4()
    user.email = "cr7@example.com"
    user.display_name = "Cristiano"
    user.hashed_password = "$2b$12$LJ3m4ys3Lk"
    user.role = "reader"
    user.is_active = True
    user.created_at = datetime.now(UTC)
    user.update_at = datetime.now(UTC)
    user.refresh_jti = None
    for k, v in overrides.items():
        setattr(user, k, v)
    return user


class TestRegister:
    async def test_register_creates_user(self, auth_service, mock_db, settings) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)
        data = RegisterIn(email="new@example.com", password="SecureP4ss", display_name="New User")
        response = MagicMock(spec=Response)

        result = await auth_service.register(data, response)

        assert isinstance(result, TokenOut)
        assert result.access_token is not None
        assert result.expires_in == settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        mock_db.add.assert_called_once()
        mock_db.flush.assert_awaited_once()

    async def test_register_duplicate_email_raises(self, auth_service, mock_db) -> None:
        existing_user = _make_user()
        mock_db.execute.return_value = MockResult(scalar_one=existing_user)
        data = RegisterIn(email="existing@example.com", password="SecureP4ss", display_name="Dup")

        with pytest.raises(ConflictError, match="ya está registrado"):
            await auth_service.register(data, MagicMock(spec=Response))


class TestLogin:
    async def test_login_success(self, auth_service, mock_db, settings) -> None:
        from app.core.security import hash_password
        user = _make_user(hashed_password=hash_password("MyP4ssword"))
        mock_db.execute.return_value = MockResult(scalar_one=user)
        data = LoginIn(email="cr7@example.com", password="MyP4ssword")

        result = await auth_service.login(data, MagicMock(spec=Response))

        assert isinstance(result, TokenOut)
        assert result.expires_in == settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

    async def test_login_wrong_password(self, auth_service, mock_db) -> None:
        from app.core.security import hash_password
        user = _make_user(hashed_password=hash_password("RealP4ss"))
        mock_db.execute.return_value = MockResult(scalar_one=user)
        data = LoginIn(email="cr7@example.com", password="WrongP4ss")

        with pytest.raises(AuthenticationError, match="Credenciales Inválidas"):
            await auth_service.login(data, MagicMock(spec=Response))

    async def test_login_user_not_found(self, auth_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)
        data = LoginIn(email="ghost@example.com", password="SomeP4ss")

        with pytest.raises(AuthenticationError, match="Credenciales Inválidas"):
            await auth_service.login(data, MagicMock(spec=Response))

    async def test_login_inactive_user(self, auth_service, mock_db) -> None:
        from app.core.security import hash_password
        user = _make_user(hashed_password=hash_password("ActiveP4ss"), is_active=False)
        mock_db.execute.return_value = MockResult(scalar_one=user)
        data = LoginIn(email="inactive@example.com", password="ActiveP4ss")

        with pytest.raises(AuthenticationError, match="Cuenta Desactivada"):
            await auth_service.login(data, MagicMock(spec=Response))


class TestRefresh:
    async def test_refresh_success(self, auth_service, mock_db, mock_redis) -> None:
        user_id = str(uuid.uuid4())
        mock_db.execute.return_value = MockResult(scalar_one=_make_user())
        payload = {"sub": user_id, "jti": str(uuid.uuid4()), "kind": "refresh"}

        result = await auth_service.refresh(payload, MagicMock(spec=Response))

        assert isinstance(result, TokenOut)
        mock_redis.setex.assert_awaited_once()
        assert mock_redis.setex.await_args[0][0].startswith("revoked_refresh:")

    async def test_refresh_revoked_token(self, auth_service, mock_redis) -> None:
        mock_redis.get = AsyncMock(return_value="1")
        payload = {"sub": str(uuid.uuid4()), "jti": str(uuid.uuid4()), "kind": "refresh"}

        with pytest.raises(AuthenticationError, match="Refresh Token Revocado"):
            await auth_service.refresh(payload, MagicMock(spec=Response))

    async def test_refresh_inactive_user(self, auth_service, mock_db, mock_redis) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=_make_user(is_active=False))
        payload = {"sub": str(uuid.uuid4()), "jti": str(uuid.uuid4()), "kind": "refresh"}

        with pytest.raises(AuthenticationError, match="Cuenta Inactiva"):
            await auth_service.refresh(payload, MagicMock(spec=Response))


class TestLogout:
    async def test_logout_with_jti(self, auth_service, mock_redis) -> None:
        response = MagicMock(spec=Response)
        user_id = str(uuid.uuid4())

        await auth_service.logout(user_id, "some-jti", response)

        mock_redis.setex.assert_awaited_once()
        response.delete_cookie.assert_called_once()

    async def test_logout_without_jti(self, auth_service, mock_redis) -> None:
        response = MagicMock(spec=Response)
        user_id = str(uuid.uuid4())

        await auth_service.logout(user_id, None, response)

        mock_redis.setex.assert_not_called()
        response.delete_cookie.assert_called_once()


class TestGetMe:
    async def test_get_me_returns_user(self, auth_service, mock_db) -> None:
        user = _make_user()
        mock_db.execute.return_value = MockResult(scalar_one=user)

        result = await auth_service.get_me(str(uuid.uuid4()))

        assert result.email == "cr7@example.com"
        assert result.display_name == "Cristiano"

    async def test_get_me_user_not_found(self, auth_service, mock_db) -> None:
        mock_db.execute.return_value = MockResult(scalar_one=None)

        with pytest.raises(AuthenticationError, match="Usuario No encontrado"):
            await auth_service.get_me(str(uuid.uuid4()))


class TestUpdateMe:
    async def test_update_display_name(self, auth_service, mock_db) -> None:
        user = _make_user()
        mock_db.execute.return_value = MockResult(scalar_one=user)
        data = UserUpdateIn(display_name="New Name")

        result = await auth_service.update_me(str(uuid.uuid4()), data)

        assert result.display_name == "New Name"

    async def test_update_no_changes(self, auth_service, mock_db) -> None:
        user = _make_user()
        mock_db.execute.return_value = MockResult(scalar_one=user)
        data = UserUpdateIn()

        result = await auth_service.update_me(str(uuid.uuid4()), data)

        assert result.display_name == "Cristiano"


class TestChangePassword:
    async def test_change_password_success(self, auth_service, mock_db) -> None:
        from app.core.security import hash_password
        user = _make_user(hashed_password=hash_password("OldP4ss"))
        mock_db.execute.return_value = MockResult(scalar_one=user)
        data = ChangePasswordIn(current_password="OldP4ss", new_password="NewP4ssWord")

        await auth_service.change_password(str(uuid.uuid4()), data)

        assert user.hashed_password != hash_password("OldP4ss")

    async def test_change_password_wrong_current(self, auth_service, mock_db) -> None:
        from app.core.security import hash_password
        user = _make_user(hashed_password=hash_password("RealP4ss"))
        mock_db.execute.return_value = MockResult(scalar_one=user)
        data = ChangePasswordIn(current_password="WrongP4ss", new_password="NewP4ssWord")

        with pytest.raises(BusinessLogicError, match="Contraseña"):
            await auth_service.change_password(str(uuid.uuid4()), data)
