# Incident Captain - MacBook Neo Execution Board

Goal: Win Track 1 (Enterprise Agent) with a production-style Coral-powered incident investigation agent.

## 1) Hard Requirements (Eligibility)
- [ ] Star the Coral GitHub repo.
- [ ] Join Coral Discord.
- [ ] Build code and assets during hackathon window.
- [ ] Keep project as a new build (not a modified old product).

## 2) Scope Lock (Track 1)
- [ ] Problem: Incident triage is slow and fragmented across tools.
- [ ] Outcome: Generate a root-cause briefing in one workflow run.
- [ ] Required sources: pagerduty, github, slack, datadog OR openobserve.
- [ ] Stretch source: statusgator.

## 3) Build Phases

### Phase 0 - Setup & Access (2-3 hours)
- [ ] Install Coral and confirm `coral sql` runs.
- [ ] Run `coral source discover` and capture supported sources.
- [ ] Add each target source with `coral source add --interactive <source>`.
- [ ] Validate with `coral source test <source>`.
- [ ] Log issues and fallback source choices.

### Phase 1 - Data Contract (3-4 hours)
- [ ] Query `coral.tables`, `coral.columns`, `coral.filters`, `coral.inputs`.
- [ ] Build canonical join-key map (service, repo, incident_id, time window, user ids).
- [ ] Define required filters for each core table.
- [ ] Freeze v1 schema map in `deliverables/docs/schema-map.md`.

### Phase 2 - SQL Intelligence Core (5-7 hours)
- [ ] Implement SQL 01: active critical incidents.
- [ ] Implement SQL 02: incident-to-recent-deploy correlation.
- [ ] Implement SQL 03: error/latency spike context.
- [ ] Implement SQL 04: team comms context.
- [ ] Implement SQL 05: final joined incident brief dataset.
- [ ] Add validation queries and sample outputs.

### Phase 3 - Agent Workflow over MCP (4-6 hours)
- [ ] Configure MCP (`coral mcp-stdio`).
- [ ] Build deterministic workflow:
  1. discover catalog
  2. select query template
  3. execute SQL
  4. produce structured briefing
- [ ] Add strict response schema (confidence, impact, evidence, actions).

### Phase 4 - Product Surface (4-6 hours)
- [ ] Build minimal UI or CLI wrapper for "Analyze Incident".
- [ ] Render: summary, likely root cause, impacted services, owners, evidence links.
- [ ] Add Markdown export for Slack/incident channels.

### Phase 5 - Reliability, Security, Telemetry (2-3 hours)
- [ ] Enable OTEL traces and capture end-to-end latency.
- [ ] Document least-privilege token scopes.
- [ ] Add graceful degradation when a source is unavailable.
- [ ] Confirm no secret output in logs or demo screens.

### Phase 6 - Demo & Submission (3-5 hours)
- [ ] Rehearse 3-minute live flow.
- [ ] Record fallback demo video.
- [ ] Capture before/after metric (triage time saved).
- [ ] Finalize README, architecture, metrics, and run instructions.

## 4) 48-Hour Sprint Cadence
- Day 1 AM: Setup + source auth + schema map
- Day 1 PM: SQL core complete
- Day 1 Night: MCP workflow complete
- Day 2 AM: UI/presentation layer
- Day 2 PM: telemetry, security, failure handling
- Day 2 Evening: demo rehearsal + final submission

## 5) Definition of Done
- [ ] 4+ source end-to-end run succeeds.
- [ ] One-command or one-click reproducible demo path.
- [ ] Measurable impact claim with evidence.
- [ ] Submission bundle complete.
- [ ] Backup demo video ready.
