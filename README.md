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

## Libraries & Frameworks

### Web & ASGI
| Library | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥ 0.111 | REST API framework with OpenAPI auto-docs |
| `uvicorn[standard]` | ≥ 0.29 | ASGI server (uvloop + httptools) |

### Database & Storage
| Library | Version | Purpose |
|---------|---------|---------|
| `asyncpg` | ≥ 0.29 | Async PostgreSQL driver (connection pool + parameterized queries) |
| `sqlalchemy[asyncio]` | ≥ 2.0 | Async ORM with async engine support |
| `alembic` | ≥ 1.13 | Database migrations (DDL versioning) |
| `minio` | ≥ 7.2 | S3-compatible client for MinIO object storage |

### Pipeline & Data Processing
| Library | Version | Purpose |
|---------|---------|---------|
| `pandas` | ≥ 2.2 | CSV reading, data frames, dtype-preserving ingestion |
| `structlog` | ≥ 24.1 | Structured JSON logging with context binding |
| pydantic v2 | ≥ 2.6 | Dual-layer schemas (`Raw*Row` / `Clean*Row`) for validation |
| `pydantic-settings` | ≥ 2.2 | Type-safe environment variable loading |

### Authentication & Security
| Library | Version | Purpose |
|---------|---------|---------|
| `python-jose[cryptography]` | ≥ 3.3 | JWT token creation & verification |
| `passlib[argon2]` | ≥ 1.7 | Argon2id password hashing (OWASP recommended) |
| `python-multipart` | ≥ 0.0.9 | Form data parsing (login endpoints) |

### Observability & Rate Limiting
| Library | Version | Purpose |
|---------|---------|---------|
| `prometheus-fastapi-instrumentator` | ≥ 6.1 | Prometheus metrics for FastAPI |
| `slowapi` | ≥ 0.1.9 | Rate limiting (DDoS protection) |
| `structlog` | ≥ 24.1 | Request/response structured logging |

### Developer Tooling
| Tool | Version | Purpose |
|------|---------|---------|
| `uv` | ≥ 0.6 | Python package & project manager (fast pip alternative) |
| `ruff` | ≥ 0.4 | Linter + formatter (100× faster than flake8) |
| `mypy` | ≥ 1.9 | Static type checking (strict mode + pydantic plugin) |
| `pytest` | ≥ 8.1 | Test runner with async support |
| `pytest-asyncio` | ≥ 0.23 | Async test fixture support |
| `pytest-cov` | ≥ 5.0 | Coverage reports |
| `httpx` | ≥ 0.27 | Async HTTP test client for FastAPI |
| `factory-boy` | ≥ 3.3 | Test data factories |

### Infrastructure
| Tool | Purpose |
|------|---------|
| **Docker Compose** | Multi-container orchestration (PostgreSQL, MinIO, workers, nginx) |
| **nginx** | Reverse proxy with rate limiting (api-gateway.conf) |
| **PostgreSQL 15** | Relational database with `raw`, `public`, `audit`, `warehouse` schemas |
| **MinIO** | S3-compatible object storage for raw CSVs + Parquet exports |

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

## Detailed Setup Guide

### 1. Clone & Environment

```bash
git clone <repo-url> && cd world_cup_soccer_blog
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# PostgreSQL
POSTGRES_USER=champion07
POSTGRES_PASSWORD=<your_secure_password>
POSTGRES_DB=data-world-cup

# MinIO
MINIO_ROOT_USER=admin
MINIO_ROOT_PASSWORD=<your_minio_password>
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=admin
S3_SECRET_KEY=<your_minio_password>
```

### 2. Initialize Database Schema

The PostgreSQL container auto-executes `db/postgres-sql/init.sql` on first boot.
This creates the 4 schemas and all staging tables:

```bash
docker compose up -d postgres minio
```

Verify with:

```bash
docker compose exec postgres psql -U champion07 -d data-world-cup -c "\dn"
#   List of schemas
#   ──────────────
#    raw
#    public
#    audit
#    warehouse
```

### 3. Run ETL Pipeline

```bash
# Stage 1 — Ingest (CSV → MinIO → raw.*)
docker compose run --rm worker uv run fifa-worker --ingest

# Stage 2 — Clean (validate & cast)
docker compose run --rm worker uv run fifa-worker --clean

# Stage 3 — Load (transform → public.* → Parquet)
docker compose run --rm worker uv run fifa-worker --load

# Full pipeline (W1 → W2 → W3 → Analysis)
docker compose run --rm worker uv run fifa-worker --all
```

### 4. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Swagger UI** | `http://localhost:8000/docs` | — |
| **ReDoc** | `http://localhost:8000/redoc` | — |
| **MinIO Console** | `http://localhost:9001` | `admin` / `<your_password>` |
| **MinIO API** | `http://localhost:9000` | `admin` / `<your_password>` |
| **PostgreSQL** | `localhost:5434` | `champion07` / `<your_password>` |
| **nginx** | `http://localhost:8080` | — |

### 5. Verify Data

```bash
# Check raw staging tables
docker compose exec postgres psql -U champion07 -d data-world-cup -c \
  "SELECT COUNT(*) FROM raw.wc_winners;"

# Check MinIO objects
docker compose exec minio mc ls local/raw/
```

### 6. Worker CLI Reference

```bash
docker compose run --rm worker --help

# Options:
#   --ingest     W1 — Extract CSV → MinIO → raw.*
#   --clean      W2 — Validate & cast → dead_letter
#   --load       W3 — Transform → public.* → Parquet
#   --analysis   W4 — Generate analytics charts
#   --all        Full pipeline (W1 → W2 → W3 → W4)
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
