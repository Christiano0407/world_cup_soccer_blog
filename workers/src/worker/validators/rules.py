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
 

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS INTERNOS DE VALIDACIÓN
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# REGLAS DE NEGOCIO: WINNERS
# Fuente: wc_winners.csv → valida antes de cargar en public.tournaments
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# REGLAS DE NEGOCIO: MATCHES
# Fuente: wc_matches.csv → valida antes de cargar en public.matches
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# REGLAS DE NEGOCIO: PLAYERS
# Fuente: wc_players.csv → valida antes de cargar en public.match_players
# ─────────────────────────────────────────────────────────────────────────────