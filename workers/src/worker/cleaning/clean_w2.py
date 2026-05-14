"""
W2 — Clean Worker
=================
Responsibility: Read raw.* staging → validate → cast types → mark valid/invalid.
Rejected rows → raw.dead_letter with structured error codes.
 
  - Anti SQL-Injection: All queries use asyncpg $N parameterized execution. 
  - Migrations: All schema de Bases de datos & Storage s3
# =============================================================================== #
  Responsabilidad única: leer raw.* → validar con rules.py → marcar → dead_letter.
 
FLUJO:
  raw.wc_* (_is_valid IS NULL)
      │
      ├─ RawXxxRow          (schema Pydantic — mapeo sin casteo)
      ├─ validate_xxx_row() (rules.py — reglas de negocio)
      │
      ├─ is_valid=True  → UPDATE _is_valid=TRUE
      └─ is_valid=False → UPDATE _is_valid=FALSE
                        → INSERT raw.dead_letter
 
MEJORAS vs versión anterior:
  - Usa validate_*_row() de rules.py — sin lógica de validación inline
  - Usa RawXxxRow de schemas.py — tipado explícito por dataset
  - Pool de conexiones en vez de conexión única
  - Batch processing: lotes de BATCH_SIZE para no cargar todo en RAM
  - CleanResult con rejection_rate, is_acceptable y log_summary
  - Transacción atómica por fila inválida (UPDATE + INSERT dead_letter)
  - match/case en vez de if/elif anidados (Python 3.10+)
 
Anti SQL-Injection: toda query usa asyncpg $N parameterized.
El f-string en update_sql usa valores de constants.py — nunca input externo.
"""

from __future__ import annotations

import asyncpg
import structlog
from typing import AsyncGenerator

from dataclasses import dataclass, field
from worker.core.config import Settings
from worker.validators.rules import (
  ValidationResult, 
  validate_matches_row, 
  validate_players_row, 
  validate_winners_row, 
  validate_team_row, 
  validate_round_row
)
from worker.validators.schemas import (
  RawMatchesRow, 
  RawPlayersRow, 
  RawWinnersRow, 
)
from worker.utils.constants import DatasetKind
from worker.utils.helpers import parse_int


log = structlog.get_logger(__name__) # - Logs / History -Real Time - #
BATCH_SIZE = 50 # filas por lote — ajustar según RAM disponible


# ─────────────────────────────────────────────────────────────────────────────
# RESULTADO DEL WORKER
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CleanResults:
  """
    - Métricas del proceso W2. Devuelto por clean_dataset().
    - El runner usa is_acceptable para decidir si continuar con W3.
  """
  dataset: DatasetKind
  rows_checked: int
  rows_valid: int
  rows_rejected: int
  rows_with_warning: int
  error_breakdown: dict[str, int] = field(default_factory=dict)
  warning_breakdown: dict[str, int] = field(default_factory=dict)

  @property
  def rejection_rate(self) -> float:
    """ Saber cuántas & cuáles fueron rechazadas (datos)"""
    if self.rows_checked == 0:
      return 0.0
    return round(self.rows_rejected / self.rows_checked * 100, 2)
  
  @property
  def is_acceptable(self) -> bool:
    "False si la tasa de rechazo supera el 10% — señal de problema en el CSV [Dataset]."
    return self.rejection_rate < 10.0
  
  def log_summary(self) -> None:
        """ History all Process (Real Time) """
        log.info(
            "w2.summary",
            dataset=self.dataset,
            rows_checked=self.rows_checked,
            rows_valid=self.rows_valid,
            rows_rejected=self.rows_rejected,
            rows_with_warning=self.rows_with_warning,
            rejection_rate_pct=self.rejection_rate,
            acceptable=self.is_acceptable,
            top_errors=sorted(
                self.error_breakdown.items(), key=lambda x: -x[1]
            )[:5],
        )


# ─────────────────────────────────────────────────────────────────────────────
# ENTRYPOINT PÚBLICO
# ─────────────────────────────────────────────────────────────────────────────
async def clean_dataset(dataset: DatasetKind, settings:Settings) -> CleanResults:
   """
     W2_clean — entrypoint principal. Llamado por el runner del pipeline.
 
    Args:
        dataset:  "winners" | "matches" | "players"
        settings: configuración del entorno (DSN postgres, etc.)
 
    Returns:
        CleanResult con métricas. Si result.is_acceptable=False,
        el runner puede detener el pipeline antes de W3 (load) - No cumplen con requisitos.
    
    Pool Connection:
        Connection Pool es un conjunto reutilizable de conexiones abiertas hacia PostgreSQL.
        abrir/cerrar conexiones constantemente, el pool:
              - crea conexiones una sola vez
              - las mantiene vivas
              - las reutiliza
              - mejora rendimiento
              - reduce latencia
              - evita saturar PostgreSQL 
        - _dns [Data Source Name]
   """
   log.info("w2.start", dataset=dataset)

   pool = await asyncpg.create_pool(
      settings.postgres_dsn,
      min_size=2,
      max_size=10,
      command_timeout=60,
   )

   try: 
      match dataset:
         case "winners":
            result = await _clean_winners(pool)
         case "matches":
            result = await _clean_matches(pool)
         case "players":
            result = await _clean_players(pool)
         case _:
            raise ValueError(
               f"Dataset desconocido: '{dataset}' "
               " - debe ser winners | matches | players "
            )
   finally: 
      await pool.close()

   if not result.is_acceptable:
      log.warning(
         "w2.high_rejection_rate",
         dataset=dataset,
         rate_pct=result.rejection_rate,
         message = "Tasa de Rechazo > 10% | Revisar la calidad de los Dataset [CSV] & DB",
      )

   return result

    
# ─────────────────────────────────────────────────────────────────────────────
# LIMPIEZA POR DATASET
# ─────────────────────────────────────────────────────────────────────────────
async def _clean_winners(pool: asyncpg.Pool) -> CleanResults:
   result = CleanResults(
      dataset="winners", 
      rows_checked=0, 
      rows_valid=0, 
      rows_rejected=0, 
      rows_with_warning=0
   )
   async for batch in _fetch_batches(pool, "raw.wc_winners"):
      result.rows_checked += len(batch)
      for row in batch:
         raw = RawWinnersRow(
            year=row["year"],
            country=row["country"],
            winner=row["winner"],
            runners_up=row["runners_up"],
            third=row["third"],
            fourth=row["fourth"],
            goals_scored=row["goals_scored"],
            qualified_teams=row["qualified_teams"],
            matches_played=row["matches_played"],
            attendance=row["attendance"],
         )
         validation = validate_winners_row(raw, raw_row_id=row["_row_id"])
         await _persist(pool, validation, "raw.wc_winners", row["_row_id"], result)

   return result


async def _clean_matches(pool: asyncpg.Pool) -> CleanResults:
   result = CleanResults (
      dataset="matches", 
      rows_checked=0, 
      rows_valid=0, 
      rows_rejected=0, 
      rows_with_warning=0
   )
   
   async for batch in _fetch_batches(pool, "raw.wc_matches"):
      result.rows_checked += len(batch)
      for row in batch:
          raw = RawMatchesRow(
             year=row["year"],
             datetime=row["datetime"],
             stage=row["stage"],
             stadium=row["stadium"],
             city=row["city"],
             home_team_name=row["home_team_name"],
             home_team_goals=row["home_team_goals"],
             away_team_goals=row["away_team_goals"],
             away_team_name=row["away_team_name"],
             win_conditions=row["win_conditions"],
             attendance=row["attendance"],
             ht_home_goals=row["ht_home_goals"],
             ht_away_goals=row["ht_away_goals"],
             referee=row["referee"],
             assistant_1=row["assistant_1"],
             assistant_2=row["assistant_2"],
             round_id=row["round_id"],
             match_id=row["match_id"],
             home_team_initials=row["home_team_initials"],
             away_team_initials=row["away_team_initials"],
          )
          year_int = parse_int(row["year"])
          tournament_id = ((year_int - 1930) // 4) + 1 if year_int else None
          validation = validate_matches_row(raw, tournament_id=tournament_id, raw_row_id=row["_row_id"])
          await _persist(pool, validation, "raw.wc_matches", row["_row_id"], result)

   return result

async def _clean_players(pool: asyncpg.Pool) -> CleanResults:
   result = CleanResults (
      dataset="players", 
      rows_checked=0, 
      rows_valid=0, 
      rows_rejected=0, 
      rows_with_warning=0
   )
   
   async for batch in _fetch_batches(pool, "raw.wc_players"):
      result.rows_checked += len(batch)
      for row in batch:
         raw = RawPlayersRow(
            round_id=row["round_id"],
            match_id=row["match_id"],
            team_initials=row["team_initials"],
            coach_name=row["coach_name"],
            line_up=row["line_up"],
            shirt_number=row["shirt_number"],
            player_name=row["player_name"],
            position=row["position"],
            event=row["event"],
         )
         validation = validate_players_row(raw, raw_row_id=row["_row_id"])
         await _persist(pool, validation, "raw.wc_players", row["_row_id"], result)

   return result 

# ─────────────────────────────────────────────────────────────────────────────
# FETCH EN LOTES — evita cargar todo el dataset en memoria
# ─────────────────────────────────────────────────────────────────────────────

async def _fetch_batches(
      pool: asyncpg.Pool, 
      table:str,
      batch_size: int = BATCH_SIZE,
) -> AsyncGenerator[list[asyncpg.Record], None]:
    """
      - Generador asíncrono que lee filas pendientes en lotes.
      - Usa LIMIT + OFFSET sobre _row_id para paginación estable.
      - table viene de constants.py — nunca de input externo.
    """
    offset = 0
    query = (
       f"SELECT * FROM {table} "  # noqa: S608
       F"WHERE _is_valid IS NULL"
       F"ORDER BY _row_id "
       F"LIMIT {batch_size} OFFSET  $1"
    )

    while True:
       async with pool.acquire() as conn:
          batch = await conn.fetch(query, offset)

       if not batch:
          break
       
       log.debug("w2.batch", table=table, offset=offset, n=len(batch))
       yield list(batch)
       offset += batch_size


 
# ─────────────────────────────────────────────────────────────────────────────
# PERSISTENCIA — una transacción atómica por fila inválida
  # - Validación de filas [Dataset / datos] - Validación todo el tiempo
# ─────────────────────────────────────────────────────────────────────────────

async def _persist(
      pool: asyncpg.Pool, 
      validation: ValidationResult, 
      table: str, 
      row_id: int,
      result: CleanResults,
) -> None:
    """
      - Persiste resultado de validación de una fila.
 
      Válida   → UPDATE _is_valid=TRUE
      Inválida → transacción: UPDATE _is_valid=FALSE + INSERT dead_letter
 
      - table viene de constants.py — f-string seguro, nunca input externo.
      - Valores van en $N — sin concatenación de datos en SQL.

      - Evitar SQL Injection [Problemas de Seguridad & Ciberseguridad]
    """
    update_sql = f"UPDATE {table} SET _is_valid = $1 WHERE _row_id = $2"  # noqa: S608

    async with pool.acquire() as conn:
       if validation.is_valid:
          await conn.execute(update_sql, True, row_id)
          result.rows_valid += 1

          if validation.has_warning:
             result.rows_with_warning += 1
             for w in validation.errors:
                if w.severity == "warning":
                   result.warning_breakdown[w.code] = (
                      result.warning_breakdown.get(w.code, 0) + 1
                   )
                   log.warning(
                      "w2.row_warning",
                      table=table,
                      row_id=row_id, 
                      code=w.code,
                      field=w.field,
                      msg=w.message,
                   )

       else:
          async with conn.transaction():
             await conn.execute(update_sql, False, row_id)
             await conn.execute(
                 """
                 INSERT INTO raw.dead_letter (
                     _source_table,
                     _source_row_id,
                     _error_code,
                     _error_detail
                 ) VALUES ($1, $2, $3, $4)
                 """,
                 table,
                 row_id,
                 validation.first_error_code or "UNKNOWN_ERROR",
                 validation.error_detail[:2000],
             )

             result.rows_rejected += 1
             for code in validation.error_code:
                 result.error_breakdown[code] = (
                     result.error_breakdown.get(code, 0) + 1
                 )
             log.warning(
                 "w2.row_rejected",
                 table=table,
                 row_id=row_id,
                 code=validation.first_error_code,
                 all_codes=validation.error_code,
             )
             