"""
workers/utils/constants.py
  - Constantes de negocio y del pipeline. | DB (Creamos)
  - Expresiones Regulares (ReGex)
  - Nunca hardcodear estos valores en la lógica — referenciar desde aquí.

=========================
Constantes de negocio y del pipeline ETL FIFA World Cup.
 
  - DatasetKind    → tipo literal para los 3 datasets del proyecto
  - DATASET_CONFIG → mapeo dataset → tabla raw + columnas + SQL de insert
  - Schemas SQL    → nombres de schemas de PostgreSQL
  - Regex          → patrones de validación reutilizables
  - Posiciones     → valores válidos del CSV de players
 
REGLA: Nunca hardcodear estos valores en la lógica — siempre referenciar desde aquí.
 
Bugs corregidos vs versión anterior:
  - matches y players: "raw_tables" → "raw_table" (typo)
  - players insert_sql: trailing comma eliminada (rompía PostgreSQL)
"""

from __future__ import annotations

from typing import Literal

# ─────────────────────────────────────────────────────────────────────────────
# TIPOS: Data Base (data sets)
# ─────────────────────────────────────────────────────────────────────────────

DatasetKind = Literal["winners", "matches", "players"]  # - Tables / SQL - postgres | Data Raw -

# = Maps dataset name → (csv columns in order, raw table name) =
DATASET_CONFIG: dict[DatasetKind, dict] = {
    "winners": {
        "raw_table": "raw.wc_winners", # > Clave consistente: raw_table
        "columns": [
            "year",
            "country",
            "winner",
            "runners_up",
            "third",
            "fourth",
            "goals_scored",
            "qualified_teams",
            "matches_played",
            "attendance",
        ],
        # $1 = _source_file, $2..$11 = columnas del CSV
        "insert_sql": """
        INSERT INTO raw.wc_winners (
          _source_file, year, country, winner, runners_up, third,
          fourth, goals_scored, qualified_teams, matches_played, attendance
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
    """,
    },
    "matches": {
        "raw_table": "raw.wc_matches",
        "columns": [
            "year",
            "datetime",
            "stage",
            "stadium",
            "city",
            "home_team_name",
            "home_team_goals",
            "away_team_goals",
            "away_team_name",
            "win_conditions",
            "attendance",
            "ht_home_goals",
            "ht_away_goals",
            "referee",
            "assistant_1",
            "assistant_2",
            "round_id",
            "match_id",
            "home_team_initials",
            "away_team_initials",
        ],
        # $1 = _source_file, $2..$21 = 20 columnas del CSV
        "insert_sql": """
          INSERT INTO raw.wc_matches (
            _source_file,
                year, datetime, stage, stadium, city,
                home_team_name, home_team_goals, away_team_goals, away_team_name,
                win_conditions, attendance, ht_home_goals, ht_away_goals,
                referee, assistant_1, assistant_2,
                round_id, match_id, home_team_initials, away_team_initials
          ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21)   
    """,
    },
    "players": {
        "raw_table": "raw.wc_players",
        "columns": [
            "round_id",
            "match_id",
            "team_initials",
            "coach_name",
            "line_up",
            "shirt_number",
            "player_name",
            "position",
            "event",
        ],
        # $1 = _source_file, $2..$10 = 9 columnas del CSV
        "insert_sql": """
          INSERT INTO raw.wc_players (
            _source_file,
            round_id, match_id, team_initials, coach_name, line_up, 
            shirt_number, player_name, position, event
          ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
      """,
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# NOMBRES DE SCHEMAS PostgreSQL
# ─────────────────────────────────────────────────────────────────────────────
RAW_SCHEMA:str = "raw"
PUBLIC_SCHEMA:str = "public"
WAREHOUSE_SCHEMA:str = "warehouse"
AUDIT_SCHEMA:str = "audit"


# ─────────────────────────────────────────────────────────────────────────────
# PATRONES REGEX
# ─────────────────────────────────────────────────────────────────────────────
## ---- Iniciales de equipo: 2-3 letras mayúsculas
TEAM_INITIALS_PATTERN: str = r"^[A-Z]{2,3}$"
## ---- Formato datetime del CSV de matches: "13 Jul 1930 - 15:00"
CSV_DATETIME_PATTERN:str = r"^\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s+\d{2}:\d{2}"
## ---- SKU genérico (heredado, por si se reutiliza)
SKU_PATTERN: str = r"^[A-Z0-9\-]{3,64}$"
## ---- Dimensiones (heredado)
DIMENSIONS_PATTERN: str = r"^\d+(\.\d+)?[xX]\d+(\.\d+)?[xX]\d+(\.\d+)?$"


# ─────────────────────────────────────────────────────────────────────────────
# VALORES VÁLIDOS DEL DOMINIO — extraídos del CSV
# ── Patrones de validación ────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
### ---- Posiciones válidas en el CSV de players
VALID_POSITIONS: frozenset[str] = frozenset({"GK", "DF", "MF", "FW"})
 
### ---- Tipos de alineación válidos
VALID_LINEUP_TYPES: frozenset[str] = frozenset({"S", "N"})
 
### ---- Eventos válidos — prefijos (ej: "G40", "G45+1" también son válidos)
VALID_EVENT_PREFIXES: tuple[str, ...] = ("G", "OG", "Y", "R", "SY", "P")
 
### ---- Rango de años válidos del Mundial FIFA
MIN_WC_YEAR: int = 1930
MAX_WC_YEAR: int = 2030
 
### ---- Límite razonable de goles por torneo
MAX_GOALS_PER_TOURNAMENT: int = 200
 
### ---- Límite razonable de asistencia por partido
MAX_ATTENDANCE_PER_MATCH: int = 200_000
 
### ---- Shirt numbers válidos (0 = sin asignar en el CSV)
MAX_SHIRT_NUMBER: int = 99


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DEL PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
#### ──- Audit ─────────────────────────────────────────────────────
AUDIT_SCHEMA: str = "audit"
RAW_SCHEMA: str = "raw"
WAREHOUSE_SCHEMA: str = "warehouse"

#### ---- Tamaño de batch para inserts en raw.* (W1)
ETL_BATCH_SIZE: int = 500
 
#### ---- Tiempo máximo de espera para conexión a DB (segundos)
DB_CONNECT_TIMEOUT: int = 30
 
#### ---- Prefijos en MinIO
MINIO_RAW_PREFIX: str       = "raw"
MINIO_PROCESSED_PREFIX: str = "processed"
MINIO_PARQUET_PREFIX: str   = "parquet"