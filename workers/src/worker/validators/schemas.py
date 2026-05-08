"""
workers/pipeline/validators/schemas.py
  - Pydantic v2 models para validar cada fila del CSV.
  - RawProductRow  → datos tal como llegan del CSV (todo strings)
  - CleanProductRow → datos después de validación y casteo
"""

from __future__ import annotations

import re
from datetime import date 
from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, Field, field_validator, model_validator

from worker.core.config import Settings
from worker.utils.constants import DatasetKind, DATASET_CONFIG
from worker.utils.helpers import (
  normalize_unique_sku,
  normalize_text,
  parse_bool,
  parse_decimal, 
  parse_date, 
  parse_int
)


## === Tipado con Pydantic (py) ===
class WinnersRow(BaseModel): 
  """ 
    Schema de Winners Data Row: todo campo es str | None porque viene de un CSV.
    Pydantic NO intenta castear — solo mapea columnas a campos.
  """
  pass


class TournamentsRow(BaseModel): 
  """ 
    Schema de Winners Data Row: todo campo es str | None porque viene de un CSV.
    Pydantic NO intenta castear — solo mapea columnas a campos.
  """
  tournament_id: str | None = None
  year: Annotated[int, Field(ge=1920, le=2018)]
  host_country: str | None = None
  winner: str | None = None
  runners_up: str | None 
  third_place: str | None
  fourth_place: str | None
  goals_scored: Annotated[int, Field(ge=0)]
  qualified_teams: Annotated[int, Field(ge=0)]
  matches_played: int | None
  attendance_total: int | None

  
class Matches(BaseModel): 
  """ 
    Schema de matches Data Row: todo campo es str | None porque viene de un CSV.
    Pydantic NO intenta castear — solo mapea columnas a campos.
  """
  pass

class Players(BaseModel): 
  """ 
    Schema de players Data Row: todo campo es str | None porque viene de un CSV.
    Pydantic NO intenta castear — solo mapea columnas a campos.
  """
  pass