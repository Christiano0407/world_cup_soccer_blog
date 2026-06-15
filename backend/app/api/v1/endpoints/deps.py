"""
  - Este archivo unifica tus generadores de base de datos (get_db), la resolución 
    de la configuración global, tu cliente de caché y la instanciación limpia 
    de tu servicio de negocio.
"""  # noqa: E501

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.config import Settings, get_setting
from app.db.session import get_db
from app.services.admin import AdminService
from app.services.auth import AuthService
from app.services.domain_analytics import (
  AnalyticsService,
  MatchService,
  PlayerService,
  TournamentService,
)
from app.services.teams import TeamService


# ─── Redis connection (singleton) ────────────────────────────────────────
_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
  global _redis
  if _redis is None:
    settings = get_setting()
    _redis = aioredis.from_url(
      settings.db_redis_url_str,
      encoding="utf-8",
      decode_responses=True,
    )
  return _redis


# ─── Auth ────────────────────────────────────────────────────────────────
async def get_auth_service(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_setting),
    redis: aioredis = Depends(get_redis),
) -> AuthService:
  return AuthService(db=db, settings=settings, redis=redis)


# ─── Teams ───────────────────────────────────────────────────────────────
async def get_team_service(
    db: AsyncSession = Depends(get_db),
) -> TeamService:
  return TeamService(db=db)


# ─── Tournaments ─────────────────────────────────────────────────────────
async def get_tournament_service(
    db: AsyncSession = Depends(get_db),
) -> TournamentService:
  return TournamentService(db=db)


# ─── Matches ─────────────────────────────────────────────────────────────
async def get_match_service(
    db: AsyncSession = Depends(get_db),
) -> MatchService:
  return MatchService(db=db)


# ─── Players ─────────────────────────────────────────────────────────────
async def get_player_service(
    db: AsyncSession = Depends(get_db),
) -> PlayerService:
  return PlayerService(db=db)


# ─── Analytics ───────────────────────────────────────────────────────────
async def get_analytics_service(
    db: AsyncSession = Depends(get_db),
) -> AnalyticsService:
  return AnalyticsService(db=db)


# ─── Admin ───────────────────────────────────────────────────────────────
async def get_admin_service(
    db: AsyncSession = Depends(get_db),
) -> AdminService:
  return AdminService(db=db)
