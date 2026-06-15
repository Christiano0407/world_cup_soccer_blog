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

from fastapi import APIRouter, Depends, 
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_setting
from app.db.session import get_db
from app.schemas.schemas import ComponentHealthOut, HeadToHeadOut, HealthOut

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


#? ===== Health/Storage =====