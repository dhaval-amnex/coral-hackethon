# Incident Captain Frontend Guidance

## What is implemented
- Command center shell with sections:
  - Dashboard
  - Analyze
  - Evidence
  - Readiness
  - Artifacts
  - Run History
- Typed API client and domain models in `src/lib`.
- Frontend wired to backend HTTP API.
- Build and typecheck passing.

## Backend binding
Run backend API server from repo root:

```bash
python -m incident_captain.cli serve-api --host 127.0.0.1 --port 8787
```

Available endpoints:
- `POST /api/analyze`
- `GET /api/evidence?incident_id=...`
- `GET /api/readiness`
- `POST /api/ship-readiness`
- `GET /api/run-history`

## Frontend run
From `frontend/`:

```bash
npm run dev
```

Optional API override:
```bash
cp .env.example .env
# edit VITE_API_BASE_URL if needed
```

## Phase-by-phase next implementation
See:
- `frontend/IMPLEMENTATION_PLAN.md`

