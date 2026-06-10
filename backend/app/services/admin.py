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
