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

class RegisterIn(BaseModel):
  email: EmailStr
  password: str = Field(min_length=8, max_length=128)
  display_name: str | None = Field(default=None, max_length=80)

  @field_validator("password")
  @classmethod
  def password_has_digit(cls, v:str) -> str:
    if not any(c.isdigit() for c in v):
      raise ValueError("La Contraseña debe contener al menos un Dígito")
    return v


class LoginIn(BaseModel):
  email: EmailStr
  password: str


class UserOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)
  user_id: uuid.UUID
  email: EmailStr
  display_name: str | None = None
  role: Literal["admin", "editor", "reader"]
  is_active: bool
  created_at: datetime


class UserUpdateIn(BaseModel):
  display_name:str | None = Field(default=None, max_length=80)


class ChangePasswordIn(BaseModel):
  current_password: str
  new_password: str = Field(min_length=8, max_length=128)
  

# ─── Tournaments ──────────────────────────────────────────────────────────────

class TournamentOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  tournament_id: int
  year: int
  host_country: str
  winner: str
  runners_up: str
  third_place: str | None = None
  fourth_place: str | None = None
  goals_scored: int
  qualified_teams: int
  matches_played: int
  attendance_total: int | None = None
  avg_goals_per_match: float | None = None


class TournamentListOut(BaseModel): 
  model_config = ConfigDict(from_attributes=True)

  tournament_id: int
  year: int
  host_country: str
  winner: str
  goals_scored: int
  matches_played: int


class TournamentIn(BaseModel):
  year:int=Field(ge=1930, le=2030)
  host_country:str=Field(max_length=100)
  winner:str=Field(max_length=100)
  runners_up:str=Field(max_length=100)
  third_place:str | None = None
  fourth_place:str | None = None
  goals_scored:int = Field(ge=0)
  qualified_teams: int = Field(ge=1, le=48)
  matches_played: int = Field(ge=1)
  attendance_total: int | None = None


class TournamentUpdate(BaseModel):
  winner: str | None = None
  runners_up: str | None = None
  goals_scored: int | None = Field(default=None, ge=0)
  attendance_total: int | None = None

# ─── Teams ────────────────────────────────────────────────────────────────────


# ─── Matches ─────────────────────────────────────────────────────────────────

 
# ─── Players ─────────────────────────────────────────────────────────────────


# ─── Admin ────────────────────────────────────────────────────────────────────
 