from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.services.admin import AdminService
from app.services.auth import AuthService
from app.services.domain_analytics import (
    AnalyticsService,
    MatchService,
    PlayerService,
    TournamentService,
)
from app.services.teams import TeamService


@pytest_asyncio.fixture
def settings() -> Settings:
    return Settings(
        JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters!!",
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test",
        REDIS_URL="redis://localhost:6379/0",
        REFRESH_COOKIE_SECURE=False,
        ENVIRONMENT="development",
    )


class MockRow:
    def __init__(self, data: dict):
        object.__setattr__(self, '_data', data)
        for k, v in data.items():
            object.__setattr__(self, k, v)

    def __getattr__(self, name: str) -> Any:
        return self._data.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        self._data[name] = value

    def _asdict(self) -> dict:
        return self._data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def keys(self):
        return self._data.keys()

    def __iter__(self):
        return iter(self._data)


class MockScalars:
    def __init__(self, items: list | None = None):
        self._items = items or []

    def all(self) -> list:
        return self._items

    def __iter__(self):
        return iter(self._items)


class MockMappings:
    def __init__(self, items: list[dict] | None = None, one: dict | None = None):
        self._items = [MockRow(d) for d in (items or [])]
        self._one = MockRow(one) if one else None

    def all(self) -> list:
        return self._items

    def one_or_none(self) -> Any:
        return self._one

    def first(self) -> Any:
        return self._items[0] if self._items else None

    def __iter__(self):
        return iter(self._items)


class MockResult:
    def __init__(
        self,
        scalar_one: Any = None,
        scalars_list: list | None = None,
        mappings_list: list[dict] | None = None,
        mappings_one: dict | None = None,
        all_list: list[dict] | list | None = None,
    ):
        self._scalar_one = MockRow(scalar_one) if isinstance(scalar_one, dict) else scalar_one
        self._scalars_list = [MockRow(d) if isinstance(d, dict) else d for d in (scalars_list or [])]
        self._scalars = MockScalars(self._scalars_list)
        self._mappings = MockMappings(mappings_list, mappings_one)
        self._all_list = all_list

    def scalar_one_or_none(self) -> Any:
        return self._scalar_one

    def scalar(self) -> Any:
        return self._scalar_one

    def scalars(self):
        return self._scalars

    def all(self) -> list:
        if self._all_list is not None:
            return [MockRow(d) if isinstance(d, dict) else d for d in self._all_list]
        return self._scalars_list

    def one(self) -> Any:
        return self._scalar_one

    def first(self) -> Any:
        return self._scalar_one

    def fetchone(self) -> Any:
        return self._scalar_one

    def one_or_none(self) -> Any:
        return self._scalar_one

    def mappings(self):
        return self._mappings

    def __iter__(self):
        return iter(self._scalars_list)


@pytest_asyncio.fixture
def mock_db() -> MagicMock:
    _auto_ids: dict[str, int] = {}
    db = MagicMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()

    async def _flush_with_id() -> None:
        call = db.add.call_args
        if call and call.args:
            obj = call.args[0]
            pk_fields = {
                "Team": "team_id", "Tournaments": "tournament_id",
                "Match": "match_id", "PlayerAppearance": "player_match_id",
                "User": "user_id",
            }
            cls_name = type(obj).__name__
            if cls_name in pk_fields:
                pk = pk_fields[cls_name]
                if getattr(obj, pk, None) is None:
                    _auto_ids[cls_name] = _auto_ids.get(cls_name, 0) + 1
                    setattr(obj, pk, _auto_ids[cls_name])

    db.flush.side_effect = _flush_with_id
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.delete = AsyncMock()
    return db


def _configure_db_execute(mock_db: MagicMock, return_value: Any = None, side_effect: list | None = None) -> None:
    if side_effect:
        mock_db.execute.side_effect = side_effect
    else:
        mock_db.execute.return_value = return_value or MockResult()


@pytest_asyncio.fixture
def mock_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock()
    redis.pipeline = AsyncMock()
    pipe = AsyncMock()
    pipe.zremrangebyscore = AsyncMock()
    pipe.zadd = AsyncMock()
    pipe.zcard = AsyncMock(return_value=0)
    pipe.expire = AsyncMock()
    pipe.execute = AsyncMock(return_value=[0, 0, 0, True])
    redis.pipeline.return_value = pipe
    return redis


@pytest_asyncio.fixture
def auth_service(mock_db: MagicMock, mock_redis: AsyncMock, settings: Settings) -> AuthService:
    return AuthService(db=mock_db, settings=settings, redis=mock_redis)


@pytest_asyncio.fixture
def team_service(mock_db: MagicMock) -> TeamService:
    return TeamService(db=mock_db)


@pytest_asyncio.fixture
def tournament_service(mock_db: MagicMock) -> TournamentService:
    return TournamentService(db=mock_db)


@pytest_asyncio.fixture
def match_service(mock_db: MagicMock) -> MatchService:
    return MatchService(db=mock_db)


@pytest_asyncio.fixture
def player_service(mock_db: MagicMock) -> PlayerService:
    return PlayerService(db=mock_db)


@pytest_asyncio.fixture
def admin_service(mock_db: MagicMock) -> AdminService:
    return AdminService(db=mock_db)


@pytest_asyncio.fixture
def sample_user_dict() -> dict:
    return {
        "user_id": uuid.uuid4(),
        "email": "cr7@example.com",
        "display_name": "Cristiano",
        "hashed_password": "$2b$12$LJ3m4ys3Lk",
        "role": "reader",
        "is_active": True,
        "created_at": datetime.now(UTC),
        "update_at": datetime.now(UTC),
        "refresh_jti": None,
    }


@pytest_asyncio.fixture
def sample_admin_dict() -> dict:
    return {
        "user_id": uuid.uuid4(),
        "email": "admin@fifa.com",
        "display_name": "Admin FIFA",
        "role": "admin",
        "is_active": True,
        "created_at": datetime.now(UTC),
        "update_at": datetime.now(UTC),
    }


def make_orm_model(model_dict: dict) -> type:
    return type("MockModel", (), model_dict)
