FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "fifa-worker", "--ingest"]
