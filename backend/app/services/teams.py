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
  - Implementar el ORM & SQL => Services (Business Logic)
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

  async def list_teams(
      self, 
      active: bool | None = None,
      confederation: str | None = None,
  ) -> list[TeamOut]:
    query = select(Team)
    if active is not None:
      query = query.where(Team.active == active)
    if confederation:
      query = query.where(Team.confederation == confederation)
    query = query.order_by(Team.name)
    result_team = await self._db.execute(query)
    # = Es el error típico de SQLAlchemy — scalar() = un valor, scalars() = varios valores.#
    return [TeamOut.model_validate(t) for t in result_team.scalars()]

  async def _get_team(self, initials:str) -> Team:
    result_query = await self._db.execute(
      select(Team).where(func.upper(Team.initials == initials.upper()))
    )
    teams = result_query.scalar_one_or_none()
    if not teams:
      raise ValueError(f"Equipo/Selección {initials}")
    return teams
  
  async def get_team_stats(self, initials:str) -> TeamStatsOut:
    team = await self._get_team(initials)
    # = Aggregate Match stats in a Single Query = #
    stats_query = text("""
        SELECT 
          COUNT(DISTINCT t.tournament_id)                     AS tournaments_played, 
          COUNT(CASE WHEN t.winner = :name THEN 1 END)        AS titles,
    """)