"""
  Pydantic v2 schemas — mirrors the OpenAPI contract exactly.
  ("Los esquemas de Pydantic v2 (Tipar Datos) reflejan exactamente el contrato OpenAPI")
  - "Pydantic es la biblioteca de validación de datos más popular en Python, diseñada para 
    validar, convertir y serializar datos estructurados utilizando las anotaciones de tipo (type hints)
     nativas del lenguaje."
"""  # noqa: E501

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

T = TypeVar("T")


# ─── Shared ───────────────────────────────────────────────────────────────────

class ErrorOut(BaseModel):
  detail: str


class HealthOut(BaseModel):
  status: Literal["ok", "degraded", "down"]
  version: str
  environment: str


class ComponentHealthOut(BaseModel):
  component: str
  status: Literal["ok", "down"]
  latency_ms: float | None = None
  
  
class Paginated[T](BaseModel):
  items: list[T]
  total: int 
  page: int
  page_size: int
  pages: int


# ─── Auth ─────────────────────────────────────────────────────────────────────


# ─── Tournaments ──────────────────────────────────────────────────────────────


# ─── Teams ────────────────────────────────────────────────────────────────────


# ─── Matches ─────────────────────────────────────────────────────────────────

 
# ─── Players ─────────────────────────────────────────────────────────────────


# ─── Admin ────────────────────────────────────────────────────────────────────
 