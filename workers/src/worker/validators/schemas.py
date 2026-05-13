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
        f"avg={avg:.2f} goles/partido — parece anormalmente bajo"
        f" ({self.goals_scored} goles en {self.matches_played} partidos)"
      )
    return self


# ═════════════════════════════════════════════════════════════════════════════
# TEAMS — extracted from matches/players → public.teams
# ═════════════════════════════════════════════════════════════════════════════

class CleanTeamRow(BaseModel):
    """
    Team row after extraction and validation from matches/players data.
    W3 produces this model for upsert into public.teams.
    """
    initials: str
    name: str | None = None
    confederation: str | None = None

    @field_validator("initials")
    @classmethod
    def validate_initials(cls, v: str) -> str:
        val = normalize_initials(v)
        if val is None:
            raise ValueError(f"Iniciales Inválidas: '{v}' - deben ser 2-3 letras Mayúsculas")
        return val


# ═════════════════════════════════════════════════════════════════════════════
# ROUNDS — extracted from matches → public.rounds
# ═════════════════════════════════════════════════════════════════════════════

class CleanRoundRow(BaseModel):
    """
    Round row after extraction and validation from matches data.
    W3 produces this model for upsert into public.rounds.
    """
    round_id: Annotated[int, Field(ge=1)]
    tournament_id: Annotated[int, Field(ge=1)]
    round_name: str


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
  model_config = {
    "str_strip_whitespace": True
  }
  year: str | None = None
  datetime: str | None = None  # "13 Jul 1930 - 15:00 "
  stage: str | None = None
  stadium: str | None = None
  city: str | None = None
  home_team_name: str | None = None
  home_team_goals: str | None = None
  away_team_name: str | None = None
  away_team_goals: str | None = None
  win_conditions: str | None = None  # vacío = tiempo normal
  attendance: str | None = None
  ht_home_goals: str | None = None # half-time
  ht_away_goals: str | None = None
  referee: str | None = None
  assistant_1: str | None = None
  assistant_2: str | None = None
  round_id: str | None = None
  match_id: str | None = None
  home_team_initials: str | None = None
  away_team_initials: str | None = None


class CleanMatchesRow(BaseModel):
  """
    Matches row con tipos reales (Ya tipadas / Types de db), lista para insertar en public.matches.
      - Datos ya tipados (types / ORM) para DB & Storage s3
  """

  match_id: Annotated[int, Field(ge=1)]
  tournament_id: Annotated[int, Field(ge=1)]
  round_id: Annotated[int, Field(ge=1)]
  year: Annotated[int, Field(ge=MIN_WC_YEAR, le=MAX_WC_YEAR)]
  match_datetime: str | None = None
  stage: str 
  stadium: str | None = None
  city: str | None = None
  home_goals: Annotated[int, Field(ge=0)]
  away_goals: Annotated[int, Field(ge=0)]
  win_conditions: str | None = None
  attendance: Annotated[int, Field(ge=0, le=MAX_ATTENDANCE_PER_MATCH)] | None = None
  ht_home_goals: Annotated[int, Field(ge=0)] | None = None   # half-time
  ht_away_goals: Annotated[int, Field(ge=0)] | None = None
  referee: str | None = None
  assistant_1: str | None = None
  assistant_2: str | None = None
  home_team_initials: str 
  away_team_initials: str 

  @field_validator("home_team_initials", "away_team_initials")
  @classmethod
  def validator_initials(cls, v:str) -> str:
    val_initials = v.strip().upper()
    if not re.match(TEAM_INITIALS_PATTERN, val_initials):
      raise ValueError(f"Iniciales Inválidas:'{val_initials}' - debe de ser entre 2-3 letras Mayúsculas (BRA).")  # noqa: E501
    return val_initials
  
  @model_validator(mode="after")
  def team_different(self) -> CleanMatchesRow:
    """Un equipo no puede jugar contra sí mismo."""
    if self.home_team_initials == self.away_team_initials:
      raise ValueError(
        f"Lo siento. 'home' & 'Away', no pueden ser el mismo equipo. {self.home_team_initials}"
      )
    return self
  
  @model_validator(mode="after")
  def halftime_goals_not_ft(self) -> CleanMatchesRow:
    """Los goles al HT(halftime/medio tiempo) no pueden superar los goles totales."""
    if self.ht_home_goals is not None and self.ht_home_goals > self.home_goals: 
      raise ValueError(
        f"ht_home_goals={self.ht_home_goals} (Goles al medio tiempo) > home_goals={self.home_goals} (goles totales  ´x´ partido)"  # noqa: E501
      )
    if self.ht_away_goals is not None and self.ht_away_goals > self.away_goals: 
      raise ValueError(
        f"ht_away_goals={self.ht_away_goals} (Goles al medio tiempo) > home_goals={self.away_goals} (goles totales  ´x´ partido)"  # noqa: E501
      )
    return self
  
  @model_validator(mode="after")
  def ht_both_goals_or_none(self) -> CleanMatchesRow:
     """Los goles de HT(Halftime/medio tiempo) son ambos None (No hay goles) o ambos int (Ya hicieron goles) — nunca uno solo."""  # noqa: E501
     if (self.ht_home_goals is None) != (self.ht_away_goals is None):
       raise ValueError("HT(Halftime/medio tiempo) son ambos None (No hay goles) o ambos int (Ya hicieron goles) — nunca uno solo.")  # noqa: E501
     return self


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
  model_config = {
    "str_strip_whitespace": True
  }

  round_id: str | None = None
  match_id: str | None = None
  team_initials: str | None = None
  coach_name: str | None = None
  line_up: str | None = None        # 'S' (Start) & 'N' (Non-started)
  shirt_number: str | None = None   # "0" (Sin asignar en el CSV)
  player_name: str | None = None
  position: str | None = None       # "GK", "DF", "MF", "FW"
  event: str | None = None          # G, G40, Y, R, OG, SY...


class CleanPlayersRow(BaseModel):
  """
    Players row con tipos reales, lista para insertar en public.match_players.
      - Ya tipado (Tipos de datos / type)
  """
  round_id: Annotated[int, Field(ge=1)]
  match_id: Annotated[int, Field(ge=1)]
  team_initials: str
  coach_name: str | None = None
  lineup_type: str                      # 'S' (Start) & 'N' (Non-started)
  shirt_number: Annotated[int, Field(ge=1, le=MAX_SHIRT_NUMBER)] | None = None   # "0" (Sin asignar en el CSV)  # noqa: E501
  player_name: str
  position: str | None = None       # "GK", "DF", "MF", "FW"
  event_code: str | None = None          # G, G40, Y, R, OG, SY...


  @field_validator("team_initials")
  @classmethod
  def validate_initials(cls, v:str) -> str:
    """ Validar las iniciales del Team (Selección) en Mayúsculas"""
    val_initials = normalize_initials(v)
    if val_initials is None:
      raise ValueError(f"Iniciales Inválidas: '{v}' - Mayúsculas")
    return val_initials
  
  @field_validator("lineup_type")
  @classmethod
  def validate_init_line_up(cls, v:str) -> str:
    """ Validar si inician el juego o no ['S' o 'N']"""
    val_line_up = normalized_lineup_type(v)
    if val_line_up is None:
      raise ValueError(f"Lineup type Invalid (Tipo de Alineación es Inválida): '{v}'. Debe ser: 'S' or 'N'.")  # noqa: E501
    return val_line_up
  
  @field_validator("position")
  @classmethod
  def validate_position_player(cls, v:str | None) -> str | None:
    """ Validamos posición de cada jugar (saber de qué juegan)"""
    val_position = normalize_player_position(v)
    if v is None: 
      return None
    return val_position
  
  @field_validator("player_name")
  @classmethod
  def player_name_not_empty(cls, v:str) -> str:
    """ Validar que el Nombre (Name), existe dentro del torneo | No está vacío o 'falso nombre' """
    if not v or not v.strip():
      raise ValueError("player_name (Nombre del jugador), no puede estar vacío")
    return v.strip()
  
  @field_validator("event_code")
  @classmethod
  def valid_event_player_game(cls, v:str | None) -> str | None:
    """ Validar los Eventos (tarjetas, goles...etc)"""
    if v is None:
      return None
    valid_event_code = normalized_event_football_players_code(v)
    if valid_event_code is None:
      return None
    # Validar por 'prefijo': G, G40, Y, R, OG, SY, etc...
    if not any(valid_event_code.startswith(p) for p in VALID_EVENT_PREFIXES):
      return None
    return valid_event_code
  

  @model_validator(mode="after")
  def shirt_zero_to_none(self) -> CleanPlayersRow:
      """El CSV usa shirt_number=0 para 'sin asignar' → convertir a None."""
      # Este caso se maneja en W2 antes de crear el schema
      return self