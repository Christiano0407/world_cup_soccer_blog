from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from jose import JWTError, jwt

from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        JWT_SECRET_KEY="test-secret-key-which-is-at-least-32-characters!!",
        JWT_ALGORITHM="HS256",
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30,
        JWT_REFRESH_TOKEN_EXPIRE_DAYS=7,
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test",
        REDIS_URL="redis://localhost:6379/0",
    )


class TestCreateAccessToken:
    def test_creates_valid_access_token(self, settings: Settings) -> None:
        token = create_access_token("user-123", "admin", settings)
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == "user-123"
        assert payload["kind"] == "access"
        assert payload["role"] == "admin"
        assert "jti" in payload
        assert "iat" in payload
        assert "exp" in payload

    def test_expiration_time(self, settings: Settings) -> None:
        before = datetime.now(UTC)
        token = create_access_token("user-1", "reader", settings)
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_min = before + timedelta(minutes=29)
        expected_max = before + timedelta(minutes=31)
        assert expected_min <= exp <= expected_max

    def test_different_tokens_have_different_jti(self, settings: Settings) -> None:
        t1 = create_access_token("user-1", "reader", settings)
        t2 = create_access_token("user-1", "reader", settings)
        payload1 = jwt.decode(t1, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        payload2 = jwt.decode(t2, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload1["jti"] != payload2["jti"]

    def test_reader_role_in_payload(self, settings: Settings) -> None:
        token = create_access_token("user-1", "reader", settings)
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["role"] == "reader"


class TestCreateRefreshToken:
    def test_creates_valid_refresh_token(self, settings: Settings) -> None:
        token = create_refresh_token("user-123", settings)
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == "user-123"
        assert payload["kind"] == "refresh"
        assert "role" not in payload

    def test_refresh_expiration_days(self, settings: Settings) -> None:
        before = datetime.now(UTC)
        token = create_refresh_token("user-1", settings)
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_min = before + timedelta(days=6, hours=23)
        expected_max = before + timedelta(days=7, hours=1)
        assert expected_min <= exp <= expected_max

    def test_refresh_has_no_role_claim(self, settings: Settings) -> None:
        token = create_refresh_token("user-1", settings)
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert "role" not in payload


class TestDecodeToken:
    def test_decode_valid_token(self, settings: Settings) -> None:
        token = create_access_token("user-1", "admin", settings)
        payload = decode_token(token, settings)
        assert payload["sub"] == "user-1"
        assert payload["kind"] == "access"

    def test_decode_expired_token_raises(self, settings: Settings) -> None:
        import time
        from jose import jws
        payload = {"sub": "user-1", "kind": "access", "role": "reader", "iat": int(time.time()) - 3600, "exp": int(time.time()) - 60, "jti": "test-jti"}
        token = jws.sign(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        with pytest.raises(AuthenticationError, match="Credenciales Inválidas"):
            decode_token(token, settings)

    def test_decode_tampered_token_raises(self, settings: Settings) -> None:
        token = create_access_token("user-1", "reader", settings)
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(AuthenticationError, match="Credenciales Inválidas"):
            decode_token(tampered, settings)

    def test_decode_invalid_algorithm_rejected(self, settings: Settings) -> None:
        token = jwt.encode({"sub": "1"}, "wrong-secret", algorithm="HS256")
        with pytest.raises(AuthenticationError, match="Credenciales Inválidas"):
            decode_token(token, settings)

    def test_decode_empty_token_raises(self, settings: Settings) -> None:
        with pytest.raises(AuthenticationError, match="Credenciales Inválidas"):
            decode_token("", settings)


class TestAccessVsRefresh:
    def test_cannot_use_refresh_as_access(self, settings: Settings) -> None:
        refresh = create_refresh_token("user-1", settings)
        payload = decode_token(refresh, settings)
        assert payload["kind"] == "refresh"

    def test_cannot_use_access_as_refresh(self, settings: Settings) -> None:
        access = create_access_token("user-1", "reader", settings)
        payload = decode_token(access, settings)
        assert payload["kind"] == "access"

    def test_different_secret_fails(self, settings: Settings) -> None:
        token = create_access_token("user-1", "admin", settings)
        fake_settings = MagicMock(wraps=settings)
        fake_settings.JWT_SECRET_KEY = "different-secret-that-is-also-32-chars-lon!"
        with pytest.raises(AuthenticationError):
            decode_token(token, fake_settings)
