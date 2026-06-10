"""Tournaments, Matches, Players, and Analytics services."""

from __future__ import annotations

from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.orm import Match, PlayerAppearance, Team, Tournament
from app.schemas.schemas import (  # noqa: E402
    AttendanceTrendPoint,
    ChoroplethPoint,
    GoalsByStagePoint,
    GoalsPerEditionPoint,
    HalftimePoint,
    MatchListOut,
    MatchOut,
    Paginated,
    PlayerAppearanceOut,
    PlayerCareerOut,
    PositionPoint,
    TeamOut,
    TeamPerformancePoint,
    TopScorerOut,
    TournamentIn,
    TournamentListOut,
    TournamentOut,
    TournamentUpdate,
)

# ─── Tournaments ─────────────────────────────────────────────────────────────


class TournamentService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _get(self, year: int) -> Tournament:
        result = await self._db.execute(select(Tournament).where(Tournament.year == year))
        t = result.scalar_one_or_none()
        if not t:
            raise NotFoundError(f"Torneo {year}")
        return t

    async def list_tournaments(
        self,
        page: int = 1,
        page_size: int = 20,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> Paginated[TournamentListOut]:
        q = select(Tournament)
        if year_from:
            q = q.where(Tournament.year >= year_from)
        if year_to:
            q = q.where(Tournament.year <= year_to)
        q = q.order_by(Tournament.year)

        total = (await self._db.execute(select(func.count()).select_from(q.subquery()))).scalar()
        q = q.offset((page - 1) * page_size).limit(page_size)
        result = await self._db.execute(q)

        items = [TournamentListOut.model_validate(t) for t in result.scalars()]
        pages = -(-total // page_size)
        return Paginated(items=items, total=total, page=page, page_size=page_size, pages=pages)

    async def get_tournament(self, year: int) -> TournamentOut:
        t = await self._get(year)
        out = TournamentOut.model_validate(t)
        out.avg_goals_per_match = t.avg_goals_per_match
        return out

    async def create_tournament(self, data: TournamentIn) -> TournamentOut:
        existing = await self._db.execute(
            select(Tournament).where(Tournament.year == data.year)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"El torneo {data.year} ya existe")
        t = Tournament(**data.model_dump())
        self._db.add(t)
        await self._db.flush()
        return TournamentOut.model_validate(t)

    async def update_tournament(self, year: int, data: TournamentUpdate) -> TournamentOut:
        t = await self._get(year)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(t, field, value)
        return TournamentOut.model_validate(t)

    async def delete_tournament(self, year: int) -> None:
        t = await self._get(year)
        await self._db.delete(t)

    async def get_matches(
        self,
        year: int,
        page: int = 1,
        page_size: int = 20,
        stage: str | None = None,
    ) -> Paginated[MatchListOut]:
        await self._get(year)
        q = select(Match).where(Match.year == year)
        if stage:
            q = q.where(Match.stage == stage)

        total = (await self._db.execute(select(func.count()).select_from(q.subquery()))).scalar()
        q = q.order_by(Match.match_datetime).offset((page - 1) * page_size).limit(page_size)
        result = await self._db.execute(q)

        items = [MatchListOut.model_validate(m) for m in result.scalars()]
        pages = -(-total // page_size) # Ceiling Division
        return Paginated(items = items, total=total, page=page, page_size=page_size ,pages=pages)

    async def get_top_scorers(self, year: int, top: int = 10) -> list[TopScorerOut]:
        await self._get(year)
        q = text("""
            SELECT
                pa.player_name,
                pa.team_initials,
                COUNT(CASE WHEN pa.event_code = 'G' THEN 1 END)  AS goals,
                COUNT(CASE WHEN pa.event_code = 'OG' THEN 1 END) AS own_goals,
                COUNT(DISTINCT pa.match_id)                       AS matches_played,
                :year AS first_wc,
                :year AS last_wc,
                1 AS editions
            FROM player_appearances pa
            JOIN matches m ON m.match_id = pa.match_id
            WHERE m.year = :year
              AND pa.event_code IN ('G', 'OG')
            GROUP BY pa.player_name, pa.team_initials
            ORDER BY goals DESC
            LIMIT :top
        """)
        rows = (await self._db.execute(q, {"year": year, "top": top})).all()
        return [TopScorerOut(**row._asdict()) for row in rows]

    async def get_teams(self, year: int) -> list[TeamOut]:
        await self._get(year)
        q = text("""
            SELECT DISTINCT t.* FROM teams t
            JOIN matches m ON
                m.home_team_initials = t.initials OR m.away_team_initials = t.initials
            WHERE m.year = :year
            ORDER BY t.name
        """)
        result = await self._db.execute(q, {"year": year})
        rows = result.mappings().all()
        return [TeamOut(**row) for row in rows]


# ─── Matches ─────────────────────────────────────────────────────────────────


class MatchService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _get(self, match_id: int) -> Match:
        result = await self._db.execute(select(Match).where(Match.match_id == match_id))
        m = result.scalar_one_or_none()
        if not m:
            raise NotFoundError(f"Partido {match_id}")
        return m

    async def list_matches(
        self,
        page: int = 1,
        page_size: int = 20,
        year: int | None = None,
        stage: str | None = None,
        team: str | None = None,
        min_goals: int | None = None,
    ) -> Paginated[MatchListOut]:
        q = select(Match)
        if year:
            q = q.where(Match.year == year)
        if stage:
            q = q.where(Match.stage == stage)
        if team:
            q = q.where(
                or_(
                    Match.home_team_initials == team.upper(),
                    Match.away_team_initials == team.upper(),
                )
            )
        if min_goals is not None:
            q = q.where((Match.home_goals + Match.away_goals) >= min_goals)

        total = (await self._db.execute(select(func.count()).select_from(q.subquery()))).scalar()
        q = q.order_by(Match.match_datetime.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self._db.execute(q)

        items = [MatchListOut.model_validate(m) for m in result.scalars()]
        pages = -(-total // page_size)
        return Paginated(items=items, total=total, page=page, page_size=page_size, pages=pages)

    async def search_matches(self, q_str: str, limit: int = 20) -> list[MatchListOut]:
        q = text("""
            SELECT m.* FROM matches m
            LEFT JOIN teams ht ON ht.initials = m.home_team_initials
            LEFT JOIN teams at_ ON at_.initials = m.away_team_initials
            WHERE
                m.stadium ILIKE :q OR
                m.city ILIKE :q OR
                m.referee ILIKE :q OR
                ht.name ILIKE :q OR
                at_.name ILIKE :q
            ORDER BY m.match_datetime DESC
            LIMIT :limit
        """)
        result = await self._db.execute(q, {"q": f"%{q_str}%", "limit": limit})
        return [MatchListOut(**row._asdict()) for row in result.mappings()]

    async def get_match(self, match_id: int) -> MatchOut:
        q = text("""
            SELECT
                m.*,
                ht.name AS home_team_name,
                at_.name AS away_team_name
            FROM matches m
            LEFT JOIN teams ht ON ht.initials = m.home_team_initials
            LEFT JOIN teams at_ ON at_.initials = m.away_team_initials
            WHERE m.match_id = :match_id
        """)
        row = (await self._db.execute(q, {"match_id": match_id})).mappings().one_or_none()
        if not row:
            raise NotFoundError(f"Partido {match_id}")
        return MatchOut(**row)

    async def get_match_players(self, match_id: int) -> list[PlayerAppearanceOut]:
        await self._get(match_id)
        result = await self._db.execute(
            select(PlayerAppearance)
            .where(PlayerAppearance.match_id == match_id)
            .order_by(PlayerAppearance.team_initials, PlayerAppearance.shirt_number)
        )
        return [PlayerAppearanceOut.model_validate(p) for p in result.scalars()]


# ─── Players ─────────────────────────────────────────────────────────────────


class PlayerService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_appearances(
        self,
        page: int = 1,
        page_size: int = 20,
        team: str | None = None,
        position: str | None = None,
        year: int | None = None,
    ) -> Paginated[PlayerAppearanceOut]:
        q = select(PlayerAppearance)
        if team:
            q = q.where(PlayerAppearance.team_initials == team.upper())
        if position:
            q = q.where(PlayerAppearance.position == position)
        if year:
            q = q.join(Match).where(Match.year == year)

        total = (await self._db.execute(select(func.count()).select_from(q.subquery()))).scalar()
        q = q.offset((page - 1) * page_size).limit(page_size)
        result = await self._db.execute(q)

        items = [PlayerAppearanceOut.model_validate(p) for p in result.scalars()]
        pages = -(-total // page_size)
        return Paginated(items=items, total=total, page=page, page_size=page_size, pages=pages)

    async def search_players(self, q_str: str, limit: int = 20) -> list[PlayerAppearanceOut]:
        q = text("""
            SELECT DISTINCT ON (player_name, team_initials) *
            FROM player_appearances
            WHERE player_name ILIKE :q
               OR similarity(player_name, :raw) > 0.2
            ORDER BY player_name, team_initials
            LIMIT :limit
        """)
        result = await self._db.execute(
            q, {"q": f"%{q_str}%", "raw": q_str, "limit": limit}
        )
        return [PlayerAppearanceOut(**r._asdict()) for r in result.mappings()]

    async def get_top_scorers(
        self,
        top: int = 20,
        team: str | None = None,
        position: str | None = None,
    ) -> list[TopScorerOut]:
        filters = ""
        params: dict = {"top": top}
        if team:
            filters += " AND pa.team_initials = :team"
            params["team"] = team.upper()
        if position:
            filters += " AND pa.position = :position"
            params["position"] = position

        q = text(f"""
            SELECT
                pa.player_name,
                pa.team_initials,
                COUNT(CASE WHEN pa.event_code = 'G' THEN 1 END)  AS goals,
                COUNT(CASE WHEN pa.event_code = 'OG' THEN 1 END) AS own_goals,
                COUNT(DISTINCT pa.match_id)                       AS matches_played,
                MIN(m.year)                                       AS first_wc,
                MAX(m.year)                                       AS last_wc,
                COUNT(DISTINCT m.year)                            AS editions
            FROM player_appearances pa
            JOIN matches m ON m.match_id = pa.match_id
            WHERE pa.event_code IN ('G', 'OG') {filters}
            GROUP BY pa.player_name, pa.team_initials
            ORDER BY goals DESC
            LIMIT :top
        """)  # noqa: S608
        rows = (await self._db.execute(q, params)).all()
        return [TopScorerOut(**row._asdict()) for row in rows]

    async def get_player_career(self, name: str) -> PlayerCareerOut:
        q = text("""
            SELECT
                pa.player_name,
                pa.team_initials,
                COUNT(*)                                            AS total_appearances,
                COUNT(CASE WHEN pa.lineup_type = 'S' THEN 1 END)  AS starts,
                COUNT(CASE WHEN pa.lineup_type = 'N' THEN 1 END)  AS substitutions,
                COUNT(CASE WHEN pa.event_code = 'G' THEN 1 END)   AS goals,
                COUNT(CASE WHEN pa.event_code = 'Y' THEN 1 END)   AS yellow_cards,
                COUNT(CASE WHEN pa.event_code = 'R' THEN 1 END)   AS red_cards,
                ARRAY_AGG(DISTINCT m.year ORDER BY m.year)         AS editions
            FROM player_appearances pa
            JOIN matches m ON m.match_id = pa.match_id
            WHERE LOWER(pa.player_name) = LOWER(:name)
            GROUP BY pa.player_name, pa.team_initials
        """)
        row = (await self._db.execute(q, {"name": name})).mappings().one_or_none()
        if not row:
            raise NotFoundError(f"Jugador {name}")
        return PlayerCareerOut(**row)


# ─── Analytics ───────────────────────────────────────────────────────────────


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def goals_per_edition(self) -> list[GoalsPerEditionPoint]:
        q = text("""
            SELECT
                t.year, t.host_country, t.winner,
                t.goals_scored, t.matches_played,
                ROUND(t.goals_scored::numeric / NULLIF(t.matches_played, 0), 2) AS avg_goals_per_match,
                t.attendance_total,
                CASE WHEN t.matches_played > 0
                    THEN (t.attendance_total / t.matches_played)::int END        AS avg_attendance_per_match
            FROM tournaments t
            ORDER BY t.year
        """)  # noqa: E501
        rows = (await self._db.execute(q)).mappings().all()
        return [GoalsPerEditionPoint(**row) for row in rows]

    async def team_performance(self, min_matches: int = 5) -> list[TeamPerformancePoint]:
        q = text("""
            SELECT
                tm.initials,
                tm.name AS team_name,
                COUNT(DISTINCT m.tournament_id)                          AS tournaments_played,
                COUNT(CASE WHEN t.winner = tm.name THEN 1 END)          AS titles,
                COUNT(m.match_id)                                        AS total_matches,
                COUNT(CASE WHEN
                    (m.home_team_initials = tm.initials AND m.home_goals > m.away_goals) OR
                    (m.away_team_initials = tm.initials AND m.away_goals > m.home_goals)
                THEN 1 END)                                              AS wins,
                COUNT(CASE WHEN m.home_goals = m.away_goals THEN 1 END) AS draws,
                COUNT(CASE WHEN
                    (m.home_team_initials = tm.initials AND m.home_goals < m.away_goals) OR
                    (m.away_team_initials = tm.initials AND m.away_goals < m.home_goals)
                THEN 1 END)                                              AS losses,
                SUM(CASE WHEN m.home_team_initials = tm.initials
                    THEN m.home_goals ELSE m.away_goals END)             AS goals_scored,
                SUM(CASE WHEN m.home_team_initials = tm.initials
                    THEN m.away_goals ELSE m.home_goals END)             AS goals_conceded
            FROM teams tm
            JOIN matches m ON m.home_team_initials = tm.initials OR m.away_team_initials = tm.initials
            JOIN tournaments t ON t.tournament_id = m.tournament_id
            GROUP BY tm.initials, tm.name
            HAVING COUNT(m.match_id) >= :min_matches
            ORDER BY titles DESC, wins DESC
        """)
        rows = (await self._db.execute(q, {"min_matches": min_matches})).mappings().all()
        return [TeamPerformancePoint(**row) for row in rows]

    async def goals_by_stage(self, year: int | None = None) -> list[GoalsByStagePoint]:
        params: dict = {}
        year_filter = "WHERE m.year = :year" if year else ""
        if year:
            params["year"] = year

        q = text(f"""
            SELECT
                m.stage,
                {'m.year' if year else 'NULL::int'} AS year,
                COUNT(*)                                                  AS matches,
                SUM(m.home_goals + m.away_goals)                         AS total_goals,
                ROUND(AVG(m.home_goals + m.away_goals)::numeric, 2)      AS avg_goals,
                COUNT(CASE WHEN m.home_goals > m.away_goals THEN 1 END)  AS home_wins,
                COUNT(CASE WHEN m.away_goals > m.home_goals THEN 1 END)  AS away_wins,
                COUNT(CASE WHEN m.home_goals = m.away_goals THEN 1 END)  AS draws,
                AVG(m.attendance)::int                                   AS avg_attendance
            FROM matches m
            {year_filter}
            GROUP BY m.stage {',' + 'm.year' if year else ''}
            ORDER BY total_goals DESC
        """)  # noqa: S608
        rows = (await self._db.execute(q, params)).mappings().all()
        return [GoalsByStagePoint(**row) for row in rows]

    async def attendance_trends(self) -> list[AttendanceTrendPoint]:
        q = text("""
            SELECT
                t.year, t.host_country, t.qualified_teams, t.matches_played,
                AVG(m.attendance)::int AS avg_attendance,
                MAX(m.attendance)      AS max_attendance
            FROM tournaments t
            LEFT JOIN matches m ON m.tournament_id = t.tournament_id
            GROUP BY t.year, t.host_country, t.qualified_teams, t.matches_played
            ORDER BY t.year
        """)
        rows = (await self._db.execute(q)).mappings().all()
        return [AttendanceTrendPoint(**row) for row in rows]

    async def top_scorers_analytics(self, top: int = 20) -> list[TopScorerOut]:
        q = text("""
            SELECT
                pa.player_name, pa.team_initials,
                COUNT(CASE WHEN pa.event_code = 'G'  THEN 1 END)  AS goals,
                COUNT(CASE WHEN pa.event_code = 'OG' THEN 1 END)  AS own_goals,
                COUNT(DISTINCT pa.match_id)                        AS matches_played,
                MIN(m.year)                                        AS first_wc,
                MAX(m.year)                                        AS last_wc,
                COUNT(DISTINCT m.year)                             AS editions
            FROM player_appearances pa
            JOIN matches m ON m.match_id = pa.match_id
            WHERE pa.event_code IN ('G','OG')
            GROUP BY pa.player_name, pa.team_initials
            ORDER BY goals DESC
            LIMIT :top
        """)
        rows = (await self._db.execute(q, {"top": top})).all()
        return [TopScorerOut(**row._asdict()) for row in rows]

    async def positions(self, year: int | None = None) -> list[PositionPoint]:
        params: dict = {}
        year_filter = "JOIN matches m ON m.match_id = pa.match_id WHERE m.year = :year" if year else ""
        if year:
            params["year"] = year

        q = text(f"""
            SELECT
                pa.position,
                COUNT(*)                                               AS appearances,
                COUNT(CASE WHEN pa.lineup_type = 'S' THEN 1 END)     AS starts,
                ROUND(
                    COUNT(CASE WHEN pa.lineup_type = 'S' THEN 1 END)::numeric /
                    NULLIF(COUNT(*), 0) * 100, 2
                )                                                      AS starter_pct
            FROM player_appearances pa
            {year_filter}
            WHERE pa.position IS NOT NULL
            GROUP BY pa.position
            ORDER BY appearances DESC
        """)  # noqa: S608
        rows = (await self._db.execute(q, params)).mappings().all()
        return [PositionPoint(**row) for row in rows]

    async def halftime_analysis(self, year: int | None = None) -> list[HalftimePoint]:
        params: dict = {}
        year_filter = "AND m.year = :year" if year else ""
        if year:
            params["year"] = year

        q = text(f"""
            SELECT
                (m.ht_home_goals - m.ht_away_goals) AS ht_diff,
                (m.home_goals - m.away_goals)        AS ft_diff,
                CASE WHEN
                    SIGN(m.ht_home_goals - m.ht_away_goals) != SIGN(m.home_goals - m.away_goals)
                    OR (m.ht_home_goals = m.ht_away_goals AND m.home_goals != m.away_goals)
                THEN TRUE ELSE FALSE END              AS result_changed
            FROM matches m
            WHERE m.ht_home_goals IS NOT NULL {year_filter}
        """)  # noqa: S608
        rows = (await self._db.execute(q, params)).mappings().all()
        return [HalftimePoint(**row) for row in rows]

    async def choropleth(self) -> list[ChoroplethPoint]:
        q = text("""
            SELECT
                COALESCE(tm.fifa_code, tm.initials) AS iso3,
                tm.name                             AS team_name,
                COUNT(CASE WHEN t.winner = tm.name THEN 1 END)              AS titles,
                COUNT(CASE WHEN
                    (m.home_team_initials = tm.initials AND m.home_goals > m.away_goals) OR
                    (m.away_team_initials = tm.initials AND m.away_goals > m.home_goals)
                THEN 1 END)                                                  AS wins,
                COUNT(m.match_id)                                            AS total_matches
            FROM teams tm
            LEFT JOIN matches m ON m.home_team_initials = tm.initials OR m.away_team_initials = tm.initials
            LEFT JOIN tournaments t ON t.tournament_id = m.tournament_id
            GROUP BY tm.initials, tm.name, tm.fifa_code
            ORDER BY titles DESC
        """)  # noqa: E501
        rows = (await self._db.execute(q)).mappings().all()
        return [ChoroplethPoint(**row) for row in rows]