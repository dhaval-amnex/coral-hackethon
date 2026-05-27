# Incident Captain Frontend

This frontend is the live command center for Incident Captain, built with React + TypeScript + Vite.

## Local Run

```bash
cd frontend
npm install
npm run dev
```

Default app URL: `http://127.0.0.1:5173`

Backend API base is controlled by `VITE_API_BASE_URL` (defaults to `http://127.0.0.1:8787`).

## Quality Checks

```bash
npm run typecheck
npm run build
```

## E2E Smoke Tests

One-time browser setup:

```bash
npx playwright install chromium
```

Run smoke tests:

```bash
npm run e2e
```

The smoke tests mock API calls so they can run without live PagerDuty/GitHub/Slack/Datadog credentials.
