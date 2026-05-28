from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .briefing import QUERY_FILES, compose_brief, discover_table_aliases, run_incident_queries
from .coral import CoralClient
from .models import IncidentBrief

QUERY_TABLE_REQUIREMENTS: dict[str, list[str]] = {
    "active_incidents": ["pagerduty.incidents"],
    "deploy_correlation": ["github.repo_deployments"],
    "telemetry_context": ["datadog.monitors"],
    "team_comms": ["slack.users"],
    "final_dataset": ["github.repo_deployments"],
}


@dataclass
class WorkflowResult:
    brief: IncidentBrief
    workflow_log: list[dict[str, Any]]
    total_duration_ms: int


def _mcp_catalog_loop(coral: CoralClient) -> tuple[str, dict[str, Any]]:
    detail: dict[str, Any] = {
        "mode": "mcp_native",
        "capabilities": {
            "list_catalog": hasattr(coral, "list_catalog"),
            "search_catalog": hasattr(coral, "search_catalog"),
            "describe_table": hasattr(coral, "describe_table"),
            "list_columns": hasattr(coral, "list_columns"),
        },
        "schemas": {},
        "top_tables": [],
        "filter_requirements": [],
    }
    has_all = all(bool(v) for v in detail["capabilities"].values())
    if has_all:
        try:
            # Best-effort dynamic MCP calls if available on the Coral client wrapper.
            list_catalog = getattr(coral, "list_catalog")
            search_catalog = getattr(coral, "search_catalog")
            list_columns = getattr(coral, "list_columns")
            catalog_rows = list_catalog()  # type: ignore[misc]
            for row in catalog_rows[:8]:
                schema = str(row.get("schema_name") or "")
                detail["schemas"][schema] = int(row.get("table_count") or 0)
            detail["top_tables"] = search_catalog("incidents deployments monitors slack users", limit=20)  # type: ignore[misc]
            # Use top table candidates to list columns.
            for table_row in detail["top_tables"][:5]:
                schema = str(table_row.get("schema_name") or "")
                table = str(table_row.get("table_name") or "")
                if not (schema and table):
                    continue
                cols = list_columns(schema, table)  # type: ignore[misc]
                required_like = [c for c in cols if bool(c.get("required"))]
                detail["filter_requirements"].extend(required_like[:10])
            return "ok", detail
        except Exception as exc:
            detail["error"] = str(exc)
            detail["fallback"] = "sql_catalog_loop"

    # Fallback path keeps runs robust even without MCP methods on client.
    try:
        schemas_rows, _ = coral.run_sql(
            "SELECT schema_name, COUNT(*) AS table_count FROM coral.tables GROUP BY schema_name ORDER BY table_count DESC"
        )
        for row in schemas_rows[:8]:
            schema = str(row.get("schema_name") or "")
            detail["schemas"][schema] = int(row.get("table_count") or 0)
        top_rows, _ = coral.run_sql(
            "SELECT schema_name, table_name FROM coral.tables ORDER BY schema_name, table_name LIMIT 20"
        )
        detail["top_tables"] = top_rows
        filter_rows, _ = coral.run_sql(
            "SELECT schema_name, table_name, filter_name, required FROM coral.filters WHERE required = true ORDER BY schema_name, table_name, filter_name LIMIT 30"
        )
        detail["filter_requirements"] = filter_rows
        detail["mode"] = "mcp_native_fallback_sql"
        return "ok", detail
    except Exception as exc:
        detail["error"] = str(exc)
        return "partial", detail


def run_deterministic_workflow(
    *,
    coral: CoralClient,
    incident_id: str,
    sql_dir: Path,
    extra_vars: dict[str, str] | None = None,
    planner_mode: str = "sql",
) -> WorkflowResult:
    started = time.perf_counter()
    workflow_log: list[dict[str, Any]] = []

    step_start = time.perf_counter()
    available_tables: set[str] = set()
    try:
        rows, _ = coral.run_sql("SELECT schema_name, table_name FROM coral.tables")
        for row in rows:
            schema = str(row.get("schema_name") or "").strip()
            table = str(row.get("table_name") or "").strip()
            if schema and table:
                available_tables.add(f"{schema}.{table}")
    except Exception:
        available_tables = set()

    table_aliases = discover_table_aliases(coral)
    remapped = {k: v for k, v in table_aliases.items() if k != v}
    template_vars: dict[str, str] = {"INCIDENT_ID": incident_id, **(extra_vars or {})}
    enabled_queries: set[str] = set()
    plan: dict[str, dict[str, Any]] = {}
    for query_name, _file in QUERY_FILES:
        required_tables = [table_aliases.get(t, t) for t in QUERY_TABLE_REQUIREMENTS.get(query_name, [])]
        missing_tables = [t for t in required_tables if available_tables and t not in available_tables]
        missing_vars: list[str] = []
        if query_name == "deploy_correlation":
            if not template_vars.get("GITHUB_OWNER"):
                missing_vars.append("GITHUB_OWNER")
            if not template_vars.get("GITHUB_REPO"):
                missing_vars.append("GITHUB_REPO")
        enabled = not missing_tables and not missing_vars
        if enabled:
            enabled_queries.add(query_name)
        plan[query_name] = {
            "enabled": enabled,
            "required_tables": required_tables,
            "missing_tables": missing_tables,
            "missing_vars": missing_vars,
        }
    workflow_log.append(
        {
            "step": "discover_catalog",
            "status": "ok",
            "detail": {
                "mode": "live",
                "planned_queries": [name for name, _ in QUERY_FILES],
                "table_aliases": table_aliases,
                "remapped_tables": remapped,
                "query_plan": plan,
            },
            "duration_ms": int((time.perf_counter() - step_start) * 1000),
        }
    )

    if planner_mode in {"mcp", "mcp_native"}:
        step_start = time.perf_counter()
        if planner_mode == "mcp_native":
            status, catalog_loop = _mcp_catalog_loop(coral)
            step_name = "mcp_native_catalog_loop"
        else:
            catalog_loop = {"schemas": {}, "top_tables": [], "filter_requirements": [], "mode": "mcp_sql"}
            try:
                schemas_rows, _ = coral.run_sql(
                    "SELECT schema_name, COUNT(*) AS table_count FROM coral.tables GROUP BY schema_name ORDER BY table_count DESC"
                )
                for row in schemas_rows[:8]:
                    schema = str(row.get("schema_name") or "")
                    catalog_loop["schemas"][schema] = int(row.get("table_count") or 0)
                top_rows, _ = coral.run_sql(
                    "SELECT schema_name, table_name FROM coral.tables ORDER BY schema_name, table_name LIMIT 20"
                )
                catalog_loop["top_tables"] = top_rows
                filter_rows, _ = coral.run_sql(
                    "SELECT schema_name, table_name, filter_name, required FROM coral.filters WHERE required = true ORDER BY schema_name, table_name, filter_name LIMIT 30"
                )
                catalog_loop["filter_requirements"] = filter_rows
                status = "ok"
            except Exception as exc:
                status = "partial"
                catalog_loop["error"] = str(exc)
            step_name = "mcp_catalog_loop"
        workflow_log.append(
            {
                "step": step_name,
                "status": status,
                "detail": catalog_loop,
                "duration_ms": int((time.perf_counter() - step_start) * 1000),
            }
        )

    step_start = time.perf_counter()
    runs, errors = run_incident_queries(
        coral=coral,
        sql_dir=sql_dir,
        incident_id=incident_id,
        extra_vars=extra_vars,
        table_aliases=table_aliases,
        enabled_queries=enabled_queries,
    )
    workflow_log.append(
        {
            "step": "execute_queries",
            "status": "ok" if not errors else "partial",
            "detail": {
                "executed": len(runs),
                "errors": errors,
                "query_names": [r.name for r in runs],
            },
            "duration_ms": int((time.perf_counter() - step_start) * 1000),
        }
    )

    step_start = time.perf_counter()
    brief = compose_brief(incident_id, runs, errors)
    workflow_log.append(
        {
            "step": "compose_brief",
            "status": "ok",
            "detail": {
                "confidence": brief.confidence,
                "evidence_count": len(brief.evidence),
            },
            "duration_ms": int((time.perf_counter() - step_start) * 1000),
        }
    )

    total_duration_ms = int((time.perf_counter() - started) * 1000)
    return WorkflowResult(brief=brief, workflow_log=workflow_log, total_duration_ms=total_duration_ms)


def write_workflow_log(path: Path, workflow_log: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(workflow_log, indent=2), encoding="utf-8")

