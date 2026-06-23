"""
  Admin router — /api/v1/admin/* (role=admin required)
  Health router — /api/health/*
  Main app entry point — FastAPI configuration + route registration.
  Prometheus - Monitoring [Open Source]
  # ==== 
  asynccontextmanager: [es ideal para gestionar recursos como conexiones a bases de datos o archivos de forma segura en entornos asíncronos.]
  AsyncGenerator: [Es un tipo (protocolo) utilizado principalmente para type hinting (anotación de tipos). |  Representa un objeto generador asíncrono nativo.]
"""  # noqa: E501

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

# === Routers === #
from app.api.v1.endpoints import admin as admin_router
from app.api.v1.endpoints import auth as auth_router
from app.api.v1.endpoints import health as health_router
from app.api.v1.endpoints import matches as matches_router
from app.api.v1.endpoints import players as players_router
from app.api.v1.endpoints import teams as teams_router
from app.api.v1.endpoints import tournaments as tournaments_router

# Analytics endpoints (DASHBOARDS D3)
#from app.api.v1.endpoints.analytics import router as analytics_router
from app.core.config import Settings, get_setting
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.db.session import lifespan_db

# === Middlewares === #
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
  settings = get_setting()
  configure_logging(log_level=settings.LOG_LEVEL, environment=settings.ENVIRONMENT)

  # = DB Connection Pool
  async with lifespan_db(settings):
    # Redis connections for rate limiting
    from app.api.v1.endpoints.deps import get_redis
    redis = await get_redis()
    app.state.redis = redis

    yield 

  # shutdown
  await app.state.redis.close()


# = Create APP - FastAPI = 
def create_app() -> FastAPI:
  settings = get_setting()

  app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION, 
    doc_api="/docs" if settings.docs_enable else None,
    redoc_url="/redoc" if settings.docs_enable else None,
    lifespan=lifespan,
  )

  # CORS
  app.add_middleware(
    CORSMiddleware, 
    allow_origins=[str(o) for o in settings.CORS_ORIGIN],
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS, 
    allow_methods=["*"], 
    allow_headers=["*"], 
  )

  # Exception Handlers
  register_exception_handlers(app)

  # Router - API v1 [OpenAPI]
  API_V1_PREFIX = "/api/v1"  # noqa: N806
  app.include_router(auth_router.router, prefix=API_V1_PREFIX)
  app.include_router(admin_router.router, prefix=API_V1_PREFIX)
  app.include_router(teams_router.router, prefix=API_V1_PREFIX)
  app.include_router(tournaments_router.router, prefix=API_V1_PREFIX)
  app.include_router(matches_router.router, prefix=API_V1_PREFIX)
  app.include_router(players_router.router, prefix=API_V1_PREFIX)
  app.include_router(health_router.router)
  #app.include_router(analytic_router, prefix=API_V1_PREFIX)

  # Prometheus Metrics
  Instrumentator().instrument(app).expose(app)

  return app