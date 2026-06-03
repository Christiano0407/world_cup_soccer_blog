"""
  Async database engine, session factory, and dependency injection.
  (Motor de base de datos asíncrono, fábrica de sesiones e inyección de dependencias.)
    - Sesiones & Conexion entre: DB & API - FastAPI
"""

from __future__ import annotations

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

_engina: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

# ─── FastAPI Engine | Async with Db - Postgres ──────────────────────────────────────────────

# ─── FastAPI dependency ───────────────────────────────────────────────────────



# ─── Test helpers ─────────────────────────────────────────────────────────────