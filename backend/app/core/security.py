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

# ─── Password | Encriptado (bcrypt) | Hash (Hashed | HASHEANDO password  | SALT ───────── #
# - Un hash es una función matemática: 
# - bcrypt es un algoritmo especializado de hashing para passwords. [Contiene  salt]
# - Un salt es un valor aleatorio agregado al password.
# =======
# Hash	    Función matemática
# Hashing	Proceso de aplicar hash
# Hashed	Resultado ya procesado
# bcrypt	Algoritmo hashing especializado
# =======

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") 

def hash_password(plain:str) -> str:
    return _pwd_context.hash(plain)

def verify_password(plain:str, hashed:str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ─── JWT (JSON Web Token) ────────────────────────────────────────────────────────────────
 
_bearer_scheme = HTTPBearer(auto_error=False)

def _create_token(
        subject: str, # Usuario
        kind: str, # Tipo de Token
        expires_delta: timedelta, # Fecha de Expiración 
        settings: Settings, # Datos
        extra: dict[str, Any] | None = None, 
) -> str: 
    now = datetime.now(UTC) # Fecha Actual
    # Payload: Claims [Es un objeto JSON codificado en Base64 que almacena pares clave-valor.]
    payload: dict[str, Any] = {
        "sub": subject,
        "kind": kind,
        "iat": now, 
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()), # Tipado | Valor único
        **(extra or {}),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# === Create Access Token ===
def create_access_token(user_id: str, role: str, settings: Settings) -> str:
    return _create_token(
        subject = user_id, 
        kind = "access", # Type Token
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        settings = settings,
        extra={"role":role} 
    )


# === Refresh Token ===
def create_refresh_token(user_id:str, settings:Settings) -> str:
    return _create_token(
        subject=user_id, 
        kind="refresh", # Type Token
        expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        settings=settings,
    )


# === Decode (Decodificar el Error) Token  | Error Token ===
def decode_token(token: str, settings: Settings) -> dict[str, Any]: 
    try: 
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc: 
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales Inválidas o Expiraron | Fecha del 'Token' expiró", 
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

# ─── FastAPI Dependencies ────────────────────────────────────────────────────
# - Minimal parsed token payload injected into routes. (Carga útil mínima del token analizado inyectada en las rutas)  # noqa: E501

class CurrentUser: 
    """
        Minimal parsed token payload injected into routes. (Carga útil mínima del token analizado inyectada en las rutas)
    """  # noqa: E501
    def __init__(self, user_id:str, role:str) -> None:
        self.user_id = user_id
        self.role = role


def _get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),  # noqa: B008
        settings: Settings = Depends(get_setting),  # noqa: B008
) -> CurrentUser:
        if not credentials:
                raise HTTPException(
                     status_code=status.HTTP_401_UNAUTHORIZED, 
                     detail= "Credenciales Inválidas o han expirado | Tiempo del Token expiró",
                     headers={"WWW-Authenticate": "Bearer"},
                )
        payload = decode_token(credentials.credentials, settings)
        if payload.get("kind") != "access":
             raise HTTPException(
                  status_code=status.HTTP_401_UNAUTHORIZED, 
                  detail="Token Inválido - Se requiere access token",
             )
        return CurrentUser(user_id=payload["sub"], role=payload.get("role", "reader"))


def get_current_user(
          user:CurrentUser=Depends(_get_current_user)  # noqa: B008
          ) -> CurrentUser:
     return user


def require_roles(*roles: str):  # noqa: ANN201
    """
        Factory that returns a dependency enforcing role membership.(Fábrica que devuelve una dependencia que impone la membresía del rol.)
        - 403 Forbidden en la autenticación 'JWT' indica que el servidor rechaza 
            el acceso porque el token es inválido, está ausente 
            o carece de los permisos necesarios.
        - 403 Forbidden indica que el servidor entiende la solicitud pero niega 
            el acceso porque el cliente carece de los permisos necesarios.
    """  # noqa: E501
 
    def _dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:  # noqa: B008
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado | el token es inválido, está ausente o carece de los permisos necesarios")  # noqa: E501
        return user
 
    return _dep


require_admin = require_roles("admin")
require_editor_or_admin = require_roles("admin", "editor")


def get_refresh_token_from_cookies(
          refresh_token: str | None = Cookie(default=None, alias="refresh_token"),
          settings: Settings=Depends(get_setting),  # noqa: B008
) -> dict[str, Any]:
    if not refresh_token:
        raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED, 
             detail="Refresh Token Ausente"
        )
    payload = decode_token(refresh_token, settings)

    if payload.get("kind") != "refresh":
        raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
             detail="Token Inválido - se requiere 'refresh token'"
        )
    return payload
