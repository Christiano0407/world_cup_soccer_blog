"""
W1 — Ingestion Worker | Extract [ETL]
=====================
Responsibility: Extract CSV files → upload raw to MinIO → insert into raw.* staging tables.
 
Rules:
- NEVER cast or validate types here. That is W2's job.
- NEVER construct SQL via string formatting. Use asyncpg $N placeholders.
- Log every file with its SHA-256 hash for reproducibility.
"""

from __future__ import annotations

import hashlib
import io 
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import asyncpg
import pandas as pd
import structlog
from minio import Minio
from minio.error import S3Error

from worker.core.config import Settings
from worker.core.storage import get_minio_client


log = structlog.get_logger(__name__) # History - Real Time -

DatasetKind = Literal["winners", "matches", "players"] # - Tables / SQL - postgres -

# = Maps dataset name → (csv columns in order, raw table name) =
DATASET_CONFIG : dict[DatasetKind, dict] = {
  "winners": {
    "raw_table": "raw.wc_winners",
    "columns": [
        "year", "country", "winner", "runners_up", "third",
        "fourth", "goals_scored", "qualified_teams", "matches_played", "attendance",
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
      "year", "datetime", "stage", "stadium", "city", "home_team_name",
      "win_conditions", "attendance", "ht_home_goals", "ht_away_goals", 
      "referee", "assistant_1", "assistant_2", "round_id", "match_id", 
      "home_team_initials", "away_team_initials",
    ],
    "insert_sql": """
          INSERT INTO raw.wc_matches (
            _source_file,
            "year", "datetime", "stage", "stadium", "city", "home_team_name",
            "win_conditions", "attendance", "ht_home_goals", "ht_away_goals", 
            "referee", "assistant_1", "assistant_2", "round_id", "match_id", 
            "home_team_initials", "away_team_initials",
          ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8 $9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21)   
    """,
  }, 
  "players": {
      "raw_tables": "raw.wc_players", 
      "columns": [
          "round_id", "match_id", "team_initials", "coach_name", "line_up", 
          "shirt_number", "player_name", "position", "event"
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

@dataclass
class IngestResult:
  dataset: DatasetKind
  source_file: str
  sha256: str
  rows_read: int
  rows_inserted: int
  minio_key: str

  async def ingest_csv(
      file_path: Path,
      dataset: DatasetKind, 
      settings: Settings
  ) -> IngestResult:
    """
      W1 main entrypoint.
        1. Read CSV with pandas (no type inference — all strings).
        2. Upload raw bytes to MinIO raw/ prefix.
        3. Insert every row into raw.* staging table (parameterized).
    """
    log.info("w1.start", dataset=dataset, file=str(file_path))

    raw_bytes = file_path.read_bytes()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    source_name = file_path.name

    # ---- Step 1: Upload raw CSV to MiniO ---- #
    minio_key = f"raw{dataset}/{source_name}"
    _upload_to_minio(settings,raw_bytes, minio_key, source_name)
    log.info("w1.minio_upload", key=minio_key)

    # ── Step 2: Read CSV — all columns as str to preserve raw ─

    # Normalize column names: lowercase + strip spaces

    # ── Step 3: Insert into raw staging (parameterized) ───────


def _upload_to_minio(settings: Settings, data: bytes, key: str, filename: str) -> None:
    client = get_minio_client(settings)
    bucket = settings.minio_bucket_raw
    if not client.bucket_exists(bucket):
      client.make_bucket(bucket)
    client.put_object(
      bucket_name=bucket,
      object_name=key,
      data=io.BytesIO(data), 
      length=len(data),
      content_type="text/csv",
      metadata={"x-source-file": filename},
    )