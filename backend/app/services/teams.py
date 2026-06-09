"""
  Teams service — CRUD + historical stats + head-to-head.
  Contiene:
  Funcionalidad	Objetivo
    - CRUD Teams	Crear, leer, actualizar, eliminar equipos
    - Historical Stats	Estadísticas históricas
    - Head-to-Head	Comparación entre dos equipos
    - Filters	Búsqueda por confederación o estado
  # ==================== #
  " Este código es un excelente ejemplo de una Service Layer orientada al dominio (Domain/Application Service).
    Aquí no estamos haciendo autenticación, sino implementando la lógica de negocio del dominio "Equipos de fútbol" 
  # ==================== #
"""  # noqa: E501

from __future__ import annotations

from sqlalchemy import case, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.orm import Match, Team, Tournaments
from app.schemas.schemas import (
  HeadToHeadOut,
  MatchListOut, 
  Paginated, 
  TeamIn, 
  TeamOut, 
  TeamStatsOut, 
  TeamUpdate,
)


class TeamService:
  def __init__(self, db:AsyncSession) -> None:
    self._db = db
    