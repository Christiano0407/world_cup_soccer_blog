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
import re
from dataclasses import dataclass
from pathlib import Path

import asyncpg
import pandas as pd
import structlog

from worker.core.config import Settings
from worker.core.storage import get_minio_client
from worker.utils.constants import DATASET_CONFIG, DatasetKind
from worker.utils.helpers import clean_cell

log = structlog.get_logger(__name__)  # History - Real Time -

# Datasets sin header row en el CSV — la primera línea son datos, no cabeceras
_NO_HEADER_DATASETS: frozenset[str] = frozenset({"matches"})


def _normalize_column_name(name: str) -> str:
    """Convierte nombres de columna CSV a snake_case compatible con DATASET_CONFIG."""
    name = name.strip()
    name = name.replace("-", "_")
    name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    return name.lower().strip("_")


@dataclass
class IngestResult:
    dataset: DatasetKind
    source_file: str
    sha256: str
    rows_read: int
    rows_inserted: int
    minio_key: str


async def ingest_csv(file_path: Path, dataset: DatasetKind, settings: Settings) -> IngestResult:
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
    minio_key = f"raw/{dataset}/{source_name}"
    _upload_to_minio(settings, raw_bytes, minio_key, source_name)
    log.info("w1.minio_upload", key=minio_key)

    config = DATASET_CONFIG[dataset]

    # ── Step 2: Read CSV — all columns as str to preserve raw | Pandas ─
    if dataset in _NO_HEADER_DATASETS:
        # matches CSV no tiene header — datos empiezan en línea 1
        df = pd.read_csv(
            io.BytesIO(raw_bytes),
            dtype=str,
            header=None,
            names=config["columns"],
            keep_default_na=False,
            encoding="utf-8",
        )
    else:
        df = pd.read_csv(
            io.BytesIO(raw_bytes),
            dtype=str,  # no inference — W2 handles casting
            keep_default_na=False,
            encoding="utf-8",
        )
        # Normalize column names to snake_case matching config
        df.columns = [_normalize_column_name(c) for c in df.columns]

    rows_read = len(df)
    log.info("w1.csv_read", dataset=dataset, rows=rows_read, cols=list(df.columns))

    # ── Step 3: Insert into raw staging (parameterized) ───────
    conn = await asyncpg.connect(settings.postgres_dsn)
    inserted = 0
    try:
        async with conn.transaction():
            for _, row in df.iterrows():
                values = [source_name] + [clean_cell(row.get(col)) for col in config["columns"]]
                await conn.execute(config["insert_sql"], *values)
                inserted += 1

    finally:
        await conn.close()

    log.info("w1.complete", dataset=dataset, inserted=inserted, sha256=sha256[:12])

    return IngestResult(
        dataset=dataset,
        source_file=source_name,
        sha256=sha256,
        rows_read=rows_read,
        rows_inserted=inserted,
        minio_key=minio_key,
    )


def _upload_to_minio(settings: Settings, data: bytes, key: str, filename: str) -> None:
    client = get_minio_client()
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

