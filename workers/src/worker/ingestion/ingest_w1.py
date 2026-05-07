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

# Maps dataset name → (csv columns in order, raw table name)
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
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
    """,
  },
  "matches": {

  }, 
  "players": {

  }
}