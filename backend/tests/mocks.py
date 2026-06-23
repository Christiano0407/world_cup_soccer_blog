from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import Response

from app.schemas.schemas import (
    AdminUserOut,
    ChangePasswordIn,
    DeadLetterOut,
    EtlStatusOut,
    EtlTriggerIn,
    HeadToHeadOut,
    LoginIn,
    MatchListOut,
    MatchOut,
    Paginated,
    PlayerAppearanceOut,
    PlayerCareerOut,
    RegisterIn,
    TeamIn,
    TeamOut,
    TeamStatsOut,
    TeamUpdate,
    TokenOut,
    TopScorerOut,
    TournamentIn,
    TournamentListOut,
    TournamentOut,
    TournamentUpdate,
    UserOut,
    UserUpdateIn,
)
from tests.factories import (
    AdminUserOutFactory,
    HeadToHeadOutFactory,
    MatchListOutFactory,
    MatchOutFactory,
    PlayerAppearanceOutFactory,
    PlayerCareerOutFactory,
    TeamOutFactory,
    TeamStatsOutFactory,
    TopScorerOutFactory,
    TournamentListOutFactory,
    TournamentOutFactory,
    UserOutFactory,
    build_paginated,
)


class MockAuthService:
    async def register(self, data: RegisterIn, response: Response) -> TokenOut:
        return TokenOut(access_token="mock_at_register", expires_in=1800)

    async def login(self, data: LoginIn, response: Response) -> TokenOut:
        return TokenOut(access_token="mock_at_login", expires_in=1800)

    async def refresh(self, payload: dict, response: Response) -> TokenOut:
        return TokenOut(access_token="mock_at_refresh", expires_in=1800)

    async def logout(self, user_id: str, bearer_jti: str | None, response: Response) -> None:
        return None

    async def get_me(self, user_id: str) -> UserOut:
        return UserOutFactory()

    async def update_me(self, user_id: str, data: UserUpdateIn) -> UserOut:
        return UserOutFactory(display_name=data.display_name or "Updated")

    async def change_password(self, user_id: str, data: ChangePasswordIn) -> None:
        return None


class MockTeamService:
    async def list_teams(self, active: bool | None = None, confederation: str | None = None) -> list[TeamOut]:
        return TeamOutFactory.build_batch(3)

    async def get_team_stats(self, initials: str) -> TeamStatsOut:
        return TeamStatsOutFactory(initials=initials)

    async def get_ranking(self, sort_by: str = "titles", min_matches: int = 3) -> list[TeamStatsOut]:
        return TeamStatsOutFactory.build_batch(5)

    async def create_team(self, data: TeamIn) -> TeamOut:
        return TeamOutFactory(initials=data.initials, name=data.name)

    async def update_team(self, initials: str, data: TeamUpdate) -> TeamOut:
        return TeamOutFactory(initials=initials, name=data.name or "Updated")

    async def get_matches(self, initials: str, page: int = 1, page_size: int = 20, year: int | None = None, stage: str | None = None) -> Paginated[MatchListOut]:
        items = MatchListOutFactory.build_batch(2)
        return build_paginated(items, page=page, page_size=page_size)

    async def head_to_head(self, initials_a: str, initials_b: str) -> HeadToHeadOut:
        return HeadToHeadOutFactory(team_a=initials_a, team_b=initials_b)


class MockTournamentService:
    async def list_tournaments(self, page: int = 1, page_size: int = 20, year_from: int | None = None, year_to: int | None = None) -> Paginated[TournamentListOut]:
        items = TournamentListOutFactory.build_batch(3)
        return build_paginated(items, page=page, page_size=page_size)

    async def get_tournament(self, year: int) -> TournamentOut:
        return TournamentOutFactory(year=year)

    async def create_tournament(self, data: TournamentIn) -> TournamentOut:
        return TournamentOutFactory(year=data.year)

    async def update_tournament(self, year: int, data: TournamentUpdate) -> TournamentOut:
        return TournamentOutFactory(year=year)

    async def delete_tournament(self, year: int) -> None:
        return None

    async def get_matches(self, year: int, page: int = 1, page_size: int = 20, stage: str | None = None) -> Paginated[MatchListOut]:
        items = MatchListOutFactory.build_batch(2)
        return build_paginated(items, page=page, page_size=page_size)

    async def get_top_scorers(self, year: int, top: int = 10) -> list[TopScorerOut]:
        return TopScorerOutFactory.build_batch(3)

    async def get_teams(self, year: int) -> list[TeamOut]:
        return TeamOutFactory.build_batch(4)


class MockMatchService:
    async def list_matches(self, page: int = 1, page_size: int = 20, year: int | None = None, stage: str | None = None, team: str | None = None, min_goals: int | None = None) -> Paginated[MatchListOut]:
        items = MatchListOutFactory.build_batch(3)
        return build_paginated(items, page=page, page_size=page_size)

    async def search_matches(self, q_str: str, limit: int = 20) -> list[MatchListOut]:
        return MatchListOutFactory.build_batch(2)

    async def get_match(self, match_id: int) -> MatchOut:
        return MatchOutFactory(match_id=match_id)

    async def get_match_players(self, match_id: int) -> list[PlayerAppearanceOut]:
        return PlayerAppearanceOutFactory.build_batch(5)


class MockPlayerService:
    async def list_appearances(self, page: int = 1, page_size: int = 20, team: str | None = None, position: str | None = None, year: int | None = None) -> Paginated[PlayerAppearanceOut]:
        items = PlayerAppearanceOutFactory.build_batch(3)
        return build_paginated(items, page=page, page_size=page_size)

    async def search_players(self, q_str: str, limit: int) -> list[PlayerAppearanceOut]:
        return PlayerAppearanceOutFactory.build_batch(2)

    async def get_top_scorers(self, top: int = 10, team: str | None = None, position: str | None = None) -> list[TopScorerOut]:
        return TopScorerOutFactory.build_batch(5)

    async def get_player_career(self, name: str) -> PlayerCareerOut:
        return PlayerCareerOutFactory(player_name=name)


class MockAdminService:
    async def list_user(self, page: int = 1, page_size: int = 20, role: str | None = None, is_active: bool | None = None) -> Paginated[AdminUserOut]:
        items = AdminUserOutFactory.build_batch(3)
        return build_paginated(items, page=page, page_size=page_size)

    async def get_user(self, user_id: str) -> AdminUserOut:
        return AdminUserOutFactory()

    async def update_user(self, user_id: str, data: AdminUserOut) -> AdminUserOut:
        return AdminUserOutFactory()

    async def soft_delete_user(self, user_id: str) -> None:
        return None

    async def trigger_etl(self, data: EtlTriggerIn, triggered_by: str) -> dict:
        return {"status": "queued", "dataset": data.dataset}

    async def get_etl_status(self, dataset: str | None = None) -> EtlStatusOut:
        return EtlStatusOut(status="success")

    async def get_dead_letters(self, page: int = 1, page_size: int = 20, dataset: str | None = None, error_code: str | None = None) -> Paginated[DeadLetterOut]:
        return build_paginated([])

    async def refresh_warehouse(self) -> dict:
        return {"status": "ok", "message": "All warehouse views refreshed"}

    async def get_audit_log(self, page: int = 1, page_size: int = 20, table_name: str | None = None, operation: str | None = None) -> dict:
        return {"items": [], "total": 0}
