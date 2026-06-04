"""
  Pydantic v2 schemas — mirrors the OpenAPI contract exactly.
  ("Los esquemas de Pydantic v2 (Tipar Datos) reflejan exactamente el contrato OpenAPI")
  - "Pydantic es la biblioteca de validación de datos más popular en Python, diseñada para 
    validar, convertir y serializar datos estructurados utilizando las anotaciones de tipo (type hints)
     nativas del lenguaje."
  # =============================================== #
    - " En Pydantic v2, model_config = ConfigDict(from_attributes=True) es una configuración que permite a
      los modelos validar y construir instancias a partir de objetos Python (como modelos ORM) en lugar 
      de únicamente diccionarios "
"""  # noqa: E501

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

T = TypeVar("T")


# ─── Shared ───────────────────────────────────────────────────────────────────

class ErrorOut(BaseModel):
  detail: str


class HealthOut(BaseModel):
  status: Literal["ok", "degraded", "down"]
  version: str
  environment: str


class ComponentHealthOut(BaseModel):
  component: str
  status: Literal["ok", "down"]
  latency_ms: float | None = None
  
  
class Paginated[T](BaseModel):
  items: list[T]
  total: int 
  page: int
  page_size: int
  pages: int


# ─── Auth ─────────────────────────────────────────────────────────────────────

class RegisterIn(BaseModel):
  email: EmailStr
  password: str = Field(min_length=8, max_length=128)
  display_name: str | None = Field(default=None, max_length=80)

  @field_validator("password")
  @classmethod
  def password_has_digit(cls, v:str) -> str:
    if not any(c.isdigit() for c in v):
      raise ValueError("La Contraseña debe contener al menos un Dígito")
    return v


class LoginIn(BaseModel):
  email: EmailStr
  password: str


class UserOut(BaseModel):
  model_config = ConfigDict(from_attributes=True) # Connect To ORM

  user_id: uuid.UUID
  email: EmailStr
  display_name: str | None = None
  role: Literal["admin", "editor", "reader"]
  is_active: bool
  created_at: datetime


class UserUpdateIn(BaseModel):
  display_name:str | None = Field(default=None, max_length=80)


class ChangePasswordIn(BaseModel):
  current_password: str
  new_password: str = Field(min_length=8, max_length=128)
  

# ─── Tournaments ──────────────────────────────────────────────────────────────

class TournamentOut(BaseModel):
  model_config = ConfigDict(from_attributes=True) # Connect To ORM

  tournament_id: int
  year: int
  host_country: str
  winner: str
  runners_up: str
  third_place: str | None = None
  fourth_place: str | None = None
  goals_scored: int
  qualified_teams: int
  matches_played: int
  attendance_total: int | None = None
  avg_goals_per_match: float | None = None


class TournamentListOut(BaseModel): 
  model_config = ConfigDict(from_attributes=True) # Connect To ORM

  tournament_id: int
  year: int
  host_country: str
  winner: str
  goals_scored: int
  matches_played: int


class TournamentIn(BaseModel):
  year:int=Field(ge=1930, le=2030)
  host_country:str=Field(max_length=100)
  winner:str=Field(max_length=100)
  runners_up:str=Field(max_length=100)
  third_place:str | None = None
  fourth_place:str | None = None
  goals_scored:int = Field(ge=0)
  qualified_teams: int = Field(ge=1, le=48)
  matches_played: int = Field(ge=1)
  attendance_total: int | None = None


class TournamentUpdate(BaseModel):
  winner: str | None = None
  runners_up: str | None = None
  goals_scored: int | None = Field(default=None, ge=0)
  attendance_total: int | None = None


# ─── Teams ────────────────────────────────────────────────────────────────────
class TeamOut(BaseModel):
  model_config = ConfigDict(from_attributes=True) # Connect To ORM
  
  team_id: int
  initials: str
  name: str
  confederation: str | None = None
  fifa_code: str | None = None
  active: bool


class TeamStatsOut(BaseModel):
    initials: str
    name: str
    confederation: str | None = None
    tournaments_played: int = 0
    titles: int = 0
    runner_ups: int = 0
    total_matches: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_scored: int = 0
    goals_conceded: int = 0
    goal_difference: int = 0
    win_rate_pct: float = 0.0
 
 
class TeamIn(BaseModel):
    initials: str = Field(min_length=2, max_length=3)
    name: str = Field(max_length=100)
    confederation: str | None = None
    active: bool = True
 
 
class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    confederation: str | None = None
    active: bool | None = None

# ─── Matches ─────────────────────────────────────────────────────────────────
class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True) # Connect To ORM
 
    match_id: int
    tournament_id: int
    year: int
    stage: str
    match_datetime: datetime
    stadium: str | None = None
    city: str | None = None
    home_team_initials: str
    away_team_initials: str
    home_team_name: str | None = None
    away_team_name: str | None = None
    home_goals: int
    away_goals: int
    ht_home_goals: int | None = None
    ht_away_goals: int | None = None
    win_conditions: str | None = None
    attendance: int | None = None
    referee: str | None = None
 
 
class MatchListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True) # Connect To ORM
 
    match_id: int
    year: int
    stage: str
    match_datetime: datetime
    home_team_initials: str
    away_team_initials: str
    home_goals: int
    away_goals: int
 
 
# ─── Players ─────────────────────────────────────────────────────────────────

class PlayerAppearanceOut(BaseModel): 
  model_config = ConfigDict(from_attributes=True) # Connect To ORM

  player_match_id: int
  match_id: int
  team_initials: str
  coach_name: str | None = None
  lineup_type: Literal["S", "N"]
  shirt_number: int | None = None
  player_name: str
  position: Literal["GK", "DF", "MF", "FW"] | None = None
  event_code: str | None = None


class TopScorerOut(BaseModel):
    player_name: str
    team_initials: str
    goals: int
    own_goals: int = 0
    matches_played: int
    first_wc: int
    last_wc: int
    editions: int
 
 
class PlayerCareerOut(BaseModel):
    player_name: str
    team_initials: str
    total_appearances: int
    starts: int
    substitutions: int
    goals: int
    yellow_cards: int
    red_cards: int
    editions: list[int]



# ─── Admin ────────────────────────────────────────────────────────────────────

class AdminUserOut(BaseModel): 
   model_config = ConfigDict(from_attributes=True) # Connect To ORM

   user_id: uuid.UUID
   email: EmailStr
   display_name: str | None = None
   role: Literal["admin", "editor", "reader"] # Define Types
   is_active: bool
   created_at: datetime
   update_at: datetime


class AdminUserUpdate(BaseModel):
   role: Literal["admin", "editor", "reader" ] # Define Types
   is_active: bool | None = None


class EtlTriggerIn(BaseModel): 
   dataset: Literal["all", "winners", "matches", "players"] = "all" # Define Types
 