from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .briefing import QUERY_FILES, compose_brief, run_incident_queries
from .coral import CoralClient
from .models import IncidentBrief


@dataclass
class WorkflowResult:
    brief: IncidentBrief
    workflow_log: list[dict[str, Any]]
    total_duration_ms: int


def run_deterministic_workflow(
    *,
    coral: CoralClient,
    incident_id: str,
    sql_dir: Path,
    mock_data_dir: Path | None = None,
    extra_vars: dict[str, str] | None = None,
) -> WorkflowResult:
    started = time.perf_counter()
    workflow_log: list[dict[str, Any]] = []

    step_start = time.perf_counter()
    workflow_log.append(
        {
            "step": "discover_catalog",
            "status": "ok",
            "detail": {
                "mode": "mock" if mock_data_dir else "live",
                "planned_queries": [name for name, _ in QUERY_FILES],
            },
            "duration_ms": int((time.perf_counter() - step_start) * 1000),
        }
    )

    step_start = time.perf_counter()
    runs, errors = run_incident_queries(
        coral=coral,
        sql_dir=sql_dir,
        incident_id=incident_id,
        mock_data_dir=mock_data_dir,
        extra_vars=extra_vars,
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

