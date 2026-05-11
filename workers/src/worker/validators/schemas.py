"""
workers/pipeline/validators/schemas.py
  - Pydantic v2 models para validar cada fila del CSV.
  - RawProductRow  → datos tal como llegan del CSV (todo strings)
  - CleanProductRow → datos después de validación y casteo
======================================
Pydantic v2 models para los 3 datasets FIFA World Cup.
- Pydantic [Type | Tipar los datos e validar]
- Pydantic, para los ORM - SQLSchemy (Ba) | Prisma en (Fr)

ARQUITECTURA DE SCHEMAS — dos capas por dataset:
 
  Raw{Dataset}Row   → datos tal como llegan del CSV (todo str | None)
                       W1 los produce, W2 los lee para validar.
                       Pydantic NO castea — solo mapea columnas a campos.
 
  Clean{Dataset}Row → datos después de validación y casteo a tipos reales.
                       W2 los produce, W3 los consume para insertar en public.*.
                       - Todos los campos tienen tipos Python correctos.
 
Datasets:
  - Winners  → wc_winners.csv  → public.tournaments
  - Matches  → wc_matches.csv  → public.matches
  - Players  → wc_players.csv  → public.match_players
"""

from __future__ import annotations

import re
from datetime import date 
from decimal import Decimal

from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

from worker.core.config import Settings
from worker.utils.helpers import (
  parse_bool,
  parse_decimal, 
  parse_date, 
  parse_int, 
  parse_datetime_csv,
  normalize_unique_sku,
  normalize_text,
  normalized_event_football_players_code, 
  normalize_initials, 
  normalized_lineup_type, 
  normalize_player_position,
  normalize_team_names
  
)
from worker.utils.constants import (
  MAX_ATTENDANCE_PER_MATCH, 
  MAX_GOALS_PER_TOURNAMENT, 
  MAX_SHIRT_NUMBER,
  MAX_WC_YEAR, 
  MIN_WC_YEAR, 
  TEAM_INITIALS_PATTERN, 
  VALID_EVENT_PREFIXES,
  VALID_LINEUP_TYPES,
  VALID_POSITIONS
)


## === Tipado con Pydantic (py) ===
# ═════════════════════════════════════════════════════════════════════════════
# WINNERS — wc_winners.csv → public.tournaments
# ═════════════════════════════════════════════════════════════════════════════

class RawWinnersRow(BaseModel): 
  """ 
    Schema de Winners Data Row: todo campo es str | None porque viene de un CSV.
    Pydantic NO intenta castear — solo mapea columnas a campos.
    #=============================#
    CSV row tal como llega del archivo wc_winners.csv.
    - Todo es str | None — sin casteo, sin validación de tipos.
    - W1 inserta en raw.wc_winners, W2 lee estas filas para validar.
 
    Columnas del CSV:
    - Year, Country, Winner, Runners-Up, Third, Fourth,
    - GoalsScored, QualifiedTeams, MatchesPlayed, Attendance
  """
  model_config = {"str_strip_whitespace": True}

  year: str | None = None
  country: str | None = None          # país anfitrión
  winner: str | None = None
  runners_up: str | None = None
  third: str | None = None
  fourth: str | None = None
  goals_scored: str | None = None
  qualified_teams: str | None = None
  matches_played: str | None = None
  attendance: str | None = None       # "590.549" — punto = miles en CSV


class CleanWinnersRow(BaseModel): 
  """
    - Winners row después de validación y casteo a tipos reales [type | Tipo de Dato].
    - W2 produce este modelo, W3 lo usa para upsert en public.tournaments.
  """

  year: Annotated[int, Field(ge=MIN_WC_YEAR, le=MAX_WC_YEAR)]
  host_country: str | None = None
  winner: str
  runners_up: str 
  third_place: str | None = None
  fourth_place: str | None = None
  goals_scored: Annotated[int, Field(ge=0, le=MAX_GOALS_PER_TOURNAMENT)]
  qualified_teams: Annotated[int, Field(ge=1, le=48)]
  matches_played: Annotated[int, Field(ge=1)]
  attendance_total: int | None = None

  @field_validator("winner", "runners_up", "host_country")
  @classmethod
  def not_empty(cls, v:str) -> str:
    if not v or not v.strip():
      raise ValueError("No puede estar Vacío")
    return v.strip()
  
  @model_validator(mode="after")
  def goals_coherent_with_match(self) -> CleanWinnersRow:
    """Los goles promedio deben ser >= 0.5 por partido (sanity check)."""
    avg = self.goals_scored / self.matches_played
    if avg < 0.5:
      raise ValueError(
        f"avg goals / match={avg:.2f} - parece correcto el número de goles & partidos"
        f"( num de goles: {self.goals_scored} goles en Num de Part: {self.matches_played} partido)"
      )
    return self



# ═════════════════════════════════════════════════════════════════════════════
# MATCHES — wc_matches.csv → public.matches
# ═════════════════════════════════════════════════════════════════════════════
   
class RawMatchesRow(BaseModel): 
  """ 
    - Schema de matches Data Row: todo campo es str | None porque viene de un CSV.
    - Pydantic NO intenta castear — solo mapea columnas a campos.
    # ======================================= #
    CSV row tal como llega de wc_matches.csv. Todo str | None.
 
    Columnas del CSV:
      Year, Datetime, Stage, Stadium, City,
      Home Team Name, Home Team Goals, Away Team Goals, Away Team Name,
      Win conditions, Attendance, Half-time Home Goals, Half-time Away Goals,
      Referee, Assistant 1, Assistant 2, RoundID, MatchID,
      Home Team Initials, Away Team Initials
  """
  pass


class CleanMatchesRow(BaseModel):
  """
    Matches row con tipos reales (Ya tipadas / Types de db), lista para insertar en public.matches.
  """
  pass

# ═════════════════════════════════════════════════════════════════════════════
# PLAYERS — wc_players.csv → public.match_players
# ═════════════════════════════════════════════════════════════════════════════

class RawPlayersRow(BaseModel): 
  """ 
    Schema de players Data Row: todo campo es str | None porque viene de un CSV.
    Pydantic NO intenta castear — solo mapea columnas a campos.
    ### =============================
    CSV row tal como llega de wc_players.csv. Todo str | None.
 
    - Columnas del CSV:
    - RoundID, MatchID, Team Initials, Coach Name, Line-up,
    - Shirt Number, Player Name, Position, Event
  """
  pass


class CleanPlayersRow(BaseModel):
  """
    Players row con tipos reales, lista para insertar en public.match_players.
      - Ya tipado (Tipos de datos / type)
  """
  pass