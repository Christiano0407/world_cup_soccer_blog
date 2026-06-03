"""
  Async database engine, session factory, and dependency injection.
  (Motor de base de datos asíncrono, fábrica de sesiones e inyección de dependencias.)
    - Sesiones & Conexion entre: DB & API - FastAPI
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
  AsyncEngine,
  AsyncSession,
  async_sessionmaker,
  create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_setting
from app.core.logging import get_logger

logger = get_logger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

#! ─── FastAPI Engine & Sessions | Async with Db - Postgres ──────────────────────────────────────────  # noqa: E501

def get_engine(settings: Settings | None = None) -> AsyncEngine: 
  global _engine
  if _engine is None: 
    cfg = settings or get_setting()
    _engine = create_async_engine(
      cfg.db_url_str, 
      pool_size=cfg.DATABASE_POOL_SIZE,
      max_overflow=cfg.DATABASE_MAX_OVERFLOW, 
      pool_timeout=cfg.DATABASE_POOL_TIMEOUT,
      pool_pre_ping=True,
      echo=cfg.DATABASE_ECHO,
    )
  return _engine


def get_sessions_factory(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]: 
  global _session_factory
  if _session_factory is None: 
    engine = get_engine(settings)
    _session_factory = async_sessionmaker (
      engine, 
      class_=AsyncSession, 
      expire_on_commit=False,
      autoflush=False, 
      autocommit=False
    )
  return _session_factory



#? ─── FastAPI dependency ───────────────────────────────────────────────────────



#// ─── Test helpers ─────────────────────────────────────────────────────────────