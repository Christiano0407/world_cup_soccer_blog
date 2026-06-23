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


class TestAuthFlow:
    async def test_register_and_login(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/register", json={
            "email": "user@fifa.com", "password": "Str0ngP4ss!", "display_name": "User",
        })
        assert resp.status_code == 201

        resp = await client.post("/api/v1/auth/login", json={
            "email": "user@fifa.com", "password": "Str0ngP4ss!",
        })
        assert resp.status_code == 200

    async def test_me_and_update(self, client: AsyncClient) -> None:
        me = await client.get("/api/v1/auth/me")
        assert me.status_code == 200

        upd = await client.patch("/api/v1/auth/me", json={"display_name": "Updated"})
        assert upd.status_code == 200

    async def test_logout(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/logout")
        assert resp.status_code == 204

    async def test_change_password(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/auth/change-password", json={
            "current_password": "Old1", "new_password": "NewP4ss!",
        })
        assert resp.status_code == 204


class TestTeamsFlow:
    async def test_list_teams(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/teams/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_team(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/teams/ARG")
        assert resp.status_code == 200

    async def test_ranking(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/teams/ranking")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_head_to_head(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/teams/ARG/head-to-head/FRA")
        assert resp.status_code == 200

    async def test_team_matches(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/teams/ARG/matches")
        assert resp.status_code == 200
        assert "items" in resp.json()


class TestTournamentsFlow:
    async def test_list_tournaments(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/tournaments/")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data

    async def test_get_tournament(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/tournaments/2022")
        assert resp.status_code == 200
        assert resp.json().get("year") == 2022

    async def test_top_scorers(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/tournaments/2022/top-scorers")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestMatchesFlow:
    async def test_list_matches(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/matches/")
        assert resp.status_code == 200
        assert "items" in resp.json()

    async def test_search_matches(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/matches/search", params={"q": "Final"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_match(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/matches/1")
        assert resp.status_code == 200
        assert resp.json().get("match_id") == 1

    async def test_match_players(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/matches/1/players")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestPlayersFlow:
    async def test_list_players(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/players/")
        assert resp.status_code == 200
        assert "items" in resp.json()

    async def test_search_players(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/players/search", params={"q": "Messi"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestAdminFlow:
    async def test_list_users(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/admin/users")
        assert resp.status_code == 200
        assert "items" in resp.json()

    async def test_dead_letters(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/admin/etl/dead-letter")
        assert resp.status_code == 200

    async def test_trigger_etl(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/admin/etl/trigger", json={"dataset": "winners"})
        assert resp.status_code == 202

    async def test_refresh_warehouse(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/admin/warehouse/refresh")
        assert resp.status_code == 202

    async def test_audit_log(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/admin/audit-log")
        assert resp.status_code == 200
