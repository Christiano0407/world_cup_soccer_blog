"""
  # Endpoint: Tournaments: [/tournaments]
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.endpoints.deps import get_tournament_service
from app.core.security import CurrentUser, require_admin, require_editor_or_admin
from app.schemas.schemas import (
  MatchListOut,
  Paginated,
  TeamOut,
  TopScorerOut,
  TournamentIn,
  TournamentListOut,
  TournamentOut,
  TournamentUpdate,
)

from app.services.domain_analytics import TournamentService

router = APIRouter(prefix="/tournaments", tags=["Tournaments"])


# ─── GET /tournaments ─────────────────────────────────────────────────────────
@router.get(
  "/tournaments", 
  response_model=Paginated[TournamentListOut], 
  status_code=status.HTTP_200_OK,
  summary="Listar todas las ediciones del Mundial (Torneo)",
)
async def list_tournaments(
  page: int = Query(default=1, ge=1), 
  page_size: int = Query(default=20, ge=1, le=100), 
  year_from: int | None = Query(default=None, ge=1930, description="Desde el año..."),
  year_to: int | None = Query(default=None, le=2030, description="Hasta el AÑO..."), 
  tournament_service: TournamentService = Depends(get_tournament_service),
) -> Paginated[TournamentListOut]:
  """
    Lista todas las ediciones del Mundial FIFA paginadas.
      - **200**: Lista paginada de torneos.
  """
  return await tournament_service.list_tournaments(
    page=page, page_size=page_size, year_from=year_from, year_to=year_to
  )



# ─── POST /tournaments ────────────────────────────────────────────────────────


# ─── GET /tournaments/{year} ──────────────────────────────────────────────────


# ─── PATCH /tournaments/{year} ────────────────────────────────────────────────


# ─── DELETE /tournaments/{year} ───────────────────────────────────────────────


# ─── GET /tournaments/{year}/matches ──────────────────────────────────────────


# ─── GET /tournaments/{year}/top-scorers ──────────────────────────────────────


# ─── GET /tournaments/{year}/teams ────────────────────────────────────────────