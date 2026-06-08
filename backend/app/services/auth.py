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
  ## ============================================================================== ## 
  Los datos dentro del payload se organizan en pares clave-valor llamados claims.  
  Existen tres tipos principales:

    ' Claims registrados (Registered claims): Son un conjunto de campos predefinidos por el estándar (RFC 7519) que se recomiendan para asegurar la interoperabilidad. No son obligatorios, pero muy comunes:
    - iss (Issuer): Identifica quién emitió el token.
    - sub (Subject): Identifica al usuario o entidad principal.
    - aud (Audience): Define para quién es válido el token (ej. una API específica).
    - exp (Expiration time): Marca temporal después de la cual el token no debe ser aceptado.
    - nbf (Not Before): Marca temporal antes de la cual el token no debe ser aceptado.
    - iat (Issued At): Indica cuándo fue creado el token.
    - jti (JWT ID): Identificador único del token. 
    
    Claims públicos (Public claims): Son definidos por la comunidad y registrados en el IANA JSON Web Token Registry para evitar colisiones de nombres. Suelen usar nombres cortos para ahorrar espacio. 
    
    Claims privados (Private claims): Son personalizados y acordados entre las partes que utilizan el token para compartir información específica de la aplicación que no está estandarizada (ej. user_role, department_id)'.

  ## ============================================================================== ##
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
  TokenOut,
  TopScorerOut,
  UserOut,
  UserUpdateIn,
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
  
  # === Get USER by Email ===
  async def _get_user_by_email(self, email: str) -> User | None: 
    '''
      scalar_one_or_none() es un método del sistema de resultados de SQLAlchemy ORM/Core,
      no de FastAPI ni de PostgreSQL
    '''
    result = await self._db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
  
  # === Get User By ID ===
  async def _get_user_by_id(self, user_id: str) -> User:
    result = await self._db.execute(select(User).where(User.user_id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
      raise AuthenticationError("Usuario No encontrado | Vuelve a Autenticar tu Usuario")
    return user
  
  # ==== Register (User) | 'Crear una cuenta Nueva. Un nuevo Registro' ====
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
        expires_in=self._settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60, # Seconds
      )
  
  # ==== LOGIN (User) | 'Ya existe una Cuenta del Usuario' ====
  async def login(self, data_login: LoginIn, response: Response) -> TokenOut:
    user = await self._get_user_by_email(data_login.email)

    if not user or not verify_password(data_login.password, user.hashed_password):
      raise AuthenticationError("Credenciales Inválidas o han expirado")
    
    if not user.is_active: 
      raise AuthenticationError("Cuenta Desactivada | Activa tu cuenta o Vuelve a activarla")
    
    access_token = create_access_token(str(user.user_id), user.role, self._settings)
    refresh_token = create_refresh_token(str(user.user_id), self._settings)
    _set_refresh_cookies(response, refresh_token, self._settings)
    
    # Type: Bearer
    return TokenOut(
        access_token=access_token,
        expires_in=self._settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60, # Seconds
      )
  
  # ==== REFRESH (User) | 'Actualizar el Token & Ver si ha sido Revocado' ====
  async def refresh(self, payload:dict, response: Response) -> TokenOut:
    """
      'El payload es la segunda parte de un Token JWT (JSON Web Token) que contiene la 
        información real o datos que se transmiten entre las partes, estructurados como pares clave-valor conocidos como claims.'
      # ==== #
      'Al escribir user_id: str = payload["sub"], estás extrayendo la identidad única del usuario desde el token JWT.' [El campo sub (abreviatura de subject o "sujeto"]
    """  # noqa: E501
    pass

    return TokenOut()
  
  
  # ==== LOGOUT (User) | 'Salirme | Revoked el Access' ====

  
  # === Get Me (User) | 'Obtener mis datos de Acceso' ===
  
  
  # === Update Me (User) | 'Actualizar mis Datos' ===


  # === Change Password (User) | 'Actualizar mis Datos - Cambiar mi contraseña' ===
