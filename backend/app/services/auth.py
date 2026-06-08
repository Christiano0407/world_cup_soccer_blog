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