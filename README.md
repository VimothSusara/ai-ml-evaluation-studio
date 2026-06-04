# Tabular ML Evaluation Studio

Upload a CSV, profile it, pick a target column, train a few scikit-learn models, and compare results in one place. Includes job polling, evaluation charts, and single-row inference against the best run.

This repo is a monorepo: `backend/` (FastAPI + Celery) and `frontend/` (Next.js).

### Suggested GitHub repo names

Pick something short you will not regret on a resume link:

| Name | Notes |
|------|--------|
| **`tabular-eval-studio`** | Clear and searchable; my first choice |
| `ml-eval-workbench` | Slightly more generic |
| `csv-model-lab` | Casual, still accurate |
| `ai-ml-evaluation-studio` | Fine if you already use this folder name |

Rename locally with `git remote` after you create the GitHub repo; the code does not depend on the folder name.

---

## What it does

1. **Upload** a CSV (preview + preflight warnings in the UI).
2. **Profile** in a background job — column types, missing counts, auto-drops index junk (`#`, `Unnamed: 0`, etc.).
3. **Validate** a target column (classification vs regression).
4. **Train** one or more models from a DB-backed catalog (Random Forest, Logistic Regression, …).
5. **Review** metrics and plots on the experiment page.
6. **Download** the winning pipeline (joblib + manifest) or **predict** one row in the UI.

Raw text columns (e.g. SMS `Message` bodies) are not first-class features yet — use tabular columns for training in v1, or treat spam/ham style data with **Category** as the target only.

---

## Stack

- **API:** FastAPI, SQLAlchemy, Alembic, JWT auth (optional Google OAuth)
- **Jobs:** Celery + Redis
- **Data:** PostgreSQL (metadata), MinIO (CSV + model artifacts)
- **ML:** pandas, scikit-learn, joblib
- **UI:** Next.js App Router, TanStack Query, shadcn/ui, Recharts

---

## Prerequisites

- Python **3.14+** and [uv](https://docs.astral.sh/uv/)
- Node **20+**
- Docker (Redis + MinIO from `backend/docker-compose.yml`)
- PostgreSQL on localhost (see `backend/.env.example`)

---

## Run locally

### Infrastructure

```powershell
cd backend
docker compose up -d
```

Redis → `6379`. MinIO → API `9000`, console `9001` (`minioadmin` / `minioadmin`).

Create a database (example name from `.env.example`):

```sql
CREATE DATABASE ai_studio_db;
```

### Backend

```powershell
cd backend
copy .env.example .env
# Edit DATABASE_URL and SECRET_KEY

uv sync
uv pip install -e .

uv run alembic upgrade head
uv run python scripts/seed_superadmin.py
uv run python scripts/seed_ml_catalog.py
```

Terminal A — API:

```powershell
uv run uvicorn app.main:app --reload --port 8000
```

Terminal B — worker (on Windows use solo pool):

```powershell
uv run celery -A app.core.celery_app:celery_app worker -l info --pool=solo
```

- http://localhost:8000/docs  
- http://localhost:8000/health  

### Frontend

```powershell
cd frontend
copy .env.local.example .env.local
npm install
npm run dev
```

http://localhost:3000

### Login after seed

- Email: `superadmin@example.com`  
- Password: `SuperAdmin123!`  

Change these in `backend/.env` before seeding if you deploy anywhere real.

---

## First demo (about 10 minutes)

Use a small CSV such as [Titanic `train.csv`](https://www.kaggle.com/competitions/titanic) (use the train file that includes `Survived`).

1. **Datasets** → select file → check preflight → **Upload & profile** → wait for `profiled`.
2. Open the dataset → **Category / target** = `Survived` → **Validate target**.
3. **Load recommended models** → **Review & start training**.
4. Open the experiment → charts, best model, **Use trained model** for a test prediction.

With `--pool=solo`, only one Celery task runs at a time. A huge upload blocks training — watch **Jobs** or profile smaller files first.

**Spam CSV (Category + Message):** target = `Category` only. Do not use `Message` as the target; v1 does not train on free text yet.

---

## Repo layout

```
backend/          FastAPI app, Celery tasks, Alembic, seeds
frontend/         Next.js dashboard
```

More detail: [backend/README.md](backend/README.md), [frontend/README.md](frontend/README.md).

---

## v1 limits (intentional)

- CSV only; no Parquet or database connectors.
- Tabular features (numeric + low-cardinality categorical). High-cardinality text is flagged, not embedded.
- One Celery worker process is assumed on Windows dev (`--pool=solo`).
- Artifacts are joblib + JSON manifest, not ONNX.
- Multiclass ROC is not plotted (binary only).
