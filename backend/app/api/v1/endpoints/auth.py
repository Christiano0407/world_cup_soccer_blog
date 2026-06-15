"""
  # Endpoint: Auth 
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.v1.endpoints.deps import get_auth_service
from app.core.config import Settings, get_setting

# Importamos tus dependencias nativas de seguridad [Ya tenemos las de FastAPI]
from app.core.security import (
  CurrentUser,
  _bearer_scheme,
  decode_token,
  get_current_user,
  get_refresh_token_from_cookies,
)
from app.schemas.schemas import (
  ChangePasswordIn,
  LoginIn,
  RegisterIn,
  TokenOut,
  UserOut,
  UserUpdateIn,
)
from app.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])

# ─── POST /register ───────────────────────────────────────────────────────────
@router.post("/register", 
             response_model=TokenOut, 
             status_code=status.HTTP_201_CREATED,
             summary="Registrar nuevo Usuario | Register new User"
             )
async def register(  # noqa: ANN201
  data_register: RegisterIn,
  response: Response, 
  auth_service: AuthService = Depends(get_auth_service),  # noqa: B008
) -> TokenOut: 
  """
    Registrar nuevo Usuario | Register new User.
    
    - **409 Conflict**: Si el email ya existe.
    - **422 Unprocessable Entity**: Si los datos de entrada no son válidos.
    - **201 Created**: Si el usuario se crea con éxito; inyecta la cookie HTTP-only.
  """
  return await auth_service.register(data_register, response)


# ─── POST /login ───────────────────────────────────────────────────────────
@router.post("/login",
             response_model=TokenOut, 
             status_code=status.HTTP_200_OK,
             summary="Iniciar Sesión (Init Session)"
             )
async def login(
  data_login: LoginIn, 
  response: Response, 
  auth_service: AuthService = Depends(get_auth_service),  # noqa: B008
) -> TokenOut:
  """
     Iniciar Sesión | Login.
 
    - **200**: Login exitoso; inyecta cookie `refresh_token` HTTP-only.
    - **401**: Credenciales inválidas.
    - **422**: Datos inválidos.
  """
  return await auth_service.login(data_login, response)


# ─── POST /refresh ───────────────────────────────────────────────────────────


# ─── POST /logOut ───────────────────────────────────────────────────────────


# ─── Get /me ───────────────────────────────────────────────────────────


# ─── PATCH /me ───────────────────────────────────────────────────────────


# ─── POST /change password ───────────────────────────────────────────────────────────