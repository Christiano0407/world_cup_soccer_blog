from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.v1.endpoints.deps import (
    get_admin_service,
    get_auth_service,
    get_match_service,
    get_player_service,
    get_team_service,
    get_tournament_service,
)
from app.core.security import get_current_user
from tests.mocks import (
    MockAdminService,
    MockAuthService,
    MockMatchService,
    MockPlayerService,
    MockTeamService,
    MockTournamentService,
)


@pytest.fixture
def app() -> FastAPI:
    from app.main import create_app
    return create_app()


@pytest.fixture
def current_user():
    from app.core.security import CurrentUser
    return CurrentUser(user_id="admin-id", role="admin")


@pytest.fixture
def client(app: FastAPI, current_user) -> AsyncClient:
    async def _override_user():
        return current_user

    app.dependency_overrides[get_auth_service] = lambda: MockAuthService()
    app.dependency_overrides[get_team_service] = lambda: MockTeamService()
    app.dependency_overrides[get_tournament_service] = lambda: MockTournamentService()
    app.dependency_overrides[get_match_service] = lambda: MockMatchService()
    app.dependency_overrides[get_player_service] = lambda: MockPlayerService()
    app.dependency_overrides[get_admin_service] = lambda: MockAdminService()
    app.dependency_overrides[get_current_user] = _override_user
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestHealthEndpoint:
    async def test_health_returns_200(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        assert response.status_code == 200

    async def test_health_returns_json(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        assert response.headers.get("content-type", "").startswith("application/json")

    async def test_health_has_status_key(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        assert "status" in response.json()


class TestAuthStatusCodes:
    async def test_register_returns_201(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/register", json={
            "email": "a@b.com", "password": "Str0ngP4ss!", "display_name": "A",
        })
        assert resp.status_code == 201

    async def test_login_returns_200(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/login", json={
            "email": "a@b.com", "password": "Str0ngP4ss!",
        })
        assert resp.status_code == 200

    async def test_logout_returns_204(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 204

    async def test_change_password_returns_204(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/change-password", json={
            "current_password": "Old1",
            "new_password": "NewP4ss!",
        })
        assert resp.status_code == 204

    async def test_refresh_without_cookie_returns_401(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401


class TestMethodNotAllowed:
    async def test_unknown_endpoint_returns_404(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/nonexistent")
        assert resp.status_code == 404

    async def test_unknown_route_returns_json_error(self, client: AsyncClient) -> None:
        resp = await client.get("/this-does-not-exist")
        assert resp.status_code == 404
        assert "detail" in resp.json()


class TestContentTypeValidation:
    async def test_missing_required_fields_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/register", json={"email": "a@b.com"})
        assert resp.status_code == 422

    async def test_invalid_email_format_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/register", json={
            "email": "invalid", "password": "Str0ngP4ss!", "display_name": "X",
        })
        assert resp.status_code == 422


class TestTeamEndpointsStatusCodes:
    async def test_list_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/teams/")
        assert resp.status_code == 200

    async def test_get_team_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/teams/ARG")
        assert resp.status_code == 200

    async def test_ranking_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/teams/ranking")
        assert resp.status_code == 200

    async def test_head_to_head_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/teams/ARG/head-to-head/FRA")
        assert resp.status_code == 200

    async def test_team_matches_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/teams/ARG/matches")
        assert resp.status_code == 200


class TestTournamentEndpointsStatusCodes:
    async def test_list_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/tournaments/")
        assert resp.status_code == 200

    async def test_by_year_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/tournaments/2022")
        assert resp.status_code == 200

    async def test_top_scorers_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/tournaments/2022/top-scorers")
        assert resp.status_code == 200

    async def test_matches_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/tournaments/2022/matches")
        assert resp.status_code == 200

    async def test_teams_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/tournaments/2022/teams")
        assert resp.status_code == 200


class TestMatchEndpointsStatusCodes:
    async def test_list_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/matches/")
        assert resp.status_code == 200

    async def test_by_id_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/matches/1")
        assert resp.status_code == 200

    async def test_search_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/matches/search", params={"q": "Final"})
        assert resp.status_code == 200

    async def test_players_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/matches/1/players")
        assert resp.status_code == 200


class TestPlayerEndpointsStatusCodes:
    async def test_list_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/players/")
        assert resp.status_code == 200

    async def test_search_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/players/search", params={"q": "Messi"})
        assert resp.status_code == 200

    async def test_top_scorers_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/players/top-scorers")
        assert resp.status_code == 200


class TestAdminEndpointsStatusCodes:
    async def test_users_list_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/admin/users")
        assert resp.status_code == 200

    async def test_dead_letters_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/admin/etl/dead-letter")
        assert resp.status_code == 200

    async def test_audit_log_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/admin/audit-log")
        assert resp.status_code == 200

    async def test_refresh_warehouse_returns_202(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/admin/warehouse/refresh")
        assert resp.status_code == 202


class TestNegativeScenarios:
    async def test_empty_body_post_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            content=b"",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 422
