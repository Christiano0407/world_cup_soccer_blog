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
  UserUpdateIn,
  TokenOut
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


# === [POO] Authentication Service [Logic, Routes & Roles To the Business] === ---------------------
# ---- Utilizamos Métodos Privados: (_) ----
class AuthService:
  def __init__(self, db:AsyncSession, settings: Settings, redis: aioredis.Redis) -> None:
    self._db = db
    self._settings = settings
    self._redis = redis

  async def _get_user_by_email(self, email: str) -> User | None: 
    '''
      scalar_one_or_none() es un método del sistema de resultados de SQLAlchemy ORM/Core,
      no de FastAPI ni de PostgreSQL
    '''
    result = await self._db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
  
  async def _get_user_by_id(self, user_id: str) -> User:
    result = await self._db.execute(select(User).where(User.user_id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
      raise AuthenticationError("Usuario No encontrado | Vuelve a Autenticar tu Usuario")
    return user
  
  async def register(self, data_register:RegisterIn, response:Response) -> TokenOut:
    existing = await self._get_user_by_email(data_register.email)

    if existing:
      raise ConflictError("El Email, ya está registrado")
    
    user = User(
      email = data_register.email, 
      hashed_password = hash_password(data_register.password), 
      display_name = data_register.display_name, 
      role="reader" 
    )

    self._db.add(user)
    await self._db.flush() # Get user_id

    access = create_access_token(str(user.user_id), user.role, self._settings)
    refresh = create_refresh_token(str(user.user_id), self._settings)
    _set_refresh_cookies(response, refresh, self._settings)
    
    # Type: Bearer
    return TokenOut(
      access_token=access, 
      expires_in=self._settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
      )