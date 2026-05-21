# FIFA World Cup Data Platform

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-00A98F?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![MinIO](https://img.shields.io/badge/MinIO-S3--compatible-FF6600?logo=minio&logoColor=white)](https://min.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![uv](https://img.shields.io/badge/uv-0.6+-DE5FE9?logo=python&logoColor=white)](https://github.com/astral-sh/uv)
[![Async](https://img.shields.io/badge/Async-asyncpg%20%7C%20httpx-0EA5E9?logo=python&logoColor=white)](https://github.com/MagicStack/asyncpg)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Mapa Maestro — Arquitectura del Sistema

```
                                ╔═══════════════════════════════════════════════════════════╗
                                ║                    nginx (reverse proxy)                  ║
                                ║                    :8080 → :80 (api-gateway.conf)         ║
                                ╚══════════════════════╤════════════════════════════════════╝
                                                       │
                                ╔══════════════════════▼════════════════════════════════════╗
                                ║              FastAPI Backend  (backend/src/app/)           ║
                                ║  ┌────────────┬────────────┬────────────┬──────────────┐  ║
                                ║  │  api/routes │ schemas/   │ models/     │ core/       │  ║
                                ║  │  (REST)     │ (Pydantic) │ (SQLAlchemy)│ config/     │  ║
                                ║  │  handlers   │  request   │  ORM models │ security/   │  ║
                                ║  │             │  response  │             │ db session  │  ║
                                ║  └──────┬──────┴─────┬──────┴──────┬──────┴──────────────┘  ║
                                ╚═════════╪═══════════╪═════════════╪═════════════════════════╝
                                          │           │             │
              ╔═══════════════════════════╪═══════════╪═════════════╪═══════════════════════╗
              ║                PostgreSQL 15  (data-world-cup)  :5434 → :5432               ║
              ║  ┌────────────────────────────────────────────────────────────────────────┐ ║
              ║  │  Schema: raw       │  Schema: public     │  Schema: warehouse           │ ║
              ║  │  ──────────        │  ──────────         │  ──────────────────          │ ║
              ║  │  wc_winners ↓text  │  teams              │  vw_* materialized views    │ ║
              ║  │  wc_matches  ↓text │  tournaments        │                              │ ║
              ║  │  wc_players  ↓text │  rounds             │  Schema: audit               │ ║
              ║  │  dead_letter       │  matches            │  ──────────────────          │ ║
              ║  │                    │  match_players      │  auth_refresh_tokens         │ ║
              ║  │                    │  users              │  auth_password_resets        │ ║
              ║  │                    │                     │  etl_run_log                 │ ║
              ║  └────────────────────────────────────────────────────────────────────────┘ ║
              ╚═══════════════════════════╤═══════════════╤══════════════════════════════════╝
                                          │               │
              ╔═══════════════════════════▼═══════════════▼══════════════════════════════════╗
              ║                         ETL Pipeline Workers (workers/src/worker/)           ║
              ║                                                                              ║
              ║  ┌─────────────────────┐    ┌─────────────────────┐    ┌───────────────────┐ ║
              ║  │  W1 — Ingest        │    │  W2 — Clean         │    │  W3 — Load        │ ║
              ║  │  (Extract)          │───▶│  (Validate)         │───▶│  (Transform)      │ ║
              ║  │                     │    │                     │    │                   │ ║
              ║  │  CSV → pandas(str)  │    │  read raw.*         │    │  _is_valid=TRUE   │ ║
              ║  │  → MinIO raw/       │    │  → validate rules   │    │  → cast types     │ ║
              ║  │  → raw.* INSERT     │    │  → UPDATE _is_valid │    │  → UPSERT public.*│ ║
              ║  │  → SHA-256 hash     │    │  → dead_letter      │    │  → Parquet export │ ║
              ║  └─────────────────────┘    └─────────────────────┘    └───────────────────┘ ║
              ║                                                                              ║
              ║                     fifa-worker --all  (W1 → W2 → W3)                        ║
              ╚═══════════════════════════╤═══════════════════════════════════════════════════╝
                                          │
              ╔═══════════════════════════▼═══════════════════════════════════════════════════╗
              ║                    MinIO (S3-compatible Storage)                             ║
              ║  ┌─────────────┬─────────────┬─────────────┬──────────────────────────────┐  ║
              ║  │  Bucket:    │  Bucket:    │  Bucket:    │  Console: :9001              │  ║
              ║  │  raw/       │  parquet/   │  processed/ │  API:     :9000              │  ║
              ║  │  raw CSV    │  .parquet   │  clean CSVs │  Admin: admin / <password>   │  ║
              ║  └─────────────┴─────────────┴─────────────┴──────────────────────────────┘  ║
              ╚═══════════════════════════════════════════════════════════════════════════════╝

                                          ┌──────────────────────┐
                                          │   Frontend Web UI    │
                                          │   (frontend/)        │
                                          └──────────────────────┘

                              Capa de Pruebas:
                              ┌────────────────────────────────────────────────────────┐
                              │  tests/unit/  →  helpers, rules, schemas, cli          │
                              │  tests/integration/  →  W1 ingest, W2 clean, W3 load   │
                              │  pytest + pytest-asyncio + pytest-cov                  │
                              └────────────────────────────────────────────────────────┘
```

---

## Pipeline ETL — Detalle por Etapa

### W1 — Ingest (Extract)

Lee los CSVs crudos del directorio `data/raw/` y los sube al storage y base de datos sin transformación alguna.

```bash
fifa-worker --ingest
```

| Responsabilidad | Implementación |
|---|---|
| Lectura CSV | `pandas.read_csv(dtype=str, keep_default_na=False)` — sin inferencia de tipos |
| Upload raw | MinIO bucket `raw/` — preservation bit a bit del archivo original |
| Staging DB | `raw.wc_winners`, `raw.wc_matches`, `raw.wc_players` — columnas TEXT |
| Trazabilidad | SHA-256 del archivo + `_source_file` por fila |
| Header | `matches` no tiene cabecera → `header=None, names=config["columns"]` |

**Anti-corruption layer:** En esta etapa NO se castea, NO se valida, NO se transforma. El CSV entra tal cual.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  wc_*.csv    │───▶│  pandas(str) │───▶│  raw.* (TEXT)│
│  data/raw/   │    │  + SHA-256   │    │  + MinIO     │
└──────────────┘    └──────────────┘    └──────────────┘
```

### W2 — Clean (Validate)

Lee las filas pendientes (`_is_valid IS NULL`) de `raw.*`, las valida contra reglas de negocio, y marca su estado.

```bash
fifa-worker --clean
```

| Dataset | Reglas de validación | Errores posibles |
|---|---|---|
| **winners** | `year` [1930-2030], `winner` presente, `goals_scored` ≥ 0, `qualified_teams` [1-48], avg goles/partido | `MISSING_YEAR`, `MISSING_WINNER`, `NEGATIVE_GOALS_SCORED`, `MISSING_PODIUM` (warning) |
| **matches** | `match_id` ≥ 1, `stage` presente, goles ≥ 0, iniciales 2-3 letras, `round_id` ≥ 1 | `INVALID_MATCH_ID`, `MISSING_STAGE`, `INVALID_HOME_GOALS`, `MISSING_HOME_INITIALS` |
| **players** | `round_id` ≥ 1, `match_id` ≥ 1, `team_initials` presentes, `line_up` S/N, `player_name` presente | `INVALID_ROUND_ID`, `MISSING_TEAM_INITIALS`, `INVALID_LINEUP_TYPE`, `MISSING_PLAYER_NAME` |

```
raw.* / _is_valid=NULL     raw.* / _is_valid=TRUE
         │                          │
         ▼                          ▼
┌────────────────────┐    ┌────────────────────┐
│  ValidationResult   │    │  Clean{Dataset}Row │
│  rules.py           │───▶│  schemas.py        │
│  - errors[]         │    │  (Pydantic v2)     │
│  - warnings[]       │    └────────────────────┘
│  - is_valid         │              │
│  - clean_row        │    raw.* / _is_valid=FALSE
└────────────────────┘              │
         │                          ▼
         ▼                 ┌────────────────────┐
┌────────────────┐        │  raw.dead_letter   │
│  is_valid=TRUE  │        │  - _error_code     │
│  → UPDATE TRUE  │        │  - _error_detail   │
│  is_valid=FALSE │        │  - _rejected_at    │
│  → UPDATE FALSE │        └────────────────────┘
│  → INSERT dead  │
└────────────────┘
```

La tasa de rechazo (`rejection_rate`) es monitoreada: si supera el 10%, el pipeline **no continúa** a W3 (señal de problema en los datos fuente).

### W3 — Load (Transform & Load)

Lee solo las filas validadas (`_is_valid = TRUE`) de `raw.*`, transforma los tipos y hace upsert en `public.*`.

```bash
fifa-worker --load
```

| Orden | Tabla destino | Fuente | Tipo de carga |
|---|---|---|---|
| 1 | `public.teams` | `raw.wc_matches` + `raw.wc_players` (DISTINCT initials) | `INSERT ... ON CONFLICT DO UPDATE` |
| 2 | `public.tournaments` | `raw.wc_winners` | `INSERT ... ON CONFLICT (year) DO UPDATE` |
| 3 | `public.rounds` | `raw.wc_matches` (DISTINCT round_id + year) | `INSERT ... ON CONFLICT (round_id) DO UPDATE` |
| 4 | `public.matches` | `raw.wc_matches` | `INSERT ... ON CONFLICT (match_id) DO UPDATE` |
| 5 | `public.match_players` | `raw.wc_players` | DELETE + INSERT (replace por match) |
| 6 | Warehouse | `SELECT warehouse.refresh_all()` | Materialized views refresh |
| 7 | Parquet export | `public.*` → `.parquet` → MinIO | `pandas.to_parquet()` |

**Transformaciones aplicadas:**
- `parse_int()` — conversión segura de strings a enteros
- `parse_attendance()` — manejo de formato europeo (punto como separador de miles: `"590.549"` → `590549`)
- `parse_datetime_csv()` — parser específico para `"13 Jul 1930 - 15:00"`
- `normalize_text()` — strip + truncate opcional por límite de columna
- `normalize_initials()` — uppercase + validación 2-3 caracteres
- `normalize_team_names()` — title case (`"germany fr"` → `"Germany Fr"`)

```
raw.wc_winners  (_is_valid=TRUE)   ───▶  public.tournaments
raw.wc_matches  (_is_valid=TRUE)   ───▶  public.rounds
                +                  ───▶  public.matches
raw.wc_players  (_is_valid=TRUE)   ───▶  public.match_players
raw.wc_matches  (_is_valid=TRUE)
raw.wc_players  (_is_valid=TRUE)   ───▶  public.teams

Todas las tablas public.*         ───▶  warehouse.refresh_all()
                                      ───▶  MinIO parquet/
```

---

## Stack Tecnológico

### Lenguajes y Entornos

| Tecnología | Versión | Propósito |
|---|---|---|
| **Python** | ≥ 3.12 | Lenguaje principal — type hints nativos, pattern matching, mejoras en asyncio |
| **Docker Compose** | v2.27+ | Orquestación multi-contenedor con health checks y dependencias |
| **nginx** | 1.25+ | Reverse proxy con rate limiting y buffering |

### Backend — API REST

| Librería | Versión | Propósito |
|---|---|---|
| `fastapi` | ≥ 0.111 | Framework REST con OpenAPI auto-documentado |
| `uvicorn[standard]` | ≥ 0.29 | Servidor ASGI con uvloop + httptools |
| `sqlalchemy[asyncio]` | ≥ 2.0 | ORM asíncrono con async engine y session factory |
| `alembic` | ≥ 1.13 | Versionado de migraciones DDL |
| `python-jose[cryptography]` | ≥ 3.3 | JWT creation & verification (Bearer tokens) |
| `passlib[argon2]` | ≥ 1.7.4 | Hashing de passwords con Argon2id (recomendación OWASP) |
| `python-multipart` | ≥ 0.0.9 | Parsing de form data para login |
| `slowapi` | ≥ 0.1.9 | Rate limiting por IP (protección DDoS) |
| `prometheus-fastapi-instrumentator` | ≥ 6.1 | Métricas Prometheus para monitoreo |

### Pipeline ETL

| Librería | Versión | Propósito |
|---|---|---|
| `asyncpg` | ≥ 0.29 | Driver PostgreSQL asíncrono — pool de conexiones, queries parametrizadas |
| `pandas` | ≥ 2.2 | Lectura de CSVs sin inferencia de tipos (`dtype=str`) |
| `minio` | ≥ 7.2 | Cliente S3 para MinIO — subida de CSVs raw y Parquet |
| `pydantic` v2 | ≥ 2.6 | Schemas dual-layer: `Raw*Row` (str) y `Clean*Row` (tipado) |
| `structlog` | ≥ 24.1 | Logging estructurado JSON con contexto por worker |
| `pydantic-settings` | ≥ 2.2 | Config tipada vía variables de entorno |

### Base de Datos — PostgreSQL 15

| Schema | Propósito | Tablas |
|---|---|---|
| **raw** | Staging — datos tal cual del CSV (TEXT) | `wc_winners`, `wc_matches`, `wc_players`, `dead_letter` |
| **public** | Producción — datos tipados con FKs y constraints | `teams`, `tournaments`, `rounds`, `matches`, `match_players`, `users` |
| **warehouse** | Materialized views para reporting | `vw_*` (refrescadas por W3) |
| **audit** | Seguridad y trazabilidad | `auth_refresh_tokens`, `auth_password_resets`, `etl_run_log` |

### Testing

| Herramienta | Versión | Propósito |
|---|---|---|
| `pytest` | ≥ 8.1 | Test runner |
| `pytest-asyncio` | ≥ 0.23 | Soporte de fixtures y tests asíncronos |
| `pytest-cov` | ≥ 5.0 | Reportes de cobertura |
| `ruff` | ≥ 0.4 | Linter + formatter (100× más rápido que flake8) |
| `mypy` | ≥ 1.9 | Type checking estricto con plugin de Pydantic |
| `httpx` | ≥ 0.27 | Cliente HTTP asíncrono para tests de API |
| `factory-boy` | ≥ 3.3 | Factories de datos de prueba |

### Tests Implementados

```
workers/tests/
└── unit/
    ├── test_helpers.py      68 tests  — parse_*, normalize_*, clean_cell, slugify
    ├── test_rules.py        35 tests  — 5 validadores (winners, matches, players, team, round)
    ├── test_schemas.py      36 tests  — Raw + Clean Pydantic models
    └── test_cli.py           8 tests  — argparse flags (ingest/clean/load/all)
                    ─────────
    Total:                  147 tests  (⚠  unit tests)

tests/
└── integration/
    ├── conftest.py          — Fixtures: PG pool, MinIO client, sample CSVs
    ├── test_w1_ingest.py    — W1: CSV → MinIO → raw.* staging
    ├── test_w2_clean.py     — W2: raw.* → validation → dead_letter
    └── test_w3_load.py      — W3: raw.* → public.* upsert → Parquet
                    ─────────
    Total:                   ~40 tests  (requiere PG + MinIO activos)
```

---

## Convenciones de Diseño

### Seguridad (Anti SQL Injection)

Todas las queries usan **parámetros posicionales `$N` de asyncpg**:

```python
# ✅ Correcto — valores en $1, $2, nunca concatenados
await conn.execute(
    "INSERT INTO raw.wc_winners (_source_file, year) VALUES ($1, $2)",
    filename, year,
)

# ❌ Prohibido — construcción con f-strings o concatenación
await conn.execute(
    f"INSERT INTO raw.wc_winners VALUES ('{filename}', {year})"  # NO
)
```

Los únicos f-strings permitidos son para nombres de tablas y columnas que vienen de `constants.py` (nunca de input externo).

### Pipeline Idempotencia

- DML usa `INSERT ... ON CONFLICT DO NOTHING` / `DO UPDATE`
- W3 upserts con `ON CONFLICT` en todas las tablas public.*
- W2 solo marca `_is_valid` sobre filas que estaban `IS NULL`
- Múltiples ejecuciones del pipeline producen el mismo resultado

### Separación de Capas (Raw vs Clean)

```
RAW (raw.*)                          CLEAN (public.*)
──────────────────────────           ──────────────────────────
Columna: TEXT                       Columna: tipada (INT, VARCHAR, TIMESTAMPTZ)
Constraint: ninguna                 Constraint: NOT NULL, CHECK, FK, UNIQUE
Índices: ninguno                    Índices: B-tree, GiST (trigram)
Propósito: ingestión masiva         Propósito: queries de producción, reportes
Dueño: W1                           Dueño: W3
```
---

## Getting Started

### Prerrequisitos

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Docker Engine + Compose

### Variables de Entorno

Copiar `.env.example` → `.env` y ajustar credenciales:

```env
# PostgreSQL
POSTGRES_USER=champion07
POSTGRES_PASSWORD=change_me_in_production
POSTGRES_DB=data-world-cup

# MinIO
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=change_me_in_production
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=admin
S3_SECRET_KEY=change_me_in_production

# Worker
CSV_SOURCE_PATH=./data
```

### Inicializar Infraestructura

```bash
docker compose up -d postgres minio
```

Las migraciones se ejecutan automáticamente via `db/scripts/run_migrations.sh` (orden alfabético: 000 → 010).

### Ejecutar Pipeline ETL

```bash
# Worker completo (W1 → W2 → W3)
docker compose run --rm worker uv run fifa-worker --all

# Etapas individuales
docker compose run --rm worker uv run fifa-worker --ingest    # W1
docker compose run --rm worker uv run fifa-worker --clean     # W2
docker compose run --rm worker uv run fifa-worker --load      # W3
```

### Ejecutar Tests

```bash
cd workers
uv sync --extra dev

# Unit tests (no requieren servicios)
uv run pytest tests/unit/ -v

# Integration tests (requieren PostgreSQL + MinIO activos)
uv run pytest tests/integration/ -v -m integration

# Todos los tests con cobertura
uv run pytest -v --cov=worker
```

---

## Project Structure

```
.
├── backend/                    # FastAPI REST API
│   └── src/app/
│       ├── main.py            # Entrypoint + OpenAPI
│       ├── api/               # Route handlers
│       ├── core/              # Config, security, DB
│       ├── models/            # SQLAlchemy ORM
│       └── schemas/           # Pydantic request/response
│
├── workers/                    # ETL Pipeline
│   ├── pyproject.toml         # Dependencias + tool config
│   ├── Dockerfile             # Multi-stage build con uv
│   ├── tests/
│   │   └── unit/              # Unit tests (147 tests)
│   │       ├── test_helpers.py
│   │       ├── test_rules.py
│   │       ├── test_schemas.py
│   │       └── test_cli.py
│   └── src/worker/
│       ├── cli.py             # CLI orchestrator (fifa-worker)
│       ├── core/              # Config, DB pool, MinIO client
│       │   ├── config.py      # Settings (pydantic-settings)
│       │   ├── db.py          # Pool factory
│       │   └── storage.py     # MinIO client wrapper
│       ├── ingestion/         # W1 — Extract (pandas + asyncpg)
│       │   └── ingest_w1.py
│       ├── cleaning/          # W2 — Validate (rules + schemas)
│       │   └── clean_w2.py
│       ├── loading/           # W3 — Transform & Load
│       │   └── load_w3.py
│       ├── validators/        # Reglas de negocio + schemas Pydantic
│       │   ├── rules.py       # 5 validadores
│       │   └── schemas.py     # 10 modelos (Raw+Clean)
│       └── utils/             # Helpers + constantes
│           ├── constants.py   # Dataset config, regex, dominios
│           └── helpers.py     # 15+ funciones puras
│
├── frontend/                   # Web UI
├── db/                         # SQL scripts
│   ├── migrations/            # DDL (000 → 010)
│   ├── dml/                   # Seed data (dml_complete.sql)
│   └── scripts/               # run_migrations.sh, run_dml.sh
│
├── data/                       # Fuentes de datos
│   ├── raw/                   # CSVs originales (wc_*.csv)
│   ├── processed/             # Datos limpios post-W2
│   └── samples/               # Versiones reducidas para test
│
├── tests/                      # Integration tests
│   └── integration/
│       ├── conftest.py        # Fixtures PG + MinIO + CSVs
│       ├── test_w1_ingest.py
│       ├── test_w2_clean.py
│       └── test_w3_load.py
│
├── infra/                      # nginx, monitoreo
├── docker-compose.yml          # Orquestación completa
├── .env.example                # Template de entorno
└── README.md
```

---

## Servicios y Puertos

| Servicio | URL | Propósito |
|---|---|---|
| FastAPI | `http://localhost:8000/docs` | Swagger UI |
| PostgreSQL | `localhost:5434` | Base de datos (vía host) |
| MinIO API | `http://localhost:9000` | Endpoint S3 |
| MinIO Console | `http://localhost:9001` | Admin UI |
| nginx | `http://localhost:8080` | Reverse proxy |

---

## Licencia

```
MIT License

Copyright (c) 2024 Platform Data Studio

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
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHER LOSSES, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
```
