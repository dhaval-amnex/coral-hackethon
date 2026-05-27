from __future__ import annotations

from pathlib import Path
from typing import Any

from .coral import CoralClient, CoralError, QueryRun, render_sql_from_template
from .models import Evidence, IncidentBrief


QUERY_FILES = [
    ("active_incidents", "01_active_critical_incidents.sql"),
    ("deploy_correlation", "02_incident_deploy_correlation.sql"),
    ("telemetry_context", "03_telemetry_spike_context.sql"),
    ("team_comms", "04_team_comms_context.sql"),
    ("final_dataset", "05_final_incident_brief_dataset.sql"),
]

# Vars that must be non-empty for a query to run (otherwise it is skipped gracefully).
QUERY_REQUIRED_VARS: dict[str, list[str]] = {
    "deploy_correlation": ["GITHUB_OWNER", "GITHUB_REPO"],
}


def run_incident_queries(
    coral: CoralClient,
    sql_dir: Path,
    incident_id: str,
    extra_vars: dict[str, str] | None = None,
) -> tuple[list[QueryRun], list[str]]:
    template_vars: dict[str, str] = {"INCIDENT_ID": incident_id, **(extra_vars or {})}
    runs: list[QueryRun] = []
    errors: list[str] = []
    for name, file_name in QUERY_FILES:
        # Skip queries whose required vars are missing or empty.
        required = QUERY_REQUIRED_VARS.get(name, [])
        missing = [v for v in required if not template_vars.get(v)]
        if missing:
            errors.append(f"{name}: skipped — set --github-owner / --github-repo to enable deploy correlation")
            continue

        path = sql_dir / file_name
        if not path.exists():
            errors.append(f"missing SQL template: {file_name}")
            continue
        sql = render_sql_from_template(path, template_vars)
        try:
            rows, duration_ms = coral.run_sql(sql)
            runs.append(QueryRun(name=name, rows=rows, duration_ms=duration_ms))
        except CoralError as exc:
            errors.append(f"{name}: {exc}")
    return runs, errors


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if not value:
            continue
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def _confidence(num_query_failures: int, evidence_count: int) -> str:
    if num_query_failures >= 3 or evidence_count == 0:
        return "low"
    if num_query_failures > 0 or evidence_count <= 2:
        return "medium"
    return "high"


def _make_executive_summary(
    incident_id: str,
    confidence: str,
    cause: str,
    services: list[str],
    owners: list[str],
    evidence_count: int,
    has_errors: bool,
) -> list[str]:
    service_text = ", ".join(services[:3]) if services else "unknown services"
    owner_text = ", ".join(owners[:2]) if owners else "on-call owner pending"
    risk = "high" if confidence == "low" else ("medium" if confidence == "medium" else "controlled")
    mitigation = "rollback candidate deploy and validate key metrics" if evidence_count else "restore source visibility and re-run analysis"
    next_update = "15 minutes" if confidence != "low" else "10 minutes"
    data_quality = "partial" if has_errors else "good"

    return [
        f"Incident {incident_id}: active service degradation detected.",
        f"Impacted scope: {service_text}.",
        f"Most likely trigger: {cause}",
        f"Current risk level: {risk} confidence ({confidence}), data quality: {data_quality}.",
        f"Current ownership: {owner_text}; immediate action: {mitigation}.",
        f"Next update ETA: {next_update}.",
    ]


def compose_brief(incident_id: str, runs: list[QueryRun], errors: list[str]) -> IncidentBrief:
    all_rows: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {"queries": {}, "errors": errors}

    for run in runs:
        diagnostics["queries"][run.name] = {
            "rows": len(run.rows),
            "duration_ms": run.duration_ms,
        }
        all_rows.extend(run.rows)

    services = _dedupe(
        [
            str(r.get("service") or r.get("service_id") or r.get("repo") or "").strip()
            for r in all_rows
        ]
    )
    owners = _dedupe(
        [
            str(r.get("owner") or r.get("author") or r.get("user_name") or "").strip()
            for r in all_rows
        ]
    )

    evidence: list[Evidence] = []
    for r in all_rows[:30]:
        link = str(r.get("incident_url") or r.get("deploy_url") or r.get("url") or "")
        if r.get("sha"):
            evidence.append(
                Evidence(
                    type="deploy",
                    detail=f"Deploy {r.get('repo', 'unknown')}@{r.get('sha')} by {r.get('author', 'unknown')}",
                    link=link,
                )
            )
        elif r.get("metric_name"):
            evidence.append(
                Evidence(
                    type="metric",
                    detail=f"{r.get('metric_name')}={r.get('value')} at {r.get('metric_ts') or r.get('timestamp')}",
                    link=link,
                )
            )
        elif r.get("text"):
            evidence.append(
                Evidence(
                    type="chat",
                    detail=f"{r.get('channel_name', 'channel')} {r.get('user_name', 'user')}: {str(r.get('text'))[:140]}",
                    link=link,
                )
            )
        elif r.get("title"):
            evidence.append(
                Evidence(
                    type="incident",
                    detail=f"Incident row: {r.get('title')}",
                    link=link,
                )
            )

    evidence = evidence[:10]
    confidence = _confidence(len(errors), len(evidence))
    cause = "Recent deployment likely triggered service degradation."
    if not evidence:
        cause = "Insufficient evidence from data sources; validate source connections and rerun."
    elif any(e.type == "metric" for e in evidence) and not any(e.type == "deploy" for e in evidence):
        cause = "Metric anomalies detected without clear deploy signal; likely infrastructure or dependency issue."

    summary = (
        f"Incident {incident_id} analyzed across Coral sources with {len(evidence)} evidence items "
        f"and {len(errors)} query errors."
    )
    actions = [
        "Validate rollback or feature-flag options for the most recent deploy.",
        "Assign primary owner and post 15-minute update cadence.",
        "Correlate affected endpoints with error and latency spikes.",
    ]
    if errors:
        actions.append("Fix failing source queries to improve confidence and coverage.")

    executive_summary = _make_executive_summary(
        incident_id=incident_id,
        confidence=confidence,
        cause=cause,
        services=services,
        owners=owners,
        evidence_count=len(evidence),
        has_errors=bool(errors),
    )

    return IncidentBrief(
        incident_id=incident_id,
        summary=summary,
        probable_root_cause=cause,
        confidence=confidence,
        impacted_services=services[:8],
        owners=owners[:8],
        evidence=evidence,
        recommended_actions=actions,
        executive_summary=executive_summary,
        diagnostics=diagnostics,
    )
