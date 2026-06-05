"""
  Rate limiting middleware — Redis sliding window counter.
    - [Middleware limitador de velocidad — contador de ventana deslizante Redis.]
    - Límite de Peticiones (Request) (¿Cuántas veces ha llamado?)
      - Fuerza bruta sobre login.
      - Ataques de bots.
      - Scraping masivo.
      - DDoS básicos.
      - Consumo excesivo de recursos.
  # =================
    - "Es un framework/toolkit ASGI ligero y de alto rendimiento para Python, diseñado específicamente para construir aplicaciones web asíncronas y servicios API." | Es la base sobre la que se construye FastAPI
  # =================
    - RATE_LIMIT_AUTH & PUBLIC [Este middleware es una implementación profesional de Rate Limiting usando Redis + Sliding Window, algo muy común en APIs públicas]
"""  # noqa: E501

from __future__ import annotations

import time

import redis.asyncio as aioredis
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import get_setting
from app.core.logging import get_logger

logger = get_logger(__name__)

#? === ---- Auth endpoints get stricter limit | Endpoints --------------------------------- ===
_AUTH_PREFIXES = ("/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/refresh")


#! === ---- Rate limiting | Request - API --------------------------------- ===

class RateLimitingMiddleware(BaseHTTPMiddleware): 
  def __init__(self, app, redis_client: aioredis.Redis) -> None: # type: ignore[type-arg]  # noqa: ANN001
    super().__init__(app)
    self._redis = redis_client
    self._settings = get_setting

  async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
    path = request.url.path

    # === Determina el Límite (Limit) === #
    if any(path.startswith(p) for p in _AUTH_PREFIXES):
            limit = self._settings.RATE_LIMIT_AUTH
    else:
        limit = self._settings.RATE_LIMIT_PUBLIC

    # === Key per IP + path-bucket === #
    client_ip = request.client.host if request.client else "unknown"
    bucket = "auth" if any(path.startswith(p) for p in _AUTH_PREFIXES) else "public"
    key = f"ratelimiting:{client_ip}:{bucket}"

    now = int(time.time())
    window_start = now - 60 # 1-minute sliding window

    pipe = self._redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zadd(key, {str(now) + f":{time.monotonic_ns()}": now})
    pipe.zcard(key)
    pipe.expire(key, 61)
    results = await pipe.execute()
    results = await pipe.execute() 

    count: int = results[2]

    if count > limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Demasiadas solicitudes. Intente en un momento."},
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60",
                },
            )
    
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
    return response