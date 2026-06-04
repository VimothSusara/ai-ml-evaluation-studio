# Frontend

Next.js dashboard for the evaluation studio: upload CSVs, walk through target validation and training, then inspect experiments and run inference.

## Requirements

- Node 20+
- Backend at http://localhost:8000 with Celery worker running (jobs otherwise stay queued)

## Setup

```powershell
cd frontend
npm install
copy .env.local.example .env.local
```

`.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_PREFIX=/api/v1
```

## Development

```powershell
npm run dev
```

App: http://localhost:3000

Log in with the seeded account from the root README (`superadmin@example.com` unless you changed seed env vars).

Production build:

```powershell
npm run build
npm run start
```

## Routes

| Path | What you do there |
|------|-------------------|
| `/login`, `/register` | Auth |
| `/datasets` | Upload CSV, inline preview, preflight warnings |
| `/datasets/[id]` | Profile view, readiness, target select, validate, train |
| `/experiments` | Past runs |
| `/experiments/[id]` | Metrics, charts, model table, download + predict |
| `/jobs` | Profiling/training job status |

## How the UI talks to the API

- TanStack Query for datasets, experiments, jobs.
- JWT in `localStorage`, sent as `Authorization: Bearer …` on each request (no cookie session in v1).
- Job cards poll until `completed` or `failed`, then redirect (e.g. to the new dataset or experiment).

Upload flow parses the first ~10 rows in the browser for preview only; the server profile is authoritative for column lists and readiness.

## Project structure (high level)

```
src/
  app/                 App Router pages (dashboard group, auth)
  components/          datasets/, experiments/, jobs/, shared UI
  lib/api/             typed fetch wrappers
  lib/datasets/        profile types
  lib/csv-preview.ts   client preflight + preview parse
  types/               API response shapes
```

Styling: Tailwind + shadcn/ui. Charts: Recharts on the experiment detail page.

## Common issues

**Target dropdown empty** — dataset status must be `profiled`; hard refresh. Columns come from `GET /datasets/{id}/columns`.

**“Re-profile this dataset” on readiness** — profile JSON predates `sanitization`; re-upload or re-run profiling with an updated worker.

**Training button never enables** — validate the target first; fix validation errors (wrong column, text field as target, etc.).

**CORS errors** — `BACKEND_CORS_ORIGINS` in backend `.env` must include `http://localhost:3000`.

## See also

[Root README](../README.md) — architecture, demo datasets, Celery solo-pool note.
