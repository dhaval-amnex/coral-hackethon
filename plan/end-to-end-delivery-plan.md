# End-to-End Delivery Plan (Codex-Owned)

Status: Active
Owner: Codex
Objective: Deliver a Track 1-winning Enterprise Agent submission (Incident Captain) with production-quality demo assets.

## Delivery Contract
- Codex will execute all technical work end-to-end in this repository.
- Codex will maintain execution artifacts, implementation, tests, docs, and demo runbooks.
- User provides source credentials/tokens only when required (never committed).
- Any hard blocker is converted into a concrete unblock checklist.

## Success Criteria
1. Functional: Incident analysis workflow runs across 4+ Coral sources.
2. Technical: MCP-integrated agent flow, multi-source SQL joins, deterministic brief output.
3. Product: Simple runnable interface (CLI or web) that produces incident brief and markdown export.
4. Trust: Security and telemetry documented and demonstrated.
5. Submission: Demo-ready package with metrics and fallback recording plan.

## Execution Streams

### Stream A: Platform Setup
- Install/runtime validation for Coral and local dev stack.
- Source onboarding scripts and health checks.
- Config templates without secrets.

Exit gate:
- `coral sql` operational and all chosen sources pass `coral source test`.

### Stream B: Data Intelligence Layer
- Catalog discovery scripts.
- Schema mapping and canonical key normalization.
- Hardened SQL templates for incidents, deploy correlation, telemetry, and comms.

Exit gate:
- All 5 core SQL queries run successfully on real connected data.

### Stream C: Agent Orchestration (MCP)
- MCP wiring and deterministic workflow.
- Structured JSON output schema.
- Failure-aware partial evidence handling.

Exit gate:
- Single command execution generates structured incident brief.

### Stream D: App Surface
- Thin app wrapper (`analyze incident`) with concise rendering.
- Markdown export for sharing.

Exit gate:
- One-click/one-command demo flow from incident ID to brief export.

### Stream E: Reliability & Security
- Telemetry instrumentation and run metrics capture.
- Security checklist completion and token scope verification.

Exit gate:
- Latency + reliability metrics collected; security checklist complete.

### Stream F: Submission & Demo
- README, architecture summary, metrics report, runbook.
- 3-minute demo script and backup run path.

Exit gate:
- Submission checklist fully complete and rehearsed.

## Implementation Sequence (No Ambiguity)
1. Scaffold app codebase and scripts.
2. Add source-health and catalog-discovery automation.
3. Implement SQL execution module + template loader.
4. Implement incident brief composer.
5. Add CLI entrypoint and markdown export.
6. Add MCP-mode orchestration support.
7. Add telemetry hooks + timing metrics.
8. Finalize docs + demo assets.

## Risks and Mitigations
- Risk: Credential delays.
  - Mitigation: Build full flow with mock adapters, then switch to real data.
- Risk: Schema mismatch across sources.
  - Mitigation: Runtime catalog inspection + mapping config.
- Risk: Live demo instability.
  - Mitigation: Warm-up query cache + backup scenario + recorded fallback.

## Blocker Protocol
When blocked, Codex will:
1. Document exact blocker and impact.
2. Provide minimum required user input.
3. Continue parallel non-blocked streams.

## Immediate Build Sprint Plan (Next 6-8 Hours)
1. Create runnable app skeleton (CLI-first).
2. Implement SQL template runner and config.
3. Implement JSON brief schema and markdown renderer.
4. Add incident workflow command.
5. Add local tests for formatter and scoring logic.
6. Update README with exact run commands.

## Inputs Needed From User (Only When Reaching Integration)
- API credentials for chosen sources (entered locally, never stored in repo).
- One or two incident IDs for real data validation.

## Daily Cadence
- Start: status + next 3 tasks.
- Mid: blockers + decisions.
- End: completed checklist + next sprint goals.
