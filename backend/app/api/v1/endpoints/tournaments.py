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
@router.post(
  "/tournaments", 
  response_model=TournamentOut, 
  status_code=status.HTTP_201_CREATED, 
  summary="Crear Ediciones (Torneo) - (admin)",
)
async def create_tournament(
  data: TournamentIn, 
  _:CurrentUser = Depends(require_editor_or_admin),  # noqa: B008
  tournament_service:TournamentService = Depends(get_tournament_service),  # noqa: B008
) -> TournamentOut:
  """
    Crea una nueva edición del Mundial.
 
    - **201**: Torneo creado.
    - **401**: Token ausente o inválido.
    - **403**: Sin permisos suficientes.
    - **409**: Año ya registrado.
  """
  return await tournament_service.create_tournament(data)

# ─── GET /tournaments/{year} ──────────────────────────────────────────────────
@router.get("/{year}",
            response_model=TournamentOut, 
            status_code=status.HTTP_200_OK, 
            summary="Mundiales (torneo), detallado por año",
            )
async def get_year_tournament(
  year: int, 
  tournament_service: TournamentService = Depends(get_tournament_service),  # noqa: B008
) -> TournamentOut: 
  """
  Retorna el detalle completo de una edición del Mundial por su año.
    - **200**: Detalle del torneo.
    - **404**: Edición no encontrada.
  """ 
  return await tournament_service.get_tournament(year)

# ─── PATCH /tournaments/{year} ────────────────────────────────────────────────
@router.patch(
  "/{year}",
  response_model=TournamentOut, 
  summary=" Actualizar edición - Mundial por año (admin)", 
)
async def update_tournament(
  year: int, 
  data: TournamentUpdate, 
  _:CurrentUser = Depends(get_tournament_service),  # noqa: B008
  tournament_service: TournamentService = Depends(get_tournament_service),  # noqa: B008
) -> TournamentOut:
  """
     Actualiza datos de una edición del Mundial.
      - **200**: Torneo actualizado.
      - **401**: Token ausente o inválido.
      - **403**: Sin permisos suficientes.
      - **404**: Edición no encontrada.
  """
  return await tournament_service.update_tournament(year, data)

# ─── DELETE /tournaments/{year} ───────────────────────────────────────────────
@router.delete(
  "/{year}", 
  status_code=status.HTTP_204_NO_CONTENT,
  summary=" Eliminar edición mundialista (Torneo) "
)
async def delete_tournament(
  year: int, 
  _:CurrentUser = Depends(get_tournament_service),  # noqa: B008
  tournament_service: TournamentService = Depends(get_tournament_service),  # noqa: B008
) -> None:
  """
    Elimina una edición del Mundial.
    **⚠ ADVERTENCIA**: Solo usar si no tiene partidos asociados.
    Los datos históricos no deben eliminarse.
    - **204**: Torneo eliminado.
    - **401**: Token ausente o inválido.
    - **403**: Rol insuficiente — requiere **admin** (no editor).
    - **404**: Edición no encontrada.
  """
  await tournament_service.delete_tournament(year)

# ─── GET /tournaments/{year}/matches ──────────────────────────────────────────
@router.get("{year}/matches", 
            response_model=Paginated[MatchListOut], 
            status_code=status.HTTP_200_OK,
            summary=" Partidos jugados por edición (Torneo) | Por año",
            )
async def tournament_matches(
    year: int, 
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    stage: str | None = Query(
      default=None, 
      description="filtrar por fase (Etapas del torneo): Group 1, Final, etc."
      ),
    tournament_service: TournamentService = Depends(get_tournament_service), 
    ) -> Paginated[MatchListOut]:
  """
    Retorna todos los partidos de una edición del Mundial, paginados.

    - **200**: Lista paginada de partidos.
    - **404**: Edición no encontrada.
  """
  return await tournament_service.get_matches(year=year, page=page, page_size=page_size, stage=stage)


# ─── GET /tournaments/{year}/top-scorers ──────────────────────────────────────


# ─── GET /tournaments/{year}/teams ────────────────────────────────────────────