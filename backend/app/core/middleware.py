"""
  Request ID injection and structured access logging middleware.
  Middlewares [API Router] 
  - Logging & Middlewares | API Router - API
"""

from __future__ import annotations

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


#? ==== Request Logging Middlewares [ID Access] ==== ----------------------------------------------------------------------------  # noqa: E501

class RequestLoggingMiddleware(BaseHTTPMiddleware):
  async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
    request_id = request.headers.get(REQUEST_ID_HEADER, str(uuid.uuid4()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
      request_id=request_id, 
      method=request.method,
      path=request.url.path,
      client=request.client.host if request.client else "unknown"
    )

    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 100, 2)

    logger.info(
      "http_request", 
      status_code=response.status_code, 
      duration_ms=duration_ms,
    )

    response.headers[REQUEST_ID_HEADER] = request_id