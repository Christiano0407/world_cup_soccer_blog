""" 
  System health  - Ha ocurrido con éxito
  System health check endpoints. [ Conjunto de Endpoints para: Monitorear el estado del sistema]
  # ==================================================== #
    - Aquí ya salimos de la capa Service (Lógica de Negocio) y entramos en la capa API REST
    - La API REST recibe solicitudes HTTP
  # ==================================================== #
    Recibe Request
    ↓
    Valida
    ↓
    Llama Servicios
    ↓
    Devuelve Response
  # ==================================================== #
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_setting
from app.db.session import get_db
from app.schemas.schemas import ComponentHealthOut, HealthOut

router = APIRouter(tags=["System"])

#? === Health ===
@router.get("/api/health", response_model=HealthOut)
async def health_check(settings: Settings = Depends(get_setting)) -> HealthOut:
  return HealthOut(
    status="ok", 
    version=settings.APP_VERSION, 
    environment=settings.ENVIRONMENT,
  )

#? ==== Health/DB ==== 
@router.get("/api/health/db", response_model=ComponentHealthOut)
async def health_db(db: AsyncSession = Depends(get_db)) -> ComponentHealthOut:
  try:
    start = time.perf_counter()
    await db.execute(text("SELECT 1"))
    latency = round((time.perf_counter() - start) * 1000, 2)
    return ComponentHealthOut(
      component="db", 
      status="ok", 
      latency_ms=latency
    )
  except Exception:
    return ComponentHealthOut(
      component="db", 
      status="down", 
      latency_ms=None
    )


#? ===== Health/Storage =====
@router.get("/api/health/storage", response_model=ComponentHealthOut)
async def health_storage() -> ComponentHealthOut:
  # ---- Stub - real impl would ping MinIO | Storage s3 ----
  return ComponentHealthOut(
    component="storage", 
    status="ok", 
    latency_ms=None
  )