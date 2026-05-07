# FIFA World Cup Data Platform

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-00A98F?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![uv](https://img.shields.io/badge/uv-0.6+-DE5FE9?logo=python&logoColor=white)](https://github.com/astral-sh/uv)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![MinIO](https://img.shields.io/badge/MinIO-S3--compatible-FF6600?logo=minio&logoColor=white)](https://min.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        nginx (reverse proxy)                 │
│                         :8080 → :80                          │
└──────────────────┬──────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────────┐
│                    FastAPI Backend (app/)                     │
│              REST API · OpenAPI · JWT Auth · Rate Limit       │
└───────┬──────────────────────────────┬──────────────────────┘
        │                              │
┌───────▼──────────┐    ┌──────────────▼──────────────────────┐
│   PostgreSQL 15   │    │     ETL Workers (workers/)          │
│   data-world-cup  │    │     ┌──────────────────────────┐   │
│   :5434 → :5432   │    │     │  W1 — Ingest (Extract)    │   │
└───────────────────┘    │     │  W2 — Clean (Validate)    │   │
                         │     │  W3 — Load (Transform)    │   │
┌───────────────────┐    │     │  Analysis (8 charts)      │   │
│    MinIO (S3)      │    │     └──────────────────────────┘   │
│   :9000 (api)      │    └──────────────────────────────────┘
│   :9001 (console)  │
└───────────────────┘
```

---

## Project Structure

```
.
├── backend/                   # FastAPI REST API
│   ├── app/
│   │   ├── main.py           # Entrypoint + OpenAPI contract
│   │   ├── api/              # Route handlers
│   │   ├── core/             # Config, security, DB
│   │   ├── models/           # SQLAlchemy ORM models
│   │   └── schemas/          # Pydantic request/response
│   └── pyproject.toml        # Backend dependencies
│
├── workers/                   # ETL Pipeline (uv)
│   ├── pyproject.toml        # Worker dependencies
│   ├── Dockerfile            # Multi-stage uv build
│   └── src/worker/
│       ├── cli.py            # CLI orchestrator (fifa-worker)
│       ├── core/             # Config, DB pool, MinIO client
│       ├── ingestion/        # W1 — Extract & stage
│       ├── cleaning/         # W2 — Validate
│       ├── loading/          # W3 — Transform & load
│       └── analysis/         # Charts & analytics
│
├── frontend/                  # Web UI
├── db/                        # SQL scripts & migrations
│   ├── postgres-sql/         # Init & DDL
│   └── dml/                  # Sample data
│
├── data_raw/                  # Source CSV files
├── infra/                     # nginx, monitoring
├── tests/                     # Integration tests
│
├── docker-compose.yml         # Full stack orchestration
├── .env                       # Local environment (gitignored)
├── .env.example               # Environment template
└── .gitignore
```

---

## Technologies

| Layer | Technology | Purpose |
|---|---|---|
| **API** | FastAPI + Uvicorn | RESTful HTTP API with auto-generated OpenAPI docs |
| **Database** | PostgreSQL 15 | Relational data store with `raw.*` and `public.*` schemas |
| **Object Storage** | MinIO | S3-compatible storage for raw CSVs and Parquet exports |
| **ETL** | Python 3.12 + uv | Pipeline workers (ingest → clean → load → analyze) |
| **Container** | Docker Compose | Multi-service orchestration with health checks |
| **Auth** | JWT (python-jose) + Argon2 | Bearer token authentication |
| **Linting** | Ruff + mypy | Static analysis and type checking |
| **Testing** | pytest + pytest-asyncio | Async test suite with coverage |

---

## Getting Started

### Prerequisites

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Docker Desktop (or Docker Engine + Compose)

### 1. Environment Setup

```bash
# Clone the repository
git clone <repo-url>
cd world_cup_soccer_blog

# Copy environment template (fill with your values)
cp .env.example .env
```

### 2. Run Full Stack (Docker)

```bash
# Build and start all services
docker compose up --build
```

This launches:
| Service | URL | Description |
|---|---|---|
| API | `http://localhost:8000/docs` | Swagger UI |
| PostgreSQL | `localhost:5434` | Database (via host) |
| MinIO API | `http://localhost:9000` | S3 endpoint |
| MinIO Console | `http://localhost:9001` | Admin UI |
| nginx | `http://localhost:8080` | Reverse proxy |

### 3. Run ETL Workers

```bash
# Build and run the worker container
docker compose up --build worker
```

Or run locally (requires PostgreSQL + MinIO running):

```bash
cd workers
uv sync                      # Install dependencies
uv run fifa-worker --help    # Show available commands
uv run fifa-worker --ingest  # Run W1 — Extract & stage
uv run fifa-worker --all     # Run full pipeline
```

### 5. Development Workflow

```bash
# Backend (development mode with hot reload)
uv run uvicorn app.main:app --reload

# Lint & format
uv run ruff check . && uv run ruff format .

# Type check
uv run mypy src/

# Run tests
uv run pytest -v
```

---

## ETL Pipeline

The worker CLI (`fifa-worker`) orchestrates a 4-stage ETL pipeline:

| Stage | Flag | Module | Description |
|---|---|---|---|
| **W1 — Ingest** | `--ingest` | `ingestion/ingest_w1.py` | Read CSV → upload to MinIO (raw/) → insert into `raw.*` staging tables |
| **W2 — Clean** | `--clean` | `cleaning/` | Validate types & constraints → dead letter queue |
| **W3 — Load** | `--load` | `loading/` | Transform & upsert into `public.*` → export Parquet to MinIO |
| **Analysis** | `--analysis` | `analysis/` | Generate 8 chart types from warehouse data |

```bash
uv run fifa-worker --ingest    # Stage 1 only
uv run fifa-worker --all       # Full pipeline
```

### Data Flow

```
CSV files (data_raw/)
    │
    ▼
┌─────────────────────┐     ┌────────────────┐     ┌──────────────────┐
│  W1 — Ingest        │────▶│  MinIO (raw/)   │     │  raw.* tables     │
│  pandas (str dtype) │     │  + asyncpg      │◀────│  (staging)        │
└─────────────────────┘     └────────────────┘     └──────────────────┘
                                                          │
    ┌──────────────────────────────────────────────────────┘
    ▼
┌─────────────────────┐     ┌────────────────┐     ┌──────────────────┐
│  W2 — Clean         │────▶│  Dead Letter    │     │  public.* tables  │
│  Validate & cast    │     │  (invalid rows) │     │  (prod)           │
└─────────────────────┘     └────────────────┘     └──────────────────┘
                                                          │
    ┌──────────────────────────────────────────────────────┘
    ▼
┌─────────────────────┐     ┌────────────────┐
│  W3 — Load          │────▶│  Parquet → S3   │
│  Transform & upsert │     │  + Refresh MV   │
└─────────────────────┘     └────────────────┘
```

---

## API Documentation

With the stack running, visit:

| Tool | URL |
|---|---|
| **Swagger UI** | `http://localhost:8000/docs` |
| **ReDoc** | `http://localhost:8000/redoc` |
| **OpenAPI JSON** | `http://localhost:8000/openapi.json` |

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `POSTGRES_USER` | PostgreSQL user | `champion07` (dev) |
| `POSTGRES_PASSWORD` | PostgreSQL password | — |
| `POSTGRES_DB` | Database name | `data-world-cup` |
| `DATABASE_URL` | Async DSN (SQLAlchemy format) | — |
| `S3_ENDPOINT` | MinIO/S3 endpoint URL | `http://minio:9000` |
| `S3_ACCESS_KEY` | S3 access key | — |
| `S3_SECRET_KEY` | S3 secret key | — |
| `MINIO_ROOT_USER` | MinIO admin user | `admin` |
| `MINIO_ROOT_PASSWORD` | MinIO admin password | — |

---

## License

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
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
