"""
  # Endpoint teams [/api/v1/teams]
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


# ─── GET /teams/ranking  (debe ir ANTES de /{initials}) ──────────────────────


# ─── GET /teams/{initials} ────────────────────────────────────────────────────


# ─── PATCH /teams/{initials} ──────────────────────────────────────────────────


# ─── GET /teams/{initials}/matches ────────────────────────────────────────────


# ─── GET /teams/{initials}/vs/{opponent} ─────────────────────────────────────