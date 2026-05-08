"""
workers/utils/constants.py
  - Constantes de negocio y del pipeline. | DB (Creamos)
  - Expresiones Regulares (ReGex)
  - Nunca hardcodear estos valores en la lógica — referenciar desde aquí.
"""

from typing import Literal

DatasetKind = Literal["winners", "matches", "players"]  # - Tables / SQL - postgres -

# = Maps dataset name → (csv columns in order, raw table name) =
DATASET_CONFIG: dict[DatasetKind, dict] = {
    "winners": {
        "raw_table": "raw.wc_winners",
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
        "insert_sql": """
        INSERT INTO raw.wc_winners (
          _source_file, year, country, winner, runners_up, third,
          fourth, goals_scored, qualified_teams, matches_played, attendance
        ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
    """,
    },
    "matches": {
        "raw_tables": "raw.wc_matches",
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
        "raw_tables": "raw.wc_players",
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
        "insert_sql": """
          INSERT INTO raw.wc_players (
            _source_file,
            round_id, match_id, team_initials, coach_name, line_up, 
            shirt_number, player_name, position, event, 
          ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
      """,
    },
}

# ── Patrones de validación ────────────────────────────────────
SKU_PATTERN: str = r"^[A-Z0-9\-]{3,64}$"
DIMENSIONS_PATTERN: str = r"^\d+(\.\d+)?[xX]\d+(\.\d+)?[xX]\d+(\.\d+)?$"

# ── Audit ─────────────────────────────────────────────────────
AUDIT_SCHEMA: str = "audit"
RAW_SCHEMA: str = "raw"
WAREHOUSE_SCHEMA: str = "warehouse"