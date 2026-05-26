# Contributing Workflow

This project uses a simple feature-first git workflow optimized for solo development with clean history.

## Branch Strategy

- `main`: stable branch, always runnable
- `feat/<short-topic>`: new feature work
- `fix/<short-topic>`: bug fixes
- `docs/<short-topic>`: documentation-only changes
- `chore/<short-topic>`: maintenance, tooling, config updates
- `test/<short-topic>`: test-focused updates

Examples:
- `feat/incident-brief-parser`
- `fix/coral-binary-detection`
- `docs/demo-runbook`

## Commit Message Style

Use concise, feature-scoped commit messages:

`<type>: <what changed>`

Types:
- `feat`
- `fix`
- `docs`
- `test`
- `chore`
- `refactor`
- `perf`
- `merge`

Examples:
- `feat: add markdown exporter for incident briefs`
- `fix: handle missing coral binary with actionable error`
- `docs: add submission checklist`

## Daily Flow

1. Create a branch from `main`:
   - `git checkout main`
   - `git pull`
   - `git checkout -b feat/<topic>`
2. Commit in small logical chunks.
3. Rebase or merge `main` as needed.
4. Merge back to `main` when stable.
5. Push:
   - `git push -u origin <branch>`

## Quality Gate Before Merge

- Run tests: `python -m pytest -q`
- Ensure key CLI paths run:
  - `python -m incident_captain.cli --help`
- Keep docs updated for behavior changes.

