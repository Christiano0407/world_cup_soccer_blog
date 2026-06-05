"""
  Rate limiting middleware — Redis sliding window counter.
    - [Middleware limitador de velocidad — contador de ventana deslizante Redis.]
  # =================
    - "Es un framework/toolkit ASGI ligero y de alto rendimiento para Python, diseñado específicamente para construir aplicaciones web asíncronas y servicios API." | Es la base sobre la que se construye FastAPI
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