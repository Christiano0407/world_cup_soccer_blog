from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import (
    CurrentUser,
    _get_current_user,
    get_refresh_token_from_cookies,
    require_admin,
    require_editor_or_admin,
    require_roles,
)
from app.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        JWT_SECRET_KEY="test-secret-key-which-is-at-least-32-characters!!",
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test",
        REDIS_URL="redis://localhost:6379/0",
    )


@pytest.fixture
def valid_access_token(settings: Settings) -> str:
    from app.core.security import create_access_token
    return create_access_token("user-123", "admin", settings)


@pytest.fixture
def valid_refresh_token(settings: Settings) -> str:
    from app.core.security import create_refresh_token
    return create_refresh_token("user-123", settings)


class TestGetCurrentUser:
    def test_valid_token_returns_current_user(self, settings: Settings, valid_access_token: str) -> None:
        credentials = MagicMock()
        credentials.credentials = valid_access_token
        user = _get_current_user(credentials=credentials, settings=settings)
        assert isinstance(user, CurrentUser)
        assert user.user_id == "user-123"
        assert user.role == "admin"

    def test_no_credentials_raises(self, settings: Settings) -> None:
        with pytest.raises(AuthenticationError, match="Credenciales Inválidas"):
            _get_current_user(credentials=None, settings=settings)

    def test_refresh_token_rejected(self, settings: Settings, valid_refresh_token: str) -> None:
        credentials = MagicMock()
        credentials.credentials = valid_refresh_token
        with pytest.raises(AuthenticationError, match="Token Inválido"):
            _get_current_user(credentials=credentials, settings=settings)

    def test_expired_token_raises(self, settings: Settings) -> None:
        import time
        from jose import jws
        payload = {"sub": "user-1", "kind": "access", "role": "reader", "iat": int(time.time()) - 3600, "exp": int(time.time()) - 60, "jti": "test-jti"}
        token = jws.sign(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        credentials = MagicMock()
        credentials.credentials = token
        with pytest.raises(AuthenticationError):
            _get_current_user(credentials=credentials, settings=settings)


class TestRequireRoles:
    def test_admin_role_allowed(self) -> None:
        dep = require_roles("admin")
        user = CurrentUser(user_id="1", role="admin")
        result = dep(user=user)
        assert result is user

    def test_editor_role_allowed(self) -> None:
        dep = require_roles("editor")
        user = CurrentUser(user_id="1", role="editor")
        result = dep(user=user)
        assert result is user

    def test_reader_rejected_for_admin(self) -> None:
        dep = require_roles("admin")
        user = CurrentUser(user_id="1", role="reader")
        with pytest.raises(AuthorizationError, match="Acceso denegado"):
            dep(user=user)

    def test_multiple_roles_allows_any(self) -> None:
        dep = require_roles("admin", "editor")
        user = CurrentUser(user_id="1", role="editor")
        result = dep(user=user)
        assert result is user

    def test_empty_roles_rejects_all(self) -> None:
        dep = require_roles()
        user = CurrentUser(user_id="1", role="admin")
        with pytest.raises(AuthorizationError):
            dep(user=user)


class TestRequireAdmin:
    def test_admin_allowed(self) -> None:
        user = CurrentUser(user_id="1", role="admin")
        result = require_admin(user=user)
        assert result is user

    def test_editor_rejected(self) -> None:
        user = CurrentUser(user_id="1", role="editor")
        with pytest.raises(AuthorizationError):
            require_admin(user=user)

    def test_reader_rejected(self) -> None:
        user = CurrentUser(user_id="1", role="reader")
        with pytest.raises(AuthorizationError):
            require_admin(user=user)


class TestRequireEditorOrAdmin:
    def test_admin_allowed(self) -> None:
        user = CurrentUser(user_id="1", role="admin")
        result = require_editor_or_admin(user=user)
        assert result is user

    def test_editor_allowed(self) -> None:
        user = CurrentUser(user_id="1", role="editor")
        result = require_editor_or_admin(user=user)
        assert result is user

    def test_reader_rejected(self) -> None:
        user = CurrentUser(user_id="1", role="reader")
        with pytest.raises(AuthorizationError):
            require_editor_or_admin(user=user)


class TestGetRefreshTokenFromCookies:
    def test_valid_refresh_token_returns_payload(self, settings: Settings, valid_refresh_token: str) -> None:
        payload = get_refresh_token_from_cookies(refresh_token=valid_refresh_token, settings=settings)
        assert payload["sub"] == "user-123"
        assert payload["kind"] == "refresh"

    def test_no_cookie_raises(self, settings: Settings) -> None:
        with pytest.raises(AuthenticationError, match="Refresh Token Ausente"):
            get_refresh_token_from_cookies(refresh_token=None, settings=settings)

    def test_access_token_rejected_as_refresh(self, settings: Settings, valid_access_token: str) -> None:
        with pytest.raises(AuthenticationError, match="Token Inválido"):
            get_refresh_token_from_cookies(refresh_token=valid_access_token, settings=settings)
