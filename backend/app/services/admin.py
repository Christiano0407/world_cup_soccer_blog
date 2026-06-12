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
  
  # ---- List de Usuarios (Access | Permisos) ----
  async def list_user(
      self, page:int = 1, page_size:int = 20, 
      role: str | None = None, is_active:bool | None = None
      ) -> Paginated[AdminUserOut]:  # type: ignore
    """
      - Construye una consulta base: select(User).
      - Aplica filtros opcionales por rol y estado.
      - Ordena por fecha de creación descendente.
      - Calcula el total de registros para paginación.
      - Aplica OFFSET y LIMIT.
      - Convierte los modelos ORM a DTOs (AdminUserOut).
    """
    query = select(User)

    if role: 
      q = query.where(User.role == role)
    if is_active is not None:
      q = query.where(User.is_active == is_active)
    q = query.order_by(User.created_at.desc())

    total = (await self._db.execute(select(func.count()).select_from(q.subquery()))).scalar() or 0

    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await self._db.execute(q)

    items = [AdminUserOut.model_validate(user) for user in result.scalars()]
    pages = -(-total // page_size)
    return Paginated(items=items, total=total, page=page, page_size=page_size, pages=pages)

  # === Obtener User Privado(Method) ===
  async def _get_user(
      self, user_id:str
      ) -> User: # type: ignore
    """
      - Busca un usuario por UUID.
          Si no existe, lanza NotFoundError, que normalmente termina en un 404 Not Found
    """
    result_query = await self._db.execute(
      select(User).where(User.user_id == uuid.UUID(user_id))
    )
    user = result_query.scalar_one_or_none()
    if not user:
      raise NotFoundError(f"User: {user_id} | Usuario no encontrado - Not Found User (404)")
    return user

  async def get_user(
      self, user_id:str
  ) -> AdminUserOut: # type: ignore
    """
      - Devuelve un único usuario usando el método privado anterior y lo transforma a AdminUserOut.
    """
    user = await self._get_user(user_id)
    return AdminUserOut.model_validate(user)

  async def update_user(
      self, user_id:str, 
      data_update_user: AdminUserUpdate
      ) -> AdminUserOut: # type: ignore
    """
      - Reglas de negocio:
          Permite cambiar el rol.
          Permite activar/desactivar la cuenta.
          Actualiza updated_at.
    """
    user = await self._get_user(user_id)
    if data_update_user.role is not None:
      user.role = data_update_user.role
    if data_update_user.is_active is not None:
      user.is_active = data_update_user.is_active
    user.update_at = datetime.now(UTC)
    return AdminUserOut.model_validate(user)

  async def soft_delete_user(
    self, user_Id:str  # noqa: N803
    ) -> None:
    """
      No elimina físicamente el registro.
        - Ventajas del soft delete
        - Conserva historial.
        - Permite auditoría.
        - Evita romper referencias.
        - Permite restaurar usuarios.
    """
    user = await self._get_user(user_Id)
    user.is_active = False
    user.update_at = datetime.now(UTC)
  
  # ==== Workers - ETL & Data | Functions ====
  async def trigger_etl(
      self, data:EtlTriggerIn, 
      triggered_by:str
      ) -> dict: # type: ignore
    """
      - ETL significa Extract, Transform, Load.
      - Qué hace:
          Crea un registro EtlRun.
          Marca el estado como running.
          Guarda quién disparó el proceso.
          Hace flush para obtener el run_id.
          Devuelve un estado de “queued”.
      - En un sistema real, aquí normalmente se enviaría una tarea a un worker de fondo como Celery, ARQ o RQ.
    """  # noqa: E501
    run = EtlRun(
      dataset=data.dataset, 
      worker="celery",
      status= "running", 
      started_at=datetime.now(UTC), 
      triggered_by = triggered_by,
    )
    self._db.add(run)
    await self._db.flush() # Object change in DB
    # In production: enqueue to Celery/ARQ here
    # celery_app.send_task("etl.run", args=[data.dataset, run.run_id])
    return { "status": "queued", "dataset": data.dataset }

  async def get_etl_status(
      self, dataset:str | None = None
  ) -> EtlStatusOut: # type: ignore
    """
      - Consulta la última ejecución ETL de un dataset.
      - Si no existe ninguna ejecución, devuelve:
    """
    query = select(EtlRun).order_by(EtlRun.started_at.desc())
    if dataset: 
      q = query.where(EtlRun.dataset == dataset)
    q = query.limit(1)
    result = await self._db.execute(q)
    run = result.scalar_one_or_none()
    if not run: 
      return EtlStatusOut(status="success")
    return EtlStatusOut.model_validate(run)
  
  async def get_dead_letters(
      self, 
      page: int = 1,
      page_size: int = 20, 
      dataset:str | None = None, 
      error_code: str | None = None
  ) -> Paginated[DeadLetterOut]: # type: ignore
    """
      - Una Dead Letter Queue (DLQ) almacena registros que no pudieron procesarse correctamente.
      - Qué hace: 
          Filtra por dataset.
          Filtra por código de error.
          Ordena por fecha de rechazo.
          Pagína resultados.
      - Supón que un CSV trae una fecha inválida. Ese registro puede enviarse a dead_letters en lugar de abortar toda la carga ETL.
    """  # noqa: E501
    q = select(DeadLetter)
    if dataset: 
      q = q.where(DeadLetter.source_table == dataset)
    if error_code: 
      q = q.where(DeadLetter.error_code == error_code)
    
    q = q.order_by(DeadLetter.rejected_at.desc())

    total = (await  self._db.execute(
      select(func.count()).select_from(q.subquery())
    )).scalar() or 0

    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await self._db.execute(q)

    items = [DeadLetterOut.model_validate(d1) for d1 in result.scalars()]
    pages = -(-total // page_size)
    return Paginated(items=items, total=total, page=page, page_size=page_size, pages = pages)


  # = ---- Warehouse Data ---- #
  async def refresh_warehouse(
      self
  ) -> dict: # type: ignore
    """
      Ejecuta una función SQL:
        Qué suele hacer esa función:
          Refrescar vistas materializadas.
          Recalcular métricas agregadas.
          Actualizar tablas analíticas.
    """
    await self._db.execute(__import__("sqlalchemy").text("SELECT warehouse.refresh_all()"))
    return { "status": "ok", "message": "All warehouse views refreshed" }

  # === ---- Log (Logging / History) ---- === #
  async def get_audit_log(
      self, 
      page: int = 1, 
      page_size: int = 20, 
      table_name: str | None = None,
      operation: str | None = None
  ) -> dict: # type: ignore
    """
      Consulta cambios realizados sobre la base de datos.
        Filtros disponibles:
          Tabla afectada.
          Operación (INSERT, UPDATE, DELETE).
        Formato de salida:
          Para qué sirve
          Trazabilidad.
          Cumplimiento.
          Investigación de incidentes.
          Auditoría de seguridad.
    """
    q = select(AuditLog)
    if table_name:
        q = q.where(AuditLog.table_name == table_name)
    if operation:
        q = q.where(AuditLog.operation == operation)
    q = q.order_by(AuditLog.changed_at.desc())

    total = (await self._db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await self._db.execute(q)

    items = [
        {
            "log_id": row.log_id,
            "schema_name": row.schema_name,
            "table_name": row.table_name,
            "operation": row.operation,
            "changed_by": row.changed_by,
            "changed_at": row.changed_at.isoformat(),
        }
        for row in result.scalars()
    ]
    return {"items": items, "total": total}