# Incident Captain: Technical Architecture

## Objective
Reduce incident triage time by generating a root-cause briefing that combines incident context, deployment context, telemetry context, and communication context in one workflow.

## System Components
1. Coral runtime (local): data access layer and SQL execution engine.
2. Sources: pagerduty, github, slack, datadog/openobserve, optional statusgator.
3. Agent runtime: MCP client invoking Coral tools.
4. App layer: thin CLI or UI wrapper.
5. Output layer: structured incident briefing + markdown export.
6. Observability: OpenTelemetry traces/metrics/logs.

## Workflow
1. Agent discovers catalog (`list_catalog`, `describe_table`, `list_columns`).
2. Agent selects SQL templates based on incident type.
3. Agent executes SQL via `sql` tool.
4. Agent composes deterministic JSON briefing.
5. App renders brief and exports markdown.

## Data Contract
- Core entities: incident, service, deployment, error signal, owner, conversation.
- Canonical keys:
  - `service_key`
  - `repo_key`
  - `incident_id`
  - `window_start` / `window_end`
  - `owner_key`
- Join strategy: normalize keys in CTEs before cross-source joins.

## Reliability Strategy
- Per-source timeout guardrails.
- Retry on transient failures.
- Partial-result fallback with confidence downgrade.
- Mandatory source health check before demo.

## Security Strategy
- Read-only least-privilege tokens.
- Secrets only via Coral source inputs (`kind: secret`).
- No token material in logs or screenshots.
- Local-trust-boundary warning in docs.

## Observability Strategy
Track the following:
- End-to-end triage latency.
- SQL query latency by template.
- Source error rates.
- Workflow success rate.
- Brief generation duration.

## Demo Narrative Hooks
- "One workflow, multi-source evidence."
- "Fewer tool hops, faster decisions."
- "Actionable root cause summary with links and owners."
