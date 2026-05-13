"""
workers/pipeline/validators/rules.py
  - Reglas de negocio reutilizables, separadas del schema Pydantic (type | tipar & validar datos).
  - Vamos usar el tipado (ya hicimos)
  - Estas reglas pueden cambiar sin modificar el schema de datos.
  - Son reglas de Negocio (Lógica de Negocio)
=====================================
Reglas de negocio reutilizables, separadas del schema Pydantic.
 
RESPONSABILIDAD: Validar que los datos tienen sentido en el contexto
del negocio FIFA — más allá de que tengan el tipo correcto.
  - Datos de mis DB - Storage s3 | Datasets
 
ARQUITECTURA:
  - ValidationError  → un error individual con campo + mensaje + severidad
  - ValidationResult → resultado de validar una fila (lista de errores + fila limpia)
  - validate_*_row() → función principal por dataset — llamada por W2
 
FLUJO:
  W2 llama validate_winners_row(raw_row) / validate_matches_row() / validate_players_row()
  → Retorna ValidationResult
  → Si result.is_valid → W3 usa result.clean_row para insertar en public.*
  → Si not result.is_valid → W2 inserta en raw.dead_letter
"""
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from worker.validators.schemas import (
  CleanMatchesRow, 
  CleanPlayersRow,
  CleanRoundRow,
  CleanTeamRow,
  CleanWinnersRow,
  RawMatchesRow, 
  RawPlayersRow, 
  RawWinnersRow, 
)

from worker.utils.helpers import (
  parse_bool,
  parse_decimal, 
  parse_date, 
  parse_int, 
  parse_attendance,
  parse_datetime_csv,
  normalize_unique_sku,
  normalize_text,
  normalized_event_football_players_code, 
  normalize_initials, 
  normalized_lineup_type, 
  normalize_player_position,
  normalize_team_names,
  
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
  VALID_POSITIONS,
)

# ─────────────────────────────────────────────────────────────────────────────
# ESTRUCTURAS DE RESULTADO
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class ValidationError:
  """ Validar que tenemos errores dentro de las Filas (Row), de nuestras DB - CSV (Dataset)"""
  field: str              # nombre del campo que falló
  code: str               # código de error — usado en dead_letter._error_code
  message: str            # descripción legible — va a dead_letter._error_detail
  severity: str = "error" # "error" (rechaza la fila) | "warning" (log pero continúa)

  def __str__(self) -> str:
    return f"[{self.severity.upper()} | {self.field}: {self.code} - {self.message}]"
 

@dataclass
class ValidationResult: 
  """  
  Resultado de validar una fila del CSV [Dataset] 
    - Coincidan las filas con los datos & Tipados de datos.
 
    Attributes:
        is_valid:   True si la fila puede cargarse en public.* (sin errores graves)
        clean_row:  La fila con tipos reales (solo si is_valid=True)
        errors:     Lista de errores y warnings encontrados
        raw_row_id: ID de la fila en raw.* (para el dead_letter)
  """
  is_valid: bool
  clean_row: CleanWinnersRow | CleanMatchesRow | CleanPlayersRow | None
  errors: list[ValidationError] = field(default_factory=list)
  raw_row_id: int | None = None

  @property
  def has_warning(self) -> bool:
    return any(e.severity == "warning" for e in self.errors)
  
  @property
  def error_code(self) -> list[str]:
    return [e.code for e in self.errors if e.severity == "error"]
  
  @property
  def first_error_code(self) -> str | None:
    codes = self.error_code
    return codes[0] if codes else None
  
  @property
  def error_detail(self) -> str: 
    return " | ".join(str(e) for e in self.errors)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS INTERNOS DE VALIDACIÓN (_)
# ─────────────────────────────────────────────────────────────────────────────

def _err(field: str, code: str, message: str) -> ValidationError:
  return ValidationError(field=field, code=code, message=message, severity="error")

def _warn(field: str, code: str, message: str) -> ValidationError:
  return ValidationError(field=field, code=code, message=message, severity="warning")

def _invalid(errors: list[ValidationError], raw_row_id: int | None = None) -> ValidationResult:
  return ValidationResult(is_valid=False, clean_row=None, errors=errors, raw_row_id=raw_row_id)

def _valid(
    clean_row: CleanWinnersRow | CleanMatchesRow | CleanPlayersRow,
    warnings: list[ValidationError] | None = None,
    raw_row_id: int | None = None
) -> ValidationResult:
    return ValidationResult(
          is_valid=True,
          clean_row=clean_row, 
          errors=warnings or [],
          raw_row_id=raw_row_id,
    )

# ─────────────────────────────────────────────────────────────────────────────
# REGLAS DE NEGOCIO: WINNERS
# Fuente: wc_winners.csv [Dataset] → valida antes de cargar en public.tournaments [DB & Storage]
# ─────────────────────────────────────────────────────────────────────────────
def validate_winners_row(
    raw: RawWinnersRow,
    raw_row_id: int | None = None,
) -> ValidationResult:
  """
    - Valida y castea una fila de wc_winners.csv.
    - Retorna ValidationResult con CleanWinnersRow si es válida.
  """
  errors : list[ValidationError] = []

  # ---- year ---- #
  year = parse_int(raw.year)
  if year is None:
    errors.append(_err("year", "MISSING_YEAR", F"'year', vacío o no parceable: '{raw.year}'"))
  elif not (MIN_WC_YEAR <= year <= MAX_WC_YEAR): 
     errors.append(_err("year", "INVALID_YEAR_RANGE (1930 - 2030)",
                           f"year={year} fuera del rango [{MIN_WC_YEAR}, {MAX_WC_YEAR}]"))
     
  # ---- host_country ---- #
  host_country = normalize_text(raw.country, max_length=100)
  if not host_country:
    errors.append(_err("country", "MISSING_HOST_WINNER", "No tenemos campeón / No existe información de quién fué el País Campeón del Mundo de ese año"))  # noqa: E501

  # ---- winners ---- #
  winners = normalize_text(raw.winner, max_length=100)
  if not winners:
    errors.append(_err("winner", "MISSING_WINNER", "No tenemos ganador - campeón"))  # noqa: E501

  # ---- runners_up ---- #
  runners_up = normalize_text(raw.runners_up, max_length=100)
  if not runners_up:
    errors.append(_err("runners_up", "MISSING_RUNNERS_UP", "Subcampeón Vacío"))

  # ---- third & fourth place (opecionales - warning si ambos están vacíos) ---- #
  third = normalize_text(raw.third, max_length=100)
  fourth = normalize_text(raw.fourth, max_length=100)

  if not third and not fourth:
    errors.append(
      _warn("third/fourth", "MISSING_PODIUM", "Podium Incompleto: No tenemos ni tercer ni cuarto lugar.")  # noqa: E501
    )

  # ---- goals_scored ---- #
  goals  = parse_int(raw.goals_scored)
  if goals is None:
    errors.append(_err("goals_scored", "EMPTY_GOALS_SCORED", f"No tiene goles anotados durante el torneo de fútbol mundial: {raw.goals_scored}"))  # noqa: E501
  elif goals < 0:
    errors.append(_err("goals_scored", "NEGATIVE_GOALS_SCORED", F"No puede tener goles negativos.Menor a cero (Don't have Negative Scored): goals_scored={goals} < 0"))  # noqa: E501

  # ---- qualified_teams ---- #
  qualified = parse_int(raw.qualified_teams)
  if qualified is None:
    errors.append(_err("qualified_teams", "MISSING_QUALIFIED_TEAMS", f"Lo sentimos pero, éste equipo no está Clasificado al Mundial. Clasificados: {raw.qualified_teams}"))  # noqa: E501
  elif qualified < 1 or qualified > 48:
    errors.append(_err("qualified_teams", "NEGATIVE_QUALIFIED_TEAMS", f"No puede haber menor a 1 Selección o más de 48 Clasificadas para el Mundial: {qualified} 1 - 48"))  # noqa: E501

  # ── matches_played ─────────────────────────────────────────────
  matches = parse_int(raw.matches_played)
  if matches is None:
    errors.append(_err("matches_played", "MISSING_MATCHES_PLAYED", 
      F"No Tenemos Registro de Partidos Jugados en el certamen mundialístico: {raw.matches_played}"))  # noqa: E501
  elif matches < 1:
    errors.append(_err("matches_played", "INVALID_MATCHES_PLAYED", F"No puede haber jugado ningún juego o 1. Se tienen que cumplir las reglas de el certamen mundialístico: {matches} - < 1 | 3 (fase de grupo)"))  # noqa: E501

  # ── attendance (opcional — punto como separador de miles) ──────
  attendance = parse_attendance(raw.attendance)
  if raw.attendance and attendance is None:
    errors.append(_warn("attendance", "UNPARSEABLE_ATTENDANCE", F"Attendance no parseable: {raw.attendance} - se guardará como NULL"))  # noqa: E501

  # ── Regla de negocio: avg goals coherente ─────────────────────
  # [Notaciones Verificadas por Partido (avg)] #
  if goals is not None and matches is not None and matches > 0: 
      avg = goals / matches 
      if avg < 0.3:
        errors.append(_warn("goals_scored", "LOG_AVG_MATCHES", f"avg={avg:.2f} goles/partidos - parece bajo (nivel de anotaciones. Verificar)"))  # noqa: E501
      if avg > 8.0:
        errors.append(_warn("goals_scored", "HIGH_SCORED_GOALS", F"avg={avg:.2f} goles/partidos - parece alto el nivel de anotaciones. Verificar"))  # noqa: E501


  # ── Si hay errores graves → rechazar ──────────────────────────
  fatal = [e for e in errors if e.severity == "error"]
  if fatal: 
    return _invalid(errors, raw_row_id)

  # ── Construir fila limpia ──────────────────────────────────────
  clean = CleanWinnersRow(
      year=year,                      # type: ignore[arg-type]
      host_country=host_country,      # type: ignore[arg-type]
      winner=winners,                  # type: ignore[arg-type]
      runners_up=runners_up,          # type: ignore[arg-type]
      third_place=third,
      fourth_place=fourth,
      goals_scored=goals,             # type: ignore[arg-type]
      qualified_teams=qualified,      # type: ignore[arg-type]
      matches_played=matches,         # type: ignore[arg-type]
      attendance_total=attendance,
  )
  return _valid(clean, warnings=[e for e in errors if e.severity == "warning"], raw_row_id=raw_row_id)  # noqa: E501


# ─────────────────────────────────────────────────────────────────────────────
# REGLAS DE NEGOCIO: MATCHES
# Fuente: wc_matches.csv → valida antes de cargar en public.matches
# ─────────────────────────────────────────────────────────────────────────────

def validate_matches_row(
    raw: RawMatchesRow,
    tournament_id: int,
    raw_row_id: int | None = None,
) -> ValidationResult:
    errors: list[ValidationError] = []

    # ---- match_id ---- #
    match_id = parse_int(raw.match_id)
    if match_id is None or match_id < 1:
        errors.append(_err("match_id", "INVALID_MATCH_ID",
                           f"MatchID inválido: '{raw.match_id}'"))

    # ---- tournament_id ---- #
    if tournament_id < 1:
        errors.append(_err("tournament_id", "INVALID_TOURNAMENT_ID",
                           f"TournamentID inválido: {tournament_id}"))

    # ---- round_id ---- #
    round_id = parse_int(raw.round_id)
    if round_id is None or round_id < 1:
        errors.append(_err("round_id", "INVALID_ROUND_ID",
                           f"RoundID inválido: '{raw.round_id}'"))

    # ---- year ---- #
    year = parse_int(raw.year)
    if year is None:
        errors.append(_err("year", "MISSING_YEAR",
                           f"Year vacío o no parseable: '{raw.year}'"))
    elif not (MIN_WC_YEAR <= year <= MAX_WC_YEAR):
        errors.append(_err("year", "INVALID_YEAR_RANGE",
                           f"year={year} fuera del rango [{MIN_WC_YEAR}, {MAX_WC_YEAR}]"))

    # ---- match_datetime ---- #
    match_dt = parse_datetime_csv(raw.datetime)
    match_datetime = str(match_dt) if match_dt else None

    # ---- stage ---- #
    stage = normalize_text(raw.stage, max_length=60)
    if not stage:
        errors.append(_err("stage", "MISSING_STAGE", "Stage vacío"))

    # ---- stadium ---- #
    stadium = normalize_text(raw.stadium, max_length=100)

    # ---- city ---- #
    city = normalize_text(raw.city, max_length=100)

    # ---- home_goals ---- #
    home_goals = parse_int(raw.home_team_goals)
    if home_goals is None or home_goals < 0:
        errors.append(_err("home_goals", "INVALID_HOME_GOALS",
                           f"Home goals inválido: '{raw.home_team_goals}'"))

    # ---- away_goals ---- #
    away_goals = parse_int(raw.away_team_goals)
    if away_goals is None or away_goals < 0:
        errors.append(_err("away_goals", "INVALID_AWAY_GOALS",
                           f"Away goals inválido: '{raw.away_team_goals}'"))

    # ---- win_conditions ---- #
    win_conditions = normalize_text(raw.win_conditions, max_length=200)

    # ---- attendance ---- #
    attendance = parse_attendance(raw.attendance)
    if raw.attendance and attendance is None:
        errors.append(_warn("attendance", "UNPARSEABLE_ATTENDANCE",
                            f"Attendance no parseable: '{raw.attendance}'"))

    # ---- ht_home_goals ---- #
    ht_home_goals = parse_int(raw.ht_home_goals)

    # ---- ht_away_goals ---- #
    ht_away_goals = parse_int(raw.ht_away_goals)

    # ---- referee ---- #
    referee = normalize_text(raw.referee, max_length=100)

    # ---- assistant_1 ---- #
    assistant_1 = normalize_text(raw.assistant_1, max_length=100)

    # ---- assistant_2 ---- #
    assistant_2 = normalize_text(raw.assistant_2, max_length=100)

    # ---- home_team_initials ---- #
    home_team_initials = normalize_initials(raw.home_team_initials)
    if not home_team_initials:
        errors.append(_err("home_team_initials", "MISSING_HOME_INITIALS",
                           f"Home team initials vacío: '{raw.home_team_initials}'"))

    # ---- away_team_initials ---- #
    away_team_initials = normalize_initials(raw.away_team_initials)
    if not away_team_initials:
        errors.append(_err("away_team_initials", "MISSING_AWAY_INITIALS",
                           f"Away team initials vacío: '{raw.away_team_initials}'"))

    # ---- Si hay errores graves → rechazar ---- #
    fatal = [e for e in errors if e.severity == "error"]
    if fatal:
        return _invalid(errors, raw_row_id)

    # ---- Construir fila limpia ---- #
    clean = CleanMatchesRow(
        match_id=match_id,
        tournament_id=tournament_id,
        round_id=round_id,
        year=year,
        match_datetime=match_datetime,
        stage=stage,
        stadium=stadium,
        city=city,
        home_goals=home_goals,
        away_goals=away_goals,
        win_conditions=win_conditions,
        attendance=attendance,
        ht_home_goals=ht_home_goals,
        ht_away_goals=ht_away_goals,
        referee=referee,
        assistant_1=assistant_1,
        assistant_2=assistant_2,
        home_team_initials=home_team_initials,
        away_team_initials=away_team_initials,
    )
    return _valid(clean, warnings=[e for e in errors if e.severity == "warning"], raw_row_id=raw_row_id)  # noqa: E501


# ─────────────────────────────────────────────────────────────────────────────
# REGLAS DE NEGOCIO: PLAYERS
# Fuente: wc_players.csv → valida antes de cargar en public.match_players
# ─────────────────────────────────────────────────────────────────────────────

def validate_players_row(
    raw: RawPlayersRow,
    raw_row_id: int | None = None,
) -> ValidationResult:
    errors: list[ValidationError] = []

    # ---- round_id ---- #
    round_id = parse_int(raw.round_id)
    if round_id is None or round_id < 1:
        errors.append(_err("round_id", "INVALID_ROUND_ID",
                           f"RoundID inválido: '{raw.round_id}'"))

    # ---- match_id ---- #
    match_id = parse_int(raw.match_id)
    if match_id is None or match_id < 1:
        errors.append(_err("match_id", "INVALID_MATCH_ID",
                           f"MatchID inválido: '{raw.match_id}'"))

    # ---- team_initials ---- #
    team_initials = normalize_initials(raw.team_initials)
    if not team_initials:
        errors.append(_err("team_initials", "MISSING_TEAM_INITIALS",
                           f"Team initials vacío: '{raw.team_initials}'"))

    # ---- coach_name ---- #
    coach_name = normalize_text(raw.coach_name, max_length=100)

    # ---- lineup_type ---- #
    lineup_type = normalized_lineup_type(raw.line_up)
    if not lineup_type:
        errors.append(_err("lineup_type", "INVALID_LINEUP_TYPE",
                           f"Lineup type inválido: '{raw.line_up}'. Debe ser 'S' o 'N'"))

    # ---- shirt_number ---- #
    shirt_number = parse_int(raw.shirt_number)
    if shirt_number is not None and shirt_number == 0:
        shirt_number = None

    # ---- player_name ---- #
    player_name = normalize_text(raw.player_name, max_length=100)
    if not player_name:
        errors.append(_err("player_name", "MISSING_PLAYER_NAME",
                           "Player name vacío"))

    # ---- position ---- #
    position = normalize_player_position(raw.position)
    if raw.position and not position:
        errors.append(_warn("position", "UNKNOWN_POSITION",
                            f"Posición no reconocida: '{raw.position}'"))

    # ---- event_code ---- #
    event_code = normalized_event_football_players_code(raw.event)
    if raw.event and not event_code:
        errors.append(_warn("event_code", "UNKNOWN_EVENT_CODE",
                            f"Event code no reconocido: '{raw.event}'"))

    # ---- Si hay errores graves → rechazar ---- #
    fatal = [e for e in errors if e.severity == "error"]
    if fatal:
        return _invalid(errors, raw_row_id)

    # ---- Construir fila limpia ---- #
    clean = CleanPlayersRow(
        round_id=round_id,
        match_id=match_id,
        team_initials=team_initials,
        coach_name=coach_name,
        lineup_type=lineup_type,
        shirt_number=shirt_number,
        player_name=player_name,
        position=position,
        event_code=event_code,
    )
    return _valid(clean, warnings=[e for e in errors if e.severity == "warning"], raw_row_id=raw_row_id)  # noqa: E501


# ─────────────────────────────────────────────────────────────────────────────
# REGLAS DE NEGOCIO: TEAMS
# Fuente: Extraídos de wc_matches.csv / wc_players.csv → public.teams
# ─────────────────────────────────────────────────────────────────────────────

def validate_team_row(
    initials: str | None,
    name: str | None = None,
    confederation: str | None = None,
    raw_row_id: int | None = None,
) -> ValidationResult:
    """
    Valida y limpia una fila de equipo extraída de matches/players.
    Los equipos se extraen como valores únicos de team_initials/home_team_initials/away_team_initials.
    """
    errors: list[ValidationError] = []

    validated_initials = normalize_initials(initials)
    if not validated_initials:
        errors.append(_err("initials", "MISSING_TEAM_INITIALS",
                           f"Iniciales de equipo vacías o inválidas: '{initials}'"))

    validated_name = normalize_text(name, max_length=100)

    validated_confederation = normalize_text(confederation, max_length=20)

    fatal = [e for e in errors if e.severity == "error"]
    if fatal:
        return _invalid(errors, raw_row_id)

    clean = CleanTeamRow(
        initials=validated_initials,
        name=validated_name,
        confederation=validated_confederation,
    )
    return _valid(clean, warnings=errors, raw_row_id=raw_row_id)


# ─────────────────────────────────────────────────────────────────────────────
# REGLAS DE NEGOCIO: ROUNDS
# Fuente: Extraídos de wc_matches.csv → public.rounds
# ─────────────────────────────────────────────────────────────────────────────

def validate_round_row(
    round_id: str | None,
    tournament_id: str | None,
    round_name: str | None,
    raw_row_id: int | None = None,
) -> ValidationResult:
    """
    Valida y limpia una fila de ronda extraída de matches.
    Las rondas se extraen como pares únicos (RoundID, Year → tournament_id, Stage → round_name).
    """
    errors: list[ValidationError] = []

    parsed_round_id = parse_int(round_id)
    if parsed_round_id is None or parsed_round_id < 1:
        errors.append(_err("round_id", "INVALID_ROUND_ID",
                           f"RoundID inválido: '{round_id}'"))

    parsed_tournament_id = parse_int(tournament_id)
    if parsed_tournament_id is None or parsed_tournament_id < 1:
        errors.append(_err("tournament_id", "INVALID_TOURNAMENT_ID",
                           f"TournamentID inválido: '{tournament_id}'"))

    validated_round_name = normalize_text(round_name, max_length=60)
    if not validated_round_name:
        errors.append(_err("round_name", "MISSING_ROUND_NAME",
                           "Nombre de ronda vacío"))

    fatal = [e for e in errors if e.severity == "error"]
    if fatal:
        return _invalid(errors, raw_row_id)

    clean = CleanRoundRow(
        round_id=parsed_round_id,
        tournament_id=parsed_tournament_id,
        round_name=validated_round_name,
    )
    return _valid(clean, warnings=errors, raw_row_id=raw_row_id)