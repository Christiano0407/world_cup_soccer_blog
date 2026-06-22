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


# ─── GET /players/search ─────────────────────────────────────────────────────────────


# ─── GET /players/top-scorers ─────────────────────────────────────────────────────────────


# ─── GET /players/{name}/career ─────────────────────────────────────────────────────────────