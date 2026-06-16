"""
  # Endpoint: Auth 
  # ======================================================== #
   - "El payload (o carga útil) en un JSON Web Token (JWT) es la sección 
   que contiene la información real o los datos que se transmiten a 
   la aplicación, estructurados como pares clave-valor conocidos 
   como claims. "
  # ======================================================== #
  [" El jti (JWT ID) es un campo opcional en los tokens JWT que actúa 
    como un identificador único para una instancia específica del token, 
    funcionando como un número de serie criptográfico "]
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
@router.post("/refresh",
             response_model=TokenOut,
             status_code=status.HTTP_200_OK, 
             summary= " Renovar Access Token (Refresh Access Token)"
             )
async def refresh(
  response: Response, 
  payload: dict = Depends(get_refresh_token_from_cookies),  # noqa: B008
  auth_service: AuthService = Depends(get_auth_service),  # noqa: B008
) -> TokenOut:
  """
     Renueva el `access_token` usando la cookie HTTP-only `refresh_token`.
    El refresh token se **rota** en cada llamada.
 
    - **200**: Nuevo access token + cookie rotada.
    - **401**: Cookie ausente, inválida o expirada.
  """
  return await auth_service.refresh(payload, response)


# ─── POST /logOut ───────────────────────────────────────────────────────────
@router.post("/logout", 
             status_code=status.HTTP_204_NO_CONTENT, 
             summary="Cerrar Sesión (Close Session)",
             )
async def logout(
  response: Response, 
  current_user: CurrentUser = Depends(get_current_user),  # noqa: B008
  credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),  # noqa: B008
  auth_service: AuthService = Depends(get_auth_service)  # noqa: B008
) -> None:
  """
    Cierra la sesión: revoca el access token en Redis y borra la cookie.
 
    - **204**: Sesión cerrada.
    - **401**: Token ausente o inválido.
    # ====
    - Extraemos el jti del access token para revocarlo en Redis -
  """
  bearer_jti = None
  if credentials: 
    from app.core.config import get_setting
    from app.core.security import decode_token
    try: 
      payload = decode_token(credentials.credentials, get_setting())
      bearer_jti = payload.get("jti")
    except Exception:  # noqa: S110
      pass 

  await auth_service.logout(current_user.user_id, bearer_jti, response)

# ─── Get /me ───────────────────────────────────────────────────────────


# ─── PATCH /me ───────────────────────────────────────────────────────────


# ─── POST /change password ───────────────────────────────────────────────────────────