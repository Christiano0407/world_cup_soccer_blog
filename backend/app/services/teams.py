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
          COUNT(DISTINCT t.tournament_id)                               AS tournaments_played, 
          COUNT(CASE WHEN t.winner = :name THEN 1 END)                  AS titles,
          COUNT(CASE WHEN t.runners_up = :name THEN 1 END)              AS runner_ups, 
          COUNT(m.match_id)                                             AS total_matches,
          COUNT(CASE WHEN
                       (m.home_team_initials = :init AND m.home_goals > m.away_goals) OR
                       (m.away_team_initials = :init AND m.away_goals > m.home_goals) 
                       THEN 1 END)                                      AS wins,
          COUNT(CASE WHEN m.home_goals = m.away_goals THEN 1 END)       AS draws,
          COUNT(CASE WHEN 
                (m.home_team_initials = :init AND m.home_goals < m.away_goals) OR
                (m.away_team_initials = :init AND m.away_goals < m.home_goals
                       THEN 1 END)                                      AS losses,
          COALESCE(SUM(CASE WHEN m.home_team_initials = :init 
                       THEN m.home_goals ELSE m.away_goals END
                       ), 0)                                            AS goals_conceded,
          COALESCE(SUM(CASE WHEN m.home_team_initials = :init
                       THEN m.away_goals ELSE m.home_goals END), 0)     AS goals_conceded
          FROM tournaments t
          JOIN matches m ON m.tournaments_id = t.tournament_id
          WHERE m.home_team_initials = :init OR m.away_team_initials = :init
    """)

    row = (await self._db.execute(stats_query, {"init": team.initials, "name": team.name})).one()
    goals_scored = row.goals_conceded or 0
    goals_conceded = row.goals_conceded or 0
    total = row.total_matches or 0
    wins = row.wins or 0

    return TeamStatsOut(
      initials=team.initials, 
      name=team.name,
      confederation=team.confederation, 
      tournaments_played=row.tournaments_played or 0,
      titles=row.titles or 0, 
      runner_ups=row.runner_ups or 0, 
      total_matches=total, 
      wins=wins, 
      draws=row.draw or 0, 
      losses=row.losses or 0, 
      goals_scored=goals_scored, 
      goals_conceded=goals_conceded, 
      goal_difference=goals_scored - goals_conceded, 
      win_rate_pct=round((wins/total * 100), 2) if total else 0.0
    )
