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
    self._settings = get_setting()

  async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
    
    path = request.url.path 
    # [/api/v1/auth/login o /api/v1/products]

    # === Determina el Límite (Limit) === #
    # = ¿Es endpoint Auth? (Determinar el Límite ) = #
    if any(path.startswith(p) for p in _AUTH_PREFIXES):
            limit = self._settings.RATE_LIMIT_AUTH
    else:
        limit = self._settings.RATE_LIMIT_PUBLIC # Limit 100

    # === Key per IP + path-bucket === #
    client_ip = request.client.host if request.client else "unknown"
    bucket = "auth" if any(path.startswith(p) for p in _AUTH_PREFIXES) else "public"
    key = f"rl:{client_ip}:{bucket}"
    # key = rl:201.145.100.1:auth & Redis Almacena [rl:201.145.100.1:auth]

    now = int(time.time())  # Tiempo actual u Horario
    window_start = now - 60 # 1-minute (60 seconds) sliding window (desliza continuamente.)

    pipe = self._redis.pipeline() # [Agrupa Comandos (4 Redis / request)]
    pipe.zremrangebyscore(key, 0, window_start) # Elimina Registros Viejos (Peticiones Viejas)
    pipe.zadd(key, {str(now) + f":{time.monotonic_ns()}": now}) # Agrega Peticiones Actuales | Redis las almacena  # noqa: E501
    pipe.zcard(key)       # Cuenta elementos (Num Login/register...etc)
    pipe.expire(key, 61)  # 60 Seg / min Expira
    results = await pipe.execute() 

    count: int = results[2] # Va con zcard

    if count > limit:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, # - Código estándar para Rate Limiting.-  # noqa: E501
                content={"detail": "Demasiadas solicitudes. Intente en un momento."},
                headers={
                    "X-RateLimit-Limit": str(limit),  # - Tu límite de request
                    "X-RateLimit-Remaining": "0",     # - Te dice Cuántas te quedan...(request)?
                    "Retry-After": "60",              # - Espera 60 segundos (otra request)
                },
            )
    
    response = await call_next(request) # Si no excede el límite > continúa hacia FastAPI (API)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
    return response