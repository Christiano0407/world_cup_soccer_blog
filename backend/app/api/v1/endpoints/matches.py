"""
  #  /api/v1/matches [Endpoints: Matches]
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.v1.endpoints.deps import get_match_service
from app.schemas.schemas import (
  MatchListOut,
  MatchOut,
  Paginated,
  PlayerAppearanceOut,
)
from app.services.domain_analytics import MatchService

router = APIRouter(prefix="/matches", tags=["Matches"])

# ─── GET /matches ─────────────────────────────────────────────────────────────
@router.get("/matches",
            response_model=Paginated[MatchListOut], 
            summary="Listar partidos con filtros (Orden los partidos del Torneo/Mundial)",
             )
async def matches_list(
  page:int = Query(default=1, ge=1), 
  page_size:int = Query(default=20, ge=1, le=100), 
  year:int | None = Query(default=None, ge=1930, le=2030, description="Inicio del Mundial"),
  stage:str | None = Query(default=None, description="Fase:Group, Semis-Finals, Finals..."),
  team:str | None = Query(default=None, max_length=3, description="Iniciales del Equipo/Selección (Iniciales) - Local & Visitante"),  # noqa: E501
  min_goals:int | None = Query(default=None, ge=0, description="Mínimo de Total de Goles en un Partido del Mundial"),  # noqa: E501
  matches_service:MatchService = Depends(get_match_service),
  ) -> Paginated[MatchListOut]:
  """
    Lista todos los partidos históricos con filtros opcionales combinables.
    - **200**: Lista paginada de partidos.
  """
  return await matches_service.list_matches(
    page=page, 
    page_size=page_size, 
    year=year, 
    stage=stage, 
    team=team, 
    min_goals=min_goals,
  )

# ─── GET /matches/search  (debe ir ANTES de /{match_id}) ─────────────────────
router.get("/search", 
           response_model=list[MatchListOut], 
           summary="Búsqueda por texto libre (Buscar su País/Selección)",
           )
async def matches_search(
    q:str = Query(min_length=2, description="Buscar una Selección, Estadio, Ciudad o árbitro"), 
    limit:int = Query(default=10, ge=1, le=50),
    match_service:MatchService = Depends(get_match_service),  # noqa: B008
) -> list[MatchListOut]:
   """
    Búsqueda de partidos por texto libre contra nombre de equipo,
    estadio, ciudad o árbitro.
      - **200**: Lista de resultados (sin paginar).
  """
   return await match_service.search_matches(q_str=q, limit=limit)


# ─── GET /matches/{match_id} ──────────────────────────────────────────────────


# ─── GET /matches/{match_id}/player ──────────────────────────────────────────

