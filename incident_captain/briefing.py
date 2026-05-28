from __future__ import annotations

import re
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
WINDOW_OPTIMIZED_QUERIES = {"deploy_correlation", "telemetry_context"}
NARROW_WINDOW_HOURS = 2
WIDE_WINDOW_HOURS = 24
MIN_ROWS_BEFORE_WIDEN = 3

# Preferred table references and fallback candidates discovered from coral.tables.
TABLE_CANDIDATES: dict[str, list[str]] = {
    "pagerduty.incidents": [
        "pagerduty.incidents",
    ],
    "github.repo_deployments": [
        "github.repo_deployments",
        "github.deployments",
    ],
    "datadog.monitors": [
        "datadog.monitors",
    ],
    "slack.users": [
        "slack.users",
    ],
}


def discover_table_aliases(coral: CoralClient) -> dict[str, str]:
    """
    Resolve preferred table refs to existing catalog tables.
    Falls back to the preferred value when no candidate is found.
    """
    try:
        rows, _ = coral.run_sql("SELECT schema_name, table_name FROM coral.tables")
    except CoralError:
        return {preferred: preferred for preferred in TABLE_CANDIDATES}

    available: set[str] = set()
    for row in rows:
        schema = str(row.get("schema_name") or "").strip()
        table = str(row.get("table_name") or "").strip()
        if schema and table:
            available.add(f"{schema}.{table}")

    resolved: dict[str, str] = {}
    for preferred, candidates in TABLE_CANDIDATES.items():
        chosen = preferred
        for candidate in candidates:
            if candidate in available:
                chosen = candidate
                break
        resolved[preferred] = chosen
    return resolved


def apply_table_aliases(sql: str, table_aliases: dict[str, str]) -> str:
    rendered = sql
    for source_ref, target_ref in table_aliases.items():
        pattern = rf"\b{re.escape(source_ref)}\b"
        rendered = re.sub(pattern, target_ref, rendered)
    return rendered


def run_incident_queries(
    coral: CoralClient,
    sql_dir: Path,
    incident_id: str,
    extra_vars: dict[str, str] | None = None,
    table_aliases: dict[str, str] | None = None,
    enabled_queries: set[str] | None = None,
) -> tuple[list[QueryRun], list[str]]:
    template_vars: dict[str, str] = {"INCIDENT_ID": incident_id, **(extra_vars or {})}
    runs: list[QueryRun] = []
    errors: list[str] = []
    table_aliases = table_aliases or {k: k for k in TABLE_CANDIDATES}
    for name, file_name in QUERY_FILES:
        if enabled_queries is not None and name not in enabled_queries:
            errors.append(f"{name}: skipped by catalog planner")
            continue
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
        base_vars = dict(template_vars)
        base_vars.setdefault("WINDOW_HOURS", str(NARROW_WINDOW_HOURS))
        sql = render_sql_from_template(path, base_vars)
        sql = apply_table_aliases(sql, table_aliases)

        def _exec(sql_text: str) -> tuple[list[dict[str, Any]], int, int]:
            if hasattr(coral, "run_sql_with_meta"):
                rows, duration_ms, meta = coral.run_sql_with_meta(sql_text)  # type: ignore[attr-defined]
                return rows, duration_ms, int(meta.get("attempts", 1))
            rows, duration_ms = coral.run_sql(sql_text)
            return rows, duration_ms, 1

        try:
            rows, duration_ms, attempts = _exec(sql)
            used_window = int(base_vars.get("WINDOW_HOURS", "0")) if name in WINDOW_OPTIMIZED_QUERIES else None

            if name in WINDOW_OPTIMIZED_QUERIES and len(rows) < MIN_ROWS_BEFORE_WIDEN:
                wide_vars = dict(template_vars)
                wide_vars["WINDOW_HOURS"] = str(WIDE_WINDOW_HOURS)
                sql_wide = apply_table_aliases(render_sql_from_template(path, wide_vars), table_aliases)
                rows_wide, duration_ms_wide, attempts_wide = _exec(sql_wide)
                if len(rows_wide) > len(rows):
                    rows, duration_ms, attempts = rows_wide, duration_ms_wide, attempts_wide
                    used_window = WIDE_WINDOW_HOURS

            runs.append(
                QueryRun(
                    name=name,
                    rows=rows,
                    duration_ms=duration_ms,
                    attempts=attempts,
                    window_hours=used_window,
                )
            )
        except CoralError as exc:
            errors.append(f"{name}: [{exc.category}] {exc}")
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


def _extract_failed_query_names(errors: list[str]) -> set[str]:
    failed: set[str] = set()
    for err in errors:
        if ":" in err:
            failed.add(err.split(":", 1)[0].strip())
    return failed


def _coverage_quality(
    runs: list[QueryRun],
    errors: list[str],
) -> tuple[int, list[str], dict[str, bool]]:
    """
    Score functional evidence-family coverage so confidence reflects partial-source fallbacks.
    """
    expected_families = {
        "incident": {"active_incidents"},
        "deploy": {"deploy_correlation"},
        "telemetry": {"telemetry_context"},
        "comms": {"team_comms"},
    }
    run_names = {r.name for r in runs}
    failed_names = _extract_failed_query_names(errors)
    if "final_dataset" in run_names and "final_dataset" not in failed_names:
        family_ok_all = {"incident": True, "deploy": True, "telemetry": True, "comms": True}
        return 4, [], family_ok_all
    family_ok: dict[str, bool] = {}
    missing_families: list[str] = []
    for family, query_names in expected_families.items():
        ok = any(q in run_names for q in query_names) and not any(q in failed_names for q in query_names)
        family_ok[family] = ok
        if not ok:
            missing_families.append(family)
    return sum(1 for v in family_ok.values() if v), missing_families, family_ok


def _row_quality_score(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    keys = ("service", "repo", "author", "user_name", "metric_name", "title", "text")
    good = 0
    for row in rows:
        if any(str(row.get(k) or "").strip() for k in keys):
            good += 1
    return round((good / len(rows)) * 100.0, 2)


def _confidence_with_coverage(
    num_query_failures: int,
    evidence_count: int,
    coverage_score: int,
) -> str:
    base = _confidence(num_query_failures, evidence_count)
    # 4 families = full coverage. Penalize confidence for missing families.
    if coverage_score <= 1:
        return "low"
    if coverage_score == 2 and base == "high":
        return "medium"
    if coverage_score == 3 and base == "high" and evidence_count < 4:
        return "medium"
    return base


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
        run.row_quality_score = _row_quality_score(run.rows)
        diagnostics["queries"][run.name] = {
            "rows": len(run.rows),
            "duration_ms": run.duration_ms,
            "attempts": run.attempts,
            "row_quality_score": run.row_quality_score,
            "window_hours": run.window_hours,
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
    coverage_score, missing_families, family_ok = _coverage_quality(runs, errors)
    confidence = _confidence_with_coverage(len(errors), len(evidence), coverage_score)
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
    if missing_families:
        actions.append(f"Restore missing evidence families: {', '.join(missing_families)}.")

    diagnostics["coverage"] = {
        "score": coverage_score,
        "max_score": 4,
        "missing_families": missing_families,
        "families": family_ok,
        "source_availability_influence": round(((4 - coverage_score) / 4) * 100.0, 2),
    }

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
