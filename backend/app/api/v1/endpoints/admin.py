"""
  Endpoints: Admin [Rutas para admin - API]
"""

from __future__ import annotations

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


# ─── PATCH /admin/users/{user_id} ─────────────────────────────────────────────


# ─── POST /admin/etl/trigger ──────────────────────────────────────────────────


# ─── GET /admin/etl/dead-letter ───────────────────────────────────────────────


# ─── POST /admin/warehouse/refresh ────────────────────────────────────────────


# ─── GET /admin/audit-log ─────────────────────────────────────────────────────