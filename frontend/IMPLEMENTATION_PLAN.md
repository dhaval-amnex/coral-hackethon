# Frontend Implementation Plan (Phased)

## Objective
Build a web command center for Incident Captain that is demo-ready and operationally useful, wired to the Python backend API.

## Phase 1: App Shell and Navigation
- Build left navigation and top status bar.
- Create section screens:
  - Dashboard
  - Analyze
  - Evidence
  - Readiness
  - Artifacts
  - Run History
- Done when app can switch sections and show stable layout on desktop/mobile.

## Phase 2: Typed API Contract
- Define frontend domain models in `src/lib/types.ts`.
- Define API client wrappers in `src/lib/api.ts`.
- Done when all screens consume typed responses.

## Phase 3: Backend Binding
- Add HTTP server in Python:
  - `GET /api/health`
  - `POST /api/analyze`
  - `GET /api/evidence`
  - `GET /api/readiness`
  - `POST /api/ship-readiness`
  - `GET /api/run-history`
- Add CLI entrypoint: `python -m incident_captain.cli serve-api`.
- Done when frontend can read/write live data flows without mocks.

## Phase 4: Feature Wiring
- Analyze page:
  - incident input
  - run analysis action
  - render summary/confidence/services/owners
- Evidence page:
  - filterable evidence table
- Readiness page:
  - release status + next actions
- Artifacts page:
  - trigger ship-readiness and render output status
- History page:
  - metrics history table
- Done when all pages are actionably connected to backend endpoints.

## Phase 5: Quality and Demo Hardening
- Add loading/error/empty states across screens.
- Verify `npm run lint`, `npm run typecheck`, `npm run build`.
- Verify backend server command and CORS behavior.
- Done when end-to-end demo flow is stable.

## Runbook
1. Start backend API:
   - `python -m incident_captain.cli serve-api --host 127.0.0.1 --port 8787`
2. Start frontend:
   - `cd frontend`
   - `npm run dev`
3. Open UI and run:
   - Analyze incident
   - Review evidence
   - Run ship-readiness
   - Validate readiness and scorecard state

## Next Extensions (Optional)
- Add polling/progress timeline for long operations.
- Add source-health badges from dedicated API endpoint.
- Add side panel for workflow log step details.
