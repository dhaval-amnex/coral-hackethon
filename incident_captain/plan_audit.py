from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def build_plan_audit(root: Path) -> dict[str, Any]:
    report_dir = root / "output" / "report"
    readiness = _read_json(report_dir / "live_readiness.json")
    release = _read_json(report_dir / "release_check.json")
    progress = _read_json(report_dir / "progress_report.json")

    pending: list[str] = []
    if not progress:
        pending.append("generate progress-report")
    if not readiness:
        pending.append("generate live-readiness report")
    if not release:
        pending.append("generate release-check report")

    blockers = readiness.get("blockers", []) if readiness else []
    for blocker in blockers:
        pending.append(f"resolve: {blocker}")

    go_for_submission = bool(release.get("go_for_submission", False)) if release else False
    go_for_live_submission = bool(release.get("go_for_live_submission", False)) if release else False

    phase_state = {
        "phase0_1_live_setup": "complete" if "catalog_snapshot_missing_or_empty" not in blockers else "pending",
        "phase2_live_sql_validation": "complete" if "no_live_runs_recorded" not in blockers else "pending",
        "phase3_6_delivery_pipeline": "complete" if progress else "pending",
        "final_submission_readiness": "complete" if go_for_submission else "pending",
        "final_live_submission_readiness": "complete" if go_for_live_submission else "pending",
    }

    if not pending and go_for_live_submission:
        pending.append("no pending items")

    return {
        "phase_state": phase_state,
        "go_for_submission": go_for_submission,
        "go_for_live_submission": go_for_live_submission,
        "pending_items": pending,
    }

