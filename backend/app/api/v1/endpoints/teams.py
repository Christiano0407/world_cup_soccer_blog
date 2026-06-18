"""
  # Endpoint teams [/api/v1/teams]
  ## ================================ ##
  - "El símbolo _: en ese contexto de Python 
  (específicamente en FastAPI o Pydantic) significa que la 
  variable se está descartando intencionalmente"
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from typing import Literal

from app.api.v1.endpoints.deps import get_team_service
from app.core.security import CurrentUser, require_editor_or_admin
from app.schemas.schemas import (
  HeadToHeadOut,
  MatchListOut,
  Paginated,
  TeamIn,
  TeamOut,
  TeamStatsOut,
  TeamUpdate,
)

from app.services.teams import TeamService

router = APIRouter(prefix="/teams", tags=["Teams"])


## [Endpoints  - Routes | API REST]============================================================== ##

# ─── GET /teams ───────────────────────────────────────────────────────────────
@router.get("/teams", 
            status_code=status.HTTP_200_OK,
            summary="Listar (orden) todas las Selecciones de Fútbol",
            )
async def teams_list(
  active:bool | None = Query(default=None, description="Filter: active/not active"),
  confederation:str | None = Query(
     default=None, description="UEFA | CONMEBOL | AFC | CONCACAF | OFC",
     ),
  team_service:TeamService = Depends(get_team_service),
) -> list[TeamOut]:
   """
    Retorna la lista paginada de selecciones nacionales.
    - Active (Sigue jugando el Torneo) & su Confederación
    - **200**: Lista de equipos.
    """
   return await team_service.list_teams(active=active, confederation=confederation)


# ─── POST /teams ──────────────────────────────────────────────────────────────
@router.post(
   "/teams", 
   response_model=TeamOut,
   status_code=status.HTTP_201_CREATED,
   summary="Crear selección/equipo (admin)", 
)
async def create_team(
   data_team:TeamIn,
   _:CurrentUser = Depends(require_editor_or_admin),
   team_service:TeamService = Depends(get_team_service),
) -> TeamOut:
   """
    Crea una nueva selección nacional.
    - **201**: Equipo creado.
    - **401**: Token ausente o inválido.
    - **403**: Sin permisos suficientes.
    - **409**: Iniciales ya registradas.
   """
   return await team_service.create_team(data_team=data_team)

# ─── GET /teams/ranking  (debe ir ANTES de /{initials}) ──────────────────────
@router.get(
   "/ranking", 
   response_model=list[TeamStatsOut], 
   description="Ranking Histórico de Selecciones de Fútbol en el Mundial",
)
async def teams_ranking( 
   sort_by: Literal["titles", "wins", "goals_scored", "total_matches"] = Query(
      default="titles", 
      description="Criterio de Ordenación (por Orden)",
   ),
   min_matches: int = Query(
      default=3, 
      ge=1,
      description="Mínimo de Partidos jugados para aparecer: 3", 
   ), 
   team_services:TeamService = Depends(get_team_service),
) -> list[TeamStatsOut]:
   """
      Ranking histórico de selecciones ordenado por el criterio elegido.
      - **200**: Lista de stats ordenada.
   """
   return await team_services.get_ranking(sort_by=sort_by, min_matches=min_matches)

# ─── GET /teams/{initials} ────────────────────────────────────────────────────
@router.get("/{initials}", 
            response_model=TeamStatsOut, 
            summary="Detalles (Details) & Estadísticas (stats) de una Selección/Equipo")
async def get_team(initials:str, 
                   team_service:TeamService = Depends(get_team_service),) -> TeamStatsOut:
   """
      Retorna el detalle y estadísticas históricas de una selección por sus iniciales FIFA.
      - **200**: Stats del equipo.
      - **404**: Selección no encontrada.
   """
   return await team_service.get_team_stats(initials.upper())



# ─── PATCH /teams/{initials} ──────────────────────────────────────────────────
@router.get("/initials",
            response_model=TeamOut, 
            summary="Actualizar selección/equipo (admin) ",
            )
async def update_team(
   initials: str, 
   data: TeamUpdate,
   _:CurrentUser = Depends(require_editor_or_admin),  # noqa: B008
   team_service: TeamService = Depends(get_team_service)  # noqa: B008
) -> TeamOut:
   """
      Actualiza los datos de una selección nacional.
      - **200**: Equipo actualizado.
      - **401**: Token ausente o inválido.
      - **403**: Sin permisos suficientes.
      - **404**: Selección no encontrada.
   """
   return await team_service.update_team(initials=initials.upper(), data_update=data)


# ─── GET /teams/{initials}/matches ────────────────────────────────────────────
@router.get("/{initials}/matches",
            response_model=Paginated[MatchListOut], 
            status_code=status.HTTP_200_OK, 
            summary="Historial de partidos de una Selección/Equipos en un Mundial"
            )
async def team_matches(
   initials: str, 
   page: int = Query(default=1, ge=1), 
   page_size: int = Query(default=20, ge=1, len=100),
   year: int | None = Query(default=None, ge=1930, le=2030), 
   stage: str | None = Query(default=None, description="Group Stage | Final | semi-final"), 
   team_service: TeamService = Depends(get_team_service),  # noqa: B008
) -> Paginated[MatchListOut]:
   """
      Retorna el historial paginado de partidos de una selección.
      - **200**: Lista paginada de partidos.
      - **404**: Selección no encontrada.
   """
   return await team_service.get_matches(
      initials.upper(), page=page, page_size=page_size, year=year, stage=stage 
   )

# ─── GET /teams/{initials}/vs/{opponent} ─────────────────────────────────────
@router.get("/{initials}/head-to-head/{opponent}",
            response_model=HeadToHeadOut, 
            status_code=status.HTTP_200_OK,
            summary="Head-to-Head (Cara a cara) entre dos Selecciones",
            )
async def head_to_head(
   initials:str, 
   opponent:str, 
   team_service: TeamService = Depends(get_team_service),  # noqa: B008
   ) -> HeadToHeadOut:
   """
       Retorna el historial de enfrentamientos directos entre dos selecciones.
         - **200**: Stats head-to-head.
          - **404**: Una o ambas selecciones no encontradas.
   """
   return await team_service.head_to_head(initials.upper(), opponent.upper())