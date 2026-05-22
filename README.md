# FIFA World Cup Data Platform

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![MinIO](https://img.shields.io/badge/MinIO-S3--compatible-FF6600?logo=minio&logoColor=white)](https://min.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![uv](https://img.shields.io/badge/uv-0.6+-DE5FE9?logo=python&logoColor=white)](https://github.com/astral-sh/uv)
[![Async](https://img.shields.io/badge/Async-asyncpg-0EA5E9?logo=python&logoColor=white)](https://github.com/MagicStack/asyncpg)

---

## Tabla de Contenidos

- [Mapa Maestro](#mapa-maestro--arquitectura-del-sistema)
- [Pipeline ETL](#pipeline-etl--detalle-por-etapa)
- [Stack Tecnológico](#stack-tecnológico)
- [Quick Reference — Comandos](#quick-reference--comandos)
- [Comandos psql para Verificación](#comandos-psql-para-verificación)
- [Servicios y Puertos](#servicios-y-puertos)
- [Prerrequisitos y Setup](#prerrequisitos-y-setup)
- [Ejecutar Pipeline ETL](#ejecutar-pipeline-etl)
- [Ejecutar Tests](#ejecutar-tests)
- [Test Architecture](#test-architecture)
- [Troubleshooting — Errores Conocidos](#troubleshooting--errores-conocidos)
- [Project Structure](#project-structure)
- [Licencia](#licencia)

---

## Mapa Maestro — Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                        DATA LAYER                                              │
│                           docker-compose.yml  ───  .env (config)                                │
│                           postgres:5434 │ minio:9000 │ nginx:8080                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────┐
    │  nginx (reverse proxy)                    host:8080 → cont:80   │
    │  ├─ /api/* ──▶ backend (FastAPI)                               │
    │  └─ /       ──▶ frontend                                       │
    └───────────────────────────────────────────┬──────────────────────┘
                                                │
                                                ▼
    ┌──────────────────────────────────────────────────────────────────┐
    │  PostgreSQL 15  (db=data-world-cup)        host:5434 → cont:5432 │
    │                                                                  │
    │  ┌────────────────────────────────────────────────────────────┐  │
    │  │  Schemas internos                                          │  │
    │  │                                                            │  │
    │  │  raw.*          │  raw.wc_winners   (TEXT, staging cruda)  │  │
    │  │                 │  raw.wc_matches   (TEXT, staging cruda)  │  │
    │  │                 │  raw.wc_players   (TEXT, staging cruda)  │  │
    │  │                 │  raw.dead_letter  (rechazos de W2)       │  │
    │  │                 └────────────────────────────────────────  │  │
    │  │                                                            │  │
    │  │  public.*       │  public.teams         (tipado + FKs)     │  │
    │  │                 │  public.tournaments   (tipado + FKs)     │  │
    │  │                 │  public.rounds        (tipado + FKs)     │  │
    │  │                 │  public.matches       (tipado + FKs)     │  │
    │  │                 │  public.match_players (tipado + FKs)     │  │
    │  │                 │  public.stadiums, referees, players...   │  │
    │  │                 └────────────────────────────────────────  │  │
    │  │                                                            │  │
    │  │  warehouse.*    │  vw_tournament_stats  (materializada)    │  │
    │  │                 │  vw_match_details     (materializada)    │  │
    │  │                 │  vw_player_leaderboard (materializada)   │  │
    │  │                 └────────────────────────────────────────  │  │
    │  │                                                            │  │
    │  │  audit.*        │  logs (cambios, errores)                 │  │
    │  │                 │  auth (credenciales API)                 │  │
    │  └────────────────────────────────────────────────────────────┘  │
    └───────────────────────┬──────────────────────────────────────────┘
                            │
                            │  asyncpg :5432 (dentro de red Docker)
                            ▼

    ┌──────────────────────────────────────────────────────────────────┐
    │  ETL Pipeline Workers  (container: fifa-workers)                 │
    │                                                                  │
    │  │ CLI entrypoint: cli.py  (fifa-worker --all)                  │
    │  │ Runtime:  uv run fifa-worker [--ingest | --clean | --load]   │
    │  │ Deps:     asyncpg, pandas, minio, pydantic, pyarrow           │
    │  │ Logging:  structlog (JSON estructurado a stdout)             │
    │  │                                                            │
    │  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
    │  │              │    │              │    │              │    │
    │  │  W1 — Ingest │───▶│  W2 — Clean  │───▶│  W3 — Load   │    │
    │  │              │    │              │    │              │    │
    │  │  CSV on disk │    │  rules.py    │    │  schemas.py  │    │
    │  │  pandas read │    │  validates   │    │  transforms  │    │
    │  │  raw.* TEXT  │    │  _is_valid   │    │  public.*    │    │
    │  │  MinIO raw/  │    │  dead_letter │    │  warehouse.* │    │
    │  │              │    │              │    │  MinIO parq/ │    │
    │  │  ingest_w1   │    │  clean_w2    │    │  load_w3     │    │
    │  └──────┬───────┘    └──────────────┘    └───────┬──────┘    │
    │         │                                        │           │
    │         └─────── Data Flow ──────────────────────┘           │
    └─────────────────────────┬────────────────────────────────────┘
                              │
                              │  minio-py :9000 (S3 API)
                              ▼

    ┌──────────────────────────────────────────────────────────────────┐
    │  MinIO (S3-compatible)              API: host:9000 → cont:9000  │
    │                                    Console: host:9001 → cont:9001│
    │                                                                  │
    │  Bucket: core-storage                                            │
    │  ┌────────────────────────────────────────────────────────────┐  │
    │  │  /raw/          CSVs originales  (W1 upload)              │  │
    │  │  /parquet/      Datos transformados (W3 export, .parquet) │  │
    │  │  /processed/    CSVs ya procesados (W1 post-upload)      │  │
    │  │  /images/       Assets gráficos  (backend/frontend)      │  │
    │  └────────────────────────────────────────────────────────────┘  │
    │                                                                  │
    │  ⚠ S3_ENDPOINT=minio:9000  (sin http:// — minio-py lo añade)   │
    └──────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────┐
    │  Volúmenes y montajes (bind mounts)                              │
    │                                                                  │
    │  ./data/raw/     ──▶  /raw/        (workers: CSVs de entrada)   │
    │  ./data/samples/ ──▶  /samples/    (workers: datos de prueba)   │
    │  db/migrations/  ──▶  /docker-entrypoint-initdb.d/  (PG init)   │
    │                                                                  │
    │  ./data/raw/  contiene:  wc_world_cup_winners.csv                │
    │                          wc_matches.csv                          │
    │                          wc_players.csv                          │
    └──────────────────────────────────────────────────────────────────┘
```

---

## Pipeline ETL — Detalle por Etapa

### W1 — Ingest (Extract)

Lee los CSVs crudos del directorio `data/raw/` y los persiste en la base y en MinIO sin transformación.

```
wc_*.csv  ──▶  pandas(dtype=str)  ──▶  raw.* (TEXT columns)
data/raw/                           ──▶  MinIO bucket raw/
                                     ──▶  SHA-256 checksum
```

| Característica | Detalle |
|---|---|
| Inferencia de tipos | Deshabilitada (`dtype=str, keep_default_na=False`) |
| Columnas | Todas `TEXT` — sin constraints ni validaciones |
| Almacenamiento | `raw.wc_winners`, `raw.wc_matches`, `raw.wc_players` |
| Trazabilidad | `_source_file`, `_row_id`, SHA-256 del archivo |
| MinIO | Bucket `raw/` con copia bit a bit del CSV original |

### W2 — Clean (Validate)

Lee filas pendientes (`_is_valid IS NULL`), aplica reglas de negocio, y marca cada fila como válida o inválida.

```
raw.*  ──▶  rules.py (validadores)  ──▶  _is_valid = TRUE/FALSE
                    │                       │
                    ▼                       ▼
            RowWarning / Error       raw.dead_letter (si FALSE)
```

| Dataset | Reglas Clave |
|---|---|
| **winners** | `year` [1930-2030], `winner` presente, `goals_scored` ≥ 0, `qualified_teams` [1-48] |
| **matches** | `match_id` ≥ 1, `stage` presente, goles ≥ 0, iniciales 2-3 letras |
| **players** | `round_id` ≥ 1, `match_id` ≥ 1, `team_initials` presentes, `line_up` S/N |

El pipeline monitorea la tasa de rechazo: si supera el 10%, no continúa a W3.

### W3 — Load (Transform & Load)

Lee solo filas validadas (`_is_valid = TRUE`), transforma tipos, y hace upsert en `public.*`.

```
raw.wc_winners  ──▶  public.tournaments    (ON CONFLICT year)
raw.wc_matches  ──▶  public.rounds          (ON CONFLICT round_id)
                 ──▶  public.matches         (ON CONFLICT match_id)
                 ──▶  public.teams           (ON CONFLICT initials)
raw.wc_players  ──▶  public.match_players    (DELETE + INSERT)
                 ──▶  public.teams

Todas ──▶  warehouse.refresh_all()
       ──▶  MinIO parquet/  (.parquet)
```

**Transformaciones:**
| Función | Propósito |
|---|---|
| `parse_int()` | String → int (None si inválido) |
| `parse_attendance()` | "590.549" → 590549 (formato europeo) |
| `parse_datetime_csv()` | "13 Jul 1930 - 15:00" → datetime |
| `normalize_text()` | Strip + truncate por límite de columna |
| `normalize_initials()` | Uppercase + validación 2-3 caracteres |
| `normalize_team_names()` | Title case |

**Manejo de errores conocidos en W3:**
- Filas sin `match_datetime` → se saltan (warn + continue)
- Players con `match_id` ausente en `matches` → se filtran contra `public.matches`

---

## Stack Tecnológico

### Core

| Tecnología | Versión | Propósito |
|---|---|---|
| Python | ≥ 3.12 | Type hints nativos, pattern matching, asyncio |
| Docker Compose | v2.27+ | Orquestación multi-contenedor |
| PostgreSQL | 15 | Base de datos relacional |
| MinIO | latest | Storage S3-compatible |
| nginx | 1.25+ | Reverse proxy |

### ETL Pipeline

| Librería | Versión | Propósito |
|---|---|---|
| `asyncpg` | ≥ 0.29 | Driver PostgreSQL asíncrono |
| `pandas` | ≥ 2.2 | Lectura de CSVs |
| `minio` | 7.2.20 | Cliente S3 para MinIO |
| `pydantic` v2 | ≥ 2.6 | Schemas Raw + Clean |
| `pyarrow` | ≥ 14.0 | Engine para exportación Parquet |
| `structlog` | ≥ 24.1 | Logging estructurado |

### Testing & Calidad

| Herramienta | Versión | Propósito |
|---|---|---|
| `pytest` | ≥ 8.1 | Test runner |
| `pytest-asyncio` | ≥ 0.23 | Tests asíncronos |
| `pytest-cov` | ≥ 5.0 | Cobertura |
| `ruff` | ≥ 0.4 | Linter + formatter |
| `mypy` | ≥ 1.9 | Type checking estricto |

---

## Quick Reference — Comandos

### Docker Compose

```bash
# Construir y levantar todos los servicios
docker compose up -d --build

# Reconstruir forzando recreación de contenedores
docker compose up -d --build --force-recreate

# Ver logs del worker (por service name)
docker compose logs worker

# Ver logs de un contenedor (por container name)
docker logs fifa-workers

# Listar servicios activos
docker compose ps

# Listar todos los servicios (incluyendo stopped)
docker compose ps -a

# Detener servicios
docker compose stop

# Detener y eliminar volúmenes (borra TODOS los datos)
docker compose down -v
```

### Pipeline ETL

```bash
# Pipeline completo (W1 → W2 → W3)
fifa-worker --all

# Etapas individuales
fifa-worker --ingest      # W1
fifa-worker --clean       # W2
fifa-worker --load        # W3
```

### Tests

```bash
cd workers

# Unit tests (sin dependencias externas)
uv run pytest tests/unit/ -v

# Integration tests (requiere PostgreSQL + MinIO)
uv run pytest tests/integration/ -v -m integration

# Todos los tests con cobertura
uv run pytest -v --cov=worker

# Lint + format
uv run ruff check . && uv run ruff format .
```

---

## Comandos psql para Verificación

```bash
# Conteo rápido de todas las tablas
docker compose exec postgres psql -U champion07 -d data-world-cup -c "
SELECT 'teams' AS tbl, COUNT(*) FROM public.teams
UNION ALL SELECT 'tournaments', COUNT(*) FROM public.tournaments
UNION ALL SELECT 'rounds', COUNT(*) FROM public.rounds
UNION ALL SELECT 'matches', COUNT(*) FROM public.matches
UNION ALL SELECT 'match_players', COUNT(*) FROM public.match_players;"

# Ver equipos cargados
docker compose exec postgres psql -U champion07 -d data-world-cup \
  -c "SELECT initials, name FROM public.teams ORDER BY initials LIMIT 10;"

# Ver torneos
docker compose exec postgres psql -U champion07 -d data-world-cup \
  -c "SELECT year, host_country, winner FROM public.tournaments ORDER BY year;"

# Ver últimos partidos
docker compose exec postgres psql -U champion07 -d data-world-cup \
  -c "SELECT match_id, match_datetime, stage, home_team_initials, away_team_initials, home_goals, away_goals FROM public.matches ORDER BY match_datetime DESC LIMIT 5;"

# Ver staging crudo (raw)
docker compose exec postgres psql -U champion07 -d data-world-cup \
  -c "SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE _is_valid) AS validos, COUNT(*) FILTER (WHERE NOT _is_valid) AS rechazados FROM raw.wc_matches;"

# Ver dead_letter (rechazos)
docker compose exec postgres psql -U champion07 -d data-world-cup \
  -c "SELECT _error_code, COUNT(*) FROM raw.dead_letter GROUP BY _error_code ORDER BY COUNT(*) DESC;"

# Conexión interactiva
docker compose exec -it postgres psql -U champion07 -d data-world-cup

# Ejecutar migraciones manualmente
docker compose exec postgres bash /docker-entrypoint-initdb.d/01-run_migrations.sh
```

---

## Servicios y Puertos

| Servicio | Host:Puerto | Propósito |
|---|---|---|
| PostgreSQL | `localhost:5434` | Base de datos ( :5432 dentro del contenedor) |
| MinIO API | `localhost:9000` | Endpoint S3 |
| MinIO Console | `localhost:9001` | Admin UI |
| nginx | `localhost:8080` | Reverse proxy |

---

## Prerrequisitos y Setup

### Requisitos

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Docker Engine + Docker Compose v2.27+

### Variables de Entorno

Copiar `.env.example` a `.env` y ajustar:

```bash
cp .env.example .env
```

**⚠ Importante:** `S3_ENDPOINT` debe ser solo `host:port` sin scheme (`http://`). El cliente MinIO lo agrega automáticamente.

```env
# PostgreSQL
POSTGRES_USER=champion07
POSTGRES_PASSWORD=change_me_in_production
POSTGRES_DB=data-world-cup

# MinIO
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=change_me_in_production
MINIO_BUCKET=core-storage
S3_ENDPOINT=minio:9000           # sin http://
S3_ACCESS_KEY=admin
S3_SECRET_KEY=change_me_in_production
```

### Inicializar Infraestructura

```bash
docker compose up -d postgres minio
```

Las migraciones (000 → 010) se ejecutan automáticamente al crear la base por primera vez via `/docker-entrypoint-initdb.d/`.

---

## Ejecutar Pipeline ETL

```bash
# Workers dentro del contenedor
docker compose run --rm worker uv run fifa-worker --all
docker compose run --rm worker uv run fifa-worker --ingest
docker compose run --rm worker uv run fifa-worker --clean
docker compose run --rm worker uv run fifa-worker --load
```

O si el worker se ejecuta en modo servicio (definido en `docker-compose.yml` como `command: ["uv", "run", "fifa-worker", "--all"]`), se ejecuta automáticamente al iniciar:

```bash
docker compose up -d --build
docker compose logs worker
```

---

## Ejecutar Tests

```bash
cd workers
uv sync --extra dev

# Unit tests
uv run pytest tests/unit/ -v

# Integration tests
uv run pytest tests/integration/ -v -m integration

# Cobertura completa
uv run pytest -v --cov=worker
```

Resultado actual:
```
workers/tests/
├── unit/
│   ├── test_helpers.py     68 tests  (97% coverage)
│   ├── test_rules.py       35 tests  (95% coverage)
│   ├── test_schemas.py     36 tests  (99% coverage)
│   └── test_cli.py          8 tests  (52% coverage)
│
├── integration/
│   ├── test_w1_ingest.py   (requiere PG + MinIO)
│   ├── test_w2_clean.py
│   └── test_w3_load.py
│
├── Total coverage: 77% (949 statements)
└── Ruff: 0 errors — All checks passed
```

---

## Test Architecture

Los tests residen en `workers/tests/` (no en una carpeta raíz) por las siguientes razones:

| Razón | Explicación |
|---|---|
| **Aislamiento** | Los workers son el único componente ETL que requiere tests. Backend y frontend tienen sus propias validaciones. |
| **Descubrimiento** | `pyproject.toml` define `testpaths = ["tests"]`. `uv run pytest` funciona sin PATH manual. |
| **Cohesión** | `uv` opera desde `workers/`. Tests fuera obligarían a rutas relativas tipo `../workers/src/`. |
| **Cobertura** | `--cov=worker` apunta al módulo correcto sin incluir backend u otros servicios. |
| **Portabilidad** | `workers/` es autocontenido: pyproject.toml, Dockerfile, src/, tests/. Se puede buildear, testear y deployar sin depender del monorepo raíz. |

### Ruff Configuration

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "S", "B", "ANN"]
per-file-ignores = { "tests/**" = ["S101", "ANN201", "ANN001", "ANN202"] }
```

- `S101` permitido en tests — `assert` es correcto en contexto de test
- `ANN201`, `ANN001`, `ANN202` permitidos en tests — type annotations en tests añaden ruido sin beneficio

---

## Troubleshooting — Errores Conocidos

### 1. Worker falla con `ValueError: path in endpoint is not allowed`

**Causa:** `S3_ENDPOINT` en `.env` incluye `http://` (ej: `http://minio:9000`).

El cliente MinIO **ya prepende** el scheme (`http://` o `https://`) automáticamente. Si el endpoint ya tiene scheme, se duplica:

```
"http://" + "http://minio:9000" = "http://http://minio:9000" → error
```

**Solución:** Usar solo `host:port` sin scheme:
```env
S3_ENDPOINT=minio:9000
```

La función `get_minio_client()` en `storage.py` también tiene una capa defensiva que limpia cualquier scheme presente.

### 2. Worker falla con `NotNullViolationError: null value in column "match_datetime"`

**Causa:** Algunas filas en `wc_matches.csv` no tienen fecha (datetime vacío). `_load_matches()` intenta insertar `NULL` en una columna `NOT NULL`.

**Solución:** W3 salta esas filas automáticamente:
```
w3.match_skip_no_datetime  match_id=43950010
```

### 3. Worker falla con `ForeignKeyViolationError: Key (match_id) is not present in table "matches"`

**Causa:** `_load_match_players()` intenta insertar jugadores cuyo `match_id` no existe en `public.matches` (porque el match fue saltado por falta de fecha, o no existe en el CSV de matches).

**Solución:** La función filtra contra `public.matches` y solo inserta players con match_id existente.

### 4. Integration tests fallan con `password authentication failed`

**Causa:** `conftest.py` usaba `postgres_port="5432"` pero Docker expone PostgreSQL en `5434:5432`.

**Solución:** El puerto en el fixture es ahora `"5434"`.

### 5. Integration tests fallan con `ForeignKeyViolationError` al truncar

**Causa:** `truncate_public_tables()` omitía tablas como `referees`, `stadiums`, `tournament_teams`, `players` que tienen FKs hacia `teams`.

**Solución:** La función ahora trunca en orden child→parent respetando todas las FKs.

### 6. Worker no aparece en `docker compose ps`

**Causa:** El service name es `worker` (no `fifa-workers`). `fifa-workers` es solo el `container_name`.

```bash
# ✅ Correcto
docker compose logs worker

# ❌ Incorrecto
docker compose logs fifa-workers
```

### 7. `uv run pytest` falla por sintaxis TOML

**Causa:** Comilla faltante en `pyproject.toml`:
```toml
"pyarrow>=14.0.0,     # ← falta "
"pyarrow>=14.0.0",    # ← correcto
```

### 8. `match_datetime` NOT NULL violada

**Solución implementada:** `_load_matches()` en `load_w3.py` skip rows con fecha nula:

```python
match_dt = parse_datetime_csv(str(r["datetime"])) if r["datetime"] else None
if match_dt is None:
    log.warning("w3.match_skip_no_datetime", match_id=match_id)
    continue
```

### 9. Migration `005_w2_clean_columns.sql` destructiva

**Problema:** Usaba `DROP TABLE IF EXISTS` + `CREATE TABLE` sin `IF NOT EXISTS`, destruyendo datos de `dead_letter` en cada re-ejecución.

**Solución:** Cambiado a `CREATE TABLE IF NOT EXISTS` — ahora es 100% idempotente.

---

## Project Structure

```
.
├── backend/                    # FastAPI REST API
├── workers/                    # ETL Pipeline
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── src/worker/
│   │   ├── cli.py
│   │   ├── core/
│   │   │   ├── config.py       # Settings (pydantic-settings)
│   │   │   ├── db.py
│   │   │   └── storage.py      # MinIO client wrapper
│   │   ├── ingestion/          # W1
│   │   │   └── ingest_w1.py
│   │   ├── cleaning/           # W2
│   │   │   └── clean_w2.py
│   │   ├── loading/            # W3
│   │   │   └── load_w3.py
│   │   ├── validators/
│   │   │   ├── rules.py
│   │   │   └── schemas.py
│   │   └── utils/
│   │       ├── constants.py
│   │       └── helpers.py
│   └── tests/
│       ├── unit/
│       │   ├── test_helpers.py
│       │   ├── test_rules.py
│       │   ├── test_schemas.py
│       │   └── test_cli.py
│       └── integration/
│           ├── conftest.py
│           ├── test_w1_ingest.py
│           ├── test_w2_clean.py
│           └── test_w3_load.py
├── frontend/
├── db/
│   ├── migrations/             # 000 → 010
│   ├── dml/
│   │   └── dml_complete.sql
│   └── scripts/
│       ├── run_migrations.sh
│       └── run_dml.sh
├── data/
│   ├── raw/                    # CSVs originales
│   ├── processed/
│   └── samples/
├── infra/
│   └── nginx/
├── docker-compose.yml
└── README.md
```

---

## Licencia

```
MIT License

Copyright (c) 2026 Platform Data Studio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
