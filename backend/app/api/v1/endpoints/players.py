"""
  # Endpoints: Players
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.v1.endpoints.deps import get_player_service
from app.schemas.schemas import (
  Paginated, 
  PlayerAppearanceOut, 
  PlayerCareerOut, 
  TopScorerOut,
)

from app.services.domain_analytics import PlayerService

router = APIRouter(prefix="players", tags=["Players"])


# ─── GET /players ─────────────────────────────────────────────────────────────
@router.get("/players", 
            response_model=Paginated[PlayerAppearanceOut],
            summary=" Listar (orden) apariciones de jugadores (dentro del Mundial/Torneo). Agregamos filtros"  # noqa: E501
            )
async def players_list(
  page: int = Query(default=1, ge=1), 
  page_size: int = Query(default=20, ge=1, le=100),
  team: str | None = Query(default=None, min_length=2, max_length=3, description="Iniciales FIFA del Equipo / Selección"),  # noqa: E501
  position: Literal["GK", "DF", "MF", "FW"] | None = Query(default=None, description="Posición del Jugador | Player Position"),  # noqa: E501
  year: int | None = Query(default=None, ge=1930, le=2030, description="Edición del Mundial | Mundial Edition"),  # noqa: E501
  service_players: PlayerService = Depends(get_player_service),  # noqa: B008
) -> Paginated[PlayerAppearanceOut]: 
  """
    Lista apariciones de jugadores en partidos del Mundial con filtros opcionales.
    - **200**: Lista paginada de apariciones.
  """
  return await service_players.list_appearances(
    page=page, 
    page_size=page_size, 
    team=team, 
    position=position, 
    year=year,
  )

# ─── GET /players/search ─────────────────────────────────────────────────────────────
@router.get("/players/search", 
            response_model= list[PlayerAppearanceOut], 
            summary=" Búsqueda (search) de jugadores por nombre ",
            )
async def players_search(
  q:str = Query(min_length=2, description="Nombre o parte del Nombre (Siglas) - Tolerante a acentos (pg_trgm)"),  # noqa: E501
  limit: int = Query(default=10, ge=1, le=50),
  service_players: PlayerService = Depends(get_player_service),  # noqa: B008
) -> list[PlayerAppearanceOut]:
  """
    Búsqueda de jugadores por nombre usando `pg_trgm` (similitud fuzzy + ILIKE).
    Tolerante a variaciones de acentos y errores tipográficos leves.
 
    - **200**: Lista de apariciones únicas por jugador/equipo.
  """
  return await service_players.search_players(q_str=q, limit=limit)


# ─── GET /players/top-scorers ─────────────────────────────────────────────────────────────


# ─── GET /players/{name}/career ─────────────────────────────────────────────────────────────