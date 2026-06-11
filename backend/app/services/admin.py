"""
  Admin service — user management, ETL pipeline, warehouse, audit log.
    [Este servicio ya no pertenece al dominio “usuario final”, sino al dominio administración y operaciones. Aquí se concentran tareas que normalmente usan administradores, operadores o procesos internos.]
  # =============================================================== #
    ¿Qué responsabilidades agrupa?

        - Administración de usuarios
        - Listar, consultar, modificar roles y desactivar usuarios.

    ETL Pipeline
        
        - Disparar cargas de datos y consultar el estado de ejecuciones.

    Warehouse / Analytics

        - Refrescar vistas materializadas o tablas analíticas.

    Auditoría y errores

        - Consultar logs de cambios y registros rechazados (dead letters).
  # =============================================================== #
    Request
    ↓
    FastAPI Router
    ↓
    AdminService
    ↓
    PostgreSQL (users, etl_runs, dead_letters, audit_log)
    Warehouse (materialized views / analytics)
    Celery/ARQ (background jobs)
  # =============================================================== #
    IAM
    │
    ├── Authentication
    │      └── AuthService
    │
    ├── Authorization
    │      └── Roles
    │
    └── User Administration
          └── AdminService
  # =============================================================== #
    UserAdminService
    │
    ├── list_users()
    ├── update_user()
    └── deactivate_user()

    ETLService
    │
    ├── trigger_etl()
    └── get_status()

    WarehouseService
    │
    └── refresh_views()

    AuditService
    │
    └── get_logs()
  # =============================================================== #
"""  # noqa: E501

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.orm import AuditLog, DeadLetter, EtlRun, User
from app.schemas.schemas import (
  AdminUserOut,
  AdminUserUpdate,
  DeadLetterOut,
  EtlStatusOut,
  EtlTriggerIn,
  Paginated,
)


# ==== Admin Service: Logic Business ========================================================= #
class AdminService: 
  def __init__(self, db:AsyncSession) -> None:
    self._db = db 

  async def list_user(
      self, page:int = 1, page_size:int = 20, 
      role: str | None = None, is_active:bool | None = None
      ) -> Paginated[AdminUserOut]:  # type: ignore
    pass

  async def _get_user(
      self, user_id:str
      ) -> User: # type: ignore
    pass

  async def get_user(
      self, user_id:str
  ) -> AdminUserOut: # type: ignore
    pass

  async def update_user(
      self, user_id:str, 
      data_update_user: AdminUserUpdate
      ) -> AdminUserOut: # type: ignore
    pass
  