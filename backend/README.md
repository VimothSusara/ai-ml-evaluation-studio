# AI Dataset Explorer — Backend

## Prerequisites
- Python 3.11+
- Docker
- uv

## Run locally

```bash
cp .env.example .env
docker compose up -d
uv sync
uv run alembic upgrade head
uv run python scripts/seed_superadmin.py
uv run uvicorn app.main:app --reload --port 8000