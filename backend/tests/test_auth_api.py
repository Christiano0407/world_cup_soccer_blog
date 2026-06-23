from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.endpoints.deps import get_auth_service, get_team_service
from app.core.security import CurrentUser, get_current_user
from tests.mocks import MockAuthService, MockTeamService


@pytest.fixture
def app() -> FastAPI:
    from app.main import create_app
    return create_app()


@pytest.fixture
def mock_auth_service() -> MockAuthService:
    return MockAuthService()


@pytest.fixture
def current_user() -> CurrentUser:
    return CurrentUser(user_id="test-user-id", role="admin")


@pytest.fixture
def client(app: FastAPI, mock_auth_service: MockAuthService, current_user: CurrentUser) -> AsyncClient:
    async def _override_auth() -> MockAuthService:
        return mock_auth_service

    async def _override_user() -> CurrentUser:
        return current_user

    app.dependency_overrides[get_auth_service] = _override_auth
    app.dependency_overrides[get_current_user] = _override_user
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def valid_register_payload() -> dict:
    return {
        "email": "new@fifa.com",
        "password": "Str0ngP4ssword!",
        "display_name": "New Player",
    }


class TestRegisterEndpoint:
    async def test_register_returns_201_and_token(self, client: AsyncClient, valid_register_payload: dict) -> None:
        response = await client.post("/api/v1/auth/register", json=valid_register_payload)
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] == "mock_at_register"
        assert "expires_in" in data

    async def test_register_returns_token_type_bearer(self, client: AsyncClient, valid_register_payload: dict) -> None:
        response = await client.post("/api/v1/auth/register", json=valid_register_payload)
        assert response.json().get("token_type") == "bearer"

    async def test_register_invalid_email_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "Str0ngP4ssword!",
            "display_name": "Bad",
        })
        assert response.status_code == 422

    async def test_register_short_password_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@fifa.com",
            "password": "123",
            "display_name": "Bad",
        })
        assert response.status_code == 422


class TestLoginEndpoint:
    async def test_login_returns_200_and_token(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/login", json={
            "email": "cr7@example.com",
            "password": "Str0ngP4ssword!",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_login_missing_fields_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/login", json={"email": "test@fifa.com"})
        assert response.status_code == 422


class TestRefreshEndpoint:
    async def test_refresh_without_cookie_returns_401(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/refresh")
        assert response.status_code == 401


class TestLogoutEndpoint:
    async def test_logout_returns_204(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 204


class TestGetMeEndpoint:
    async def test_get_me_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "display_name" in data


class TestUpdateMeEndpoint:
    async def test_patch_me_returns_200(self, client: AsyncClient) -> None:
        response = await client.patch("/api/v1/auth/me", json={"display_name": "Messi"})
        assert response.status_code == 200
        data = response.json()
        assert data.get("display_name") == "Messi"

    async def test_patch_me_without_body_returns_200(self, client: AsyncClient) -> None:
        response = await client.patch("/api/v1/auth/me", json={})
        assert response.status_code == 200


class TestChangePasswordEndpoint:
    async def test_change_password_returns_204(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/change-password", json={
            "current_password": "OldP4ss",
            "new_password": "NewP4ssWord!",
        })
        assert response.status_code == 204

    async def test_change_password_missing_fields_returns_422(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/change-password", json={})
        assert response.status_code == 422
