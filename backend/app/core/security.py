"""Security utilities: JWT tokens, password hashing, cookie helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import Settings, get_setting

# ─── Password | Encriptado (bcrypt) | Hash (Hashed ──────────────────────────────── #

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # - Encriptado -

def hash_password(plain:str) -> str:
    return _pwd_context.hash(plain)

def verify_password(plain:str, hashed:str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ─── JWT (JSON Web Token) ────────────────────────────────────────────────────────────────
 

# ─── FastAPI Dependencies ────────────────────────────────────────────────────