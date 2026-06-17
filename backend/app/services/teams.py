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

  # === [GET | Private] === #
  async def _get_team(self, initials:str) -> Team:
    result_query = await self._db.execute(
      select(Team).where(func.upper(Team.initials) == initials.upper())
    )
    teams = result_query.scalar_one_or_none()
    if not teams:
      raise NotFoundError(f"Selección(Team): {initials} no encontrada")
    return teams
  
  async def get_team_stats(self, initials:str) -> TeamStatsOut:
    team = await self._get_team(initials)
    # = Aggregate Match stats in a Single Query = #
    stats_query = text("""
         SELECT
              COUNT(DISTINCT t.tournament_id)                                 AS tournaments_played,
              COUNT(CASE WHEN t.winner    = :name THEN 1 END)                 AS titles,
              COUNT(CASE WHEN t.runners_up = :name THEN 1 END)                AS runner_ups,
              COUNT(m.match_id)                                               AS total_matches,
              COUNT(CASE WHEN
                  (m.home_team_initials = :init AND m.home_goals > m.away_goals) OR
                  (m.away_team_initials = :init AND m.away_goals > m.home_goals)
                  THEN 1 END)                                                 AS wins,
              COUNT(CASE WHEN m.home_goals = m.away_goals THEN 1 END)         AS draws,
              COUNT(CASE WHEN
                  (m.home_team_initials = :init AND m.home_goals < m.away_goals) OR
                  (m.away_team_initials = :init AND m.away_goals < m.home_goals)
                  THEN 1 END)                                                 AS losses,
              COALESCE(SUM(CASE
                  WHEN m.home_team_initials = :init THEN m.home_goals
                  ELSE m.away_goals
              END), 0)                                                        AS goals_scored,
              COALESCE(SUM(CASE
                  WHEN m.home_team_initials = :init THEN m.away_goals
                  ELSE m.home_goals
              END), 0)                                                        AS goals_conceded
            FROM tournaments t
            JOIN matches m ON m.tournament_id = t.tournament_id
            WHERE m.home_team_initials = :init OR m.away_team_initials = :init
    """)

    row = (
        await self._db.execute(stats_query, {"init": team.initials, "name": team.name})
    ).one()

    goals_scored   = row.goals_scored   or 0
    goals_conceded = row.goals_conceded or 0
    total          = row.total_matches  or 0
    wins           = row.wins           or 0

    return TeamStatsOut(
        initials=team.initials,
        name=team.name,
        confederation=team.confederation,
        tournaments_played=row.tournaments_played or 0,
        titles=row.titles     or 0,
        runner_ups=row.runner_ups or 0,
        total_matches=total,
        wins=wins,
        draws=row.draws       or 0,   # BUG FIX: era row.draw (sin 's')
        losses=row.losses     or 0,
        goals_scored=goals_scored,
        goals_conceded=goals_conceded,
        goal_difference=goals_scored - goals_conceded,
        win_rate_pct=round((wins / total * 100), 2) if total else 0.0,
    )

  # === [GET] === #
  async def get_ranking(
      self,
      sort_by: str = "titles", 
      min_matches: int = 5
  ) -> list[TeamStatsOut]:
    
    result = await self._db.execute(select(Team).where(Team.active == True))  # noqa: E712
    teams = result.scalars().all()  # noqa: F841

    stats = [] # List / Matriz / Array  # noqa: F841

    for team in teams:
      try:
        s = await self.get_team_stats(team.initials)
        if s.total_matches >= min_matches:
          stats.append(s)
      except NotFoundError:
        continue

    key_map = {
      "titles":lambda s:s.titles,
      "wins":lambda s:s.wins,
      "goals_scored":lambda s:s.goals_scored,
      "total_matches":lambda s:s.total_matches,
    }

    return sorted(stats, key=key_map.get(sort_by, lambda s:s.titles), reverse=True)

  # === [CRUD] - Create a new Team / Selección === #
  async def create_team(self, data_team: TeamIn) -> TeamOut:
    existing_team = await self._db.execute(
      select(Team).where(func.upper(Team.initials) == data_team.initials.upper())
    )
    if existing_team.scalar_one_or_none():
      raise ConflictError(f"El Team(Selección): {data_team.initials} ya existe (Ya tiene un lugar dentro del Torneo Mundial de fútbol)")  # noqa: E501
    team = Team(**data_team.model_dump())
    self._db.add(team)
    await self._db.flush() 
    return TeamOut.model_validate(team)
  
  # === [CRUD] - Update === #
  async def update_team(self, initials: str, data_update: TeamUpdate) -> TeamOut:
    team = await self._get_team(initials)
    for field, value in data_update.model_dump(exclude_none=True).items(): # Considera: Scalar_one_none...(_get_team)  # noqa: E501
      setattr(team, field, value)
    return TeamOut.model_validate(team)


  async def get_matches(
      self, 
      initials: str, 
      page: int = 1, 
      page_size: int = 20,
      year: int | None = None, 
      stage: str | None = None, 
  ) -> Paginated[MatchListOut]:
    
    await self._get_team(initials)

    query = select(Match).where(
      or_(
        Match.home_team_initials == initials.upper(),
        Match.away_team_initials == initials.upper(),
      )
    )

    if year: 
      query = query.where(Match.year == year)
    if stage: 
      query = query.where(Match.stage == stage)

    total = (await self._db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0  # noqa: E501
    q = query.order_by(Match.match_datetime.desc())
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await self._db.execute(q)

    items = [MatchListOut.model_validate(m) for m in result.scalars()]
    pages = -(-total // page_size) # Ceiling Division
    return Paginated(items = items, total=total, page=page, page_size=page_size ,pages=pages)



  async def head_to_head(self, initials_a:str, initials_b:str) -> HeadToHeadOut: 
    """ Confrontar & Comparar entre Selecciones | SQL:Todos los Parámetros (HeadToHeadOut)"""
    await self._get_team(initials_a)
    await self._get_team(initials_b)
    # = SQL/Postgres = #
    query = text(
      """
        SELECT 
          COUNT(*)                                                  AS total_matches,
          MIN(year)                                                 AS first_encounter, 
          MAX(year)                                                 AS last_encounter, 
          COUNT(
            CASE WHEN 
              (home_team_initials = :a AND home_goals > away_goals) 
              OR 
              (away_team_initials = :a AND away_goals > home_goals)
              THEN 1 END
              )                                                     AS team_a_wins,
          COUNT(
            CASE WHEN
              (home_team_initials = :b AND home_goals > away_goals)
              OR 
              (away_team_initials = :b AND away_goals > home_goals)
              THEN 1 END
              )                                                     AS team_b_wins,
          COUNT(CASE WHEN home_goals = away_goals THEN 1 END)       AS draws,
          SUM(CASE WHEN home_team_initials :a 
              THEN home_goals ELSE away_goals END
          )                                                         AS team_a_goals,
          SUM(CASE WHEN away_team_initials :b
            THEN away_goals  ELSE home_goals  
          )                                                         AS team_b_goals,

          FROM matches 
          WHERE 
            (home_team_initials = :a AND away_team_initials :b)
            OR 
            (home_team_initials = :b AND away_team_initials :b)
      """
    )
    # = Filas = #
    row = (await self._db.execute(query, {"a": initials_a.upper(), "b": initials_b.upper()})).one()  # noqa: F841

    return HeadToHeadOut(
      team_a=initials_a.upper(), 
      team_b=initials_b.upper(),
      total_matches=row.total_matches or 0,  
      team_a_wins=row.team_a_wins or 0,
      team_b_wins=row.team_b_wins or 0,
      draws=row.draw or 0, 
      team_a_goals=row.team_a_goals or 0, 
      team_b_goals=row.team_b_goals or 0, 
      first_encounter=row.first_encounter or 0,
      last_encounter=row.last_encounter or 0,
    )

