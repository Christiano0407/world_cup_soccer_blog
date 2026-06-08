"""
  Now let me create the service layer and route handlers 
    - Lógica & Reglas de Negocio ((Business Layer) de tu módulo de autenticación.)
    - Authentication service — register, login, refresh, password change.
  ## ============================================================================ ##
  La capa Service contiene las reglas de negocio.
    - No le importa HTTP.
    - No le importa FastAPI.
    - No le importa Swagger. 
    - No le importa JSON.
    - Su única responsabilidad es:
      Tomar datos
          ↓
          Aplicar reglas de negocio
          ↓
          Usar BD
          ↓
          Usar Redis
          ↓
          Usar JWT
          ↓
          Devolver resultados
  ## ============================================================================== ##
  - Utilizamos Métodos Privados: (_)
"""  # noqa: E501

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import redis.asyncio as aioredis
from fastapi import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AuthenticationError, BusinessLogicError, ConflictError
from app.core.security import (
  create_access_token, 
  create_refresh_token, 
  hash_password, 
  verify_password, 
)

from app.models.orm import User
from app.schemas.schemas import (
  ChangePasswordIn, 
  LoginIn, 
  RegisterIn, 
  TopScorerOut, 
  UserOut, 
  UserUpdateIn
)



# === Refresh Tokens | Cookies === --------------------------------------------------
def _set_refresh_cookies(response: Response, token: str, settings: Settings) -> None:
  """ 
    Cookie: 'Se guarda en el Navegador'
      - Redis no almacena la Cookie. | 
      - Redis almacena información relacionada con el token.
  """ 
  response.set_cookie(
    key=settings.REFRESH_COOKIES_NAME,
    value=token,
    httponly=settings.REFRESH_COOKIE_HTTPONLY, 
    secure=settings.REFRESH_COOKIE_SECURE, 
    samesite=settings.REFRESH_COOKIE_SAMESITE, 
    path=settings.REFRESH_COOKIE_PATH, 
    max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
  )


# === Clear Refresh Tokens | Cookies === --------------------------------------------------
def _clear_refresh_cookies(response: Response, settings: Settings) -> None:
  response.delete_cookie(
    key=settings.REFRESH_COOKIES_NAME, 
    path=settings.REFRESH_COOKIE_PATH,
  )


# === Authentication Service [Logic, Routes & Roles To the Business] === -------------------------