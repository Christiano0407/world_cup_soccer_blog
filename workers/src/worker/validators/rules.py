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
    raw_row_id: int | None = None
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

  # ---- runners_up ---- #

  # ---- third & fourth place (opecionales - warning si ambos están vacíos) ---- #

  # ---- goals_scored ---- #

  # ---- qualified_teams ---- #

  # ── matches_played ─────────────────────────────────────────────

  # ── attendance (opcional — punto como separador de miles) ──────

  # ── Regla de negocio: avg goals coherente ─────────────────────

  # ── Si hay errores graves → rechazar ──────────────────────────

  # ── Construir fila limpia ──────────────────────────────────────



# ─────────────────────────────────────────────────────────────────────────────
# REGLAS DE NEGOCIO: MATCHES
# Fuente: wc_matches.csv → valida antes de cargar en public.matches
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# REGLAS DE NEGOCIO: PLAYERS
# Fuente: wc_players.csv → valida antes de cargar en public.match_players
# ─────────────────────────────────────────────────────────────────────────────