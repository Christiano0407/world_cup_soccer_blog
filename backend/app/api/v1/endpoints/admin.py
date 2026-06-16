"""
  Endpoints: Admin [Rutas para admin - API]
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status 

from app.api.v1.endpoints.deps import get_admin_service
from core.security import CurrentUser, require_admin
from app.schemas.schemas import (
  AdminUserOut, 
  AdminUserUpdate, 
  DeadLetterOut, 
  EtlStatusOut, 
  EtlTriggerIn, 
  Paginated
)
from app.services.admin import AdminService

router = APIRouter(prefix="admin", tags=["Admin"])


# ─── GET /admin/users ─────────────────────────────────────────────────────────
@router.get(
    "/users", 
    response_model=Paginated[AdminUserOut], 
    summary="Listar (Ordenar) los usuario que tienen acceso & permisos (role)")
async def list_users(
  page:int = Query(default=1, ge=1),
  page_size: int = Query(default=20, g1=1, le=100), 
  role:str | None = Query(default=None, description="Filtrar por Rol: Admin | Editor | Reader"), 
  is_active: bool | None = Query(default=None, description="Filtrar por estado"), 
  _: CurrentUser=Depends(require_admin), 
  admin_service: AdminService = Depends(get_admin_service),
) -> Paginated[AdminUserOut]:
  """
    Lista todos los usuarios de la plataforma con filtros opcionales.
 
    - **200**: Lista paginada de usuarios.
    - **401**: Token ausente o inválido.
    - **403**: Rol insuficiente (requiere admin).
  """
  return await admin_service.list_user(page=page, page_size=page_size, role=role, is_active=is_active)

# ─── PATCH /admin/users/{user_id} ─────────────────────────────────────────────
@router.patch(
  "/users/{user_id}", 
  response_model=AdminUserOut, 
  summary="Modificar (Actualizar) el role del Usuario o estado del mismo",
)
async def update_user(
  user_id: uuid.UUID,
  data: AdminUserUpdate, 
  _: CurrentUser = Depends(require_admin), 
  admin_service: AdminService = Depends(get_admin_service),
) -> AdminUserOut:
  """
     Actualiza el rol y/o estado activo de un usuario.
 
    - **200**: Usuario actualizado.
    - **401**: Token ausente o inválido.
    - **403**: Rol insuficiente (requiere admin).
    - **404**: Usuario no encontrado.
  """
  return await admin_service.update_user(str(user_id), data)


# ─── POST /admin/etl/trigger [Ejecuta la función & Dataset Especificado] ──────────────────────────
@router.post("/etl/trigger", 
             status_code=status.HTTP_202_ACCEPTED, 
             )
async def etl_trigger(
  data_etl: EtlTriggerIn,
  current_user: CurrentUser = Depends(require_admin),
  admin_service: AdminService = Depends(get_admin_service),
) -> dict:
  """
     Dispara la ejecución del pipeline ETL para el dataset especificado.
 
    - **202**: Job ETL encolado.
    - **401**: Token ausente o inválido.
    - **403**: Rol insuficiente (requiere admin).
  """
  return await admin_service.trigger_etl(data_etl, triggered_by=current_user.user_id)

# ─── GET /admin/etl/dead-letter ───────────────────────────────────────────────
@router.get(
    "/etl/dead-letter",
    response_model=Paginated[DeadLetterOut],
    summary="Filas rechazadas por el ETL (admin)",
)
async def etl_dead_letter(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    source_table: str | None = Query(default=None, description="Filtrar por tabla de origen"),
    _: CurrentUser = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
) -> Paginated[DeadLetterOut]:
    """
    Retorna las filas rechazadas (dead letter queue) del pipeline ETL.
 
    - **200**: Lista paginada de filas rechazadas.
    - **401**: Token ausente o inválido.
    - **403**: Rol insuficiente (requiere admin).
    """
    return await admin_service.get_dead_letters(page=page, page_size=page_size, source_table=source_table)


# ─── POST /admin/warehouse/refresh ────────────────────────────────────────────
@router.post(
   "/warehouse/refresh", 
   status_code=status.HTTP_202_ACCEPTED, 
   summary="efrescar (refresh) vistas materializadas del warehouse (admin)",
)
async def warehouse_refresh(
   _:CurrentUser = Depends(require_admin), 
   admin_service: AdminService = Depends(get_admin_service), 
) -> dict: 
   """

    Dispara el refresco (refresh) de las vistas materializadas del data warehouse.
 
    - **202**: Refresco encolado.
    - **401**: Token ausente o inválido.
    - **403**: Rol insuficiente (requiere admin).
   """
   await admin_service.refresh_warehouse()
   return { "detail": "Warehouse refresh encolado" }


# ─── GET /admin/audit-log [History] ─────────────────────────────────────────────────────
@router.get(
    "/audit-log",
    summary="Log (History) de cambios en tablas de producción",
)
async def audit_log(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    table_name: str | None = Query(default=None, description="Filtrar por tabla: tournaments, matches, users, etc."),
    operation: str | None = Query(default=None, description="I=insert, U=update, D=delete"),
    _: CurrentUser = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
) -> dict:
    """
    Consulta cambios realizados sobre la base de datos.

    - **200**: Lista paginada de eventos de auditoría.
    - **401**: Token ausente o inválido.
    - **403**: Rol insuficiente (requiere admin).
    """
    return await admin_service.get_audit_log(
        page=page, page_size=page_size, table_name=table_name, operation=operation
    )