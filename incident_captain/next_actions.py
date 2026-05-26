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


def build_next_actions(report_dir: Path) -> dict[str, Any]:
    progress = _read_json(report_dir / "progress_report.json")
    readiness = _read_json(report_dir / "live_readiness.json")
    release = _read_json(report_dir / "release_check.json")

    actions: list[str] = []
    if not progress:
        actions.append("run progress-report to generate implementation audit")
    else:
        for pending in progress.get("pending_checks", []):
            actions.append(f"complete pending check: {pending}")

    if not readiness:
        actions.append("run live-readiness to identify live-data blockers")
    else:
        for blocker in readiness.get("blockers", []):
            actions.append(f"resolve live blocker: {blocker}")

    if not release:
        actions.append("run release-check for final go/no-go decision")
    else:
        if not release.get("go_for_submission", False):
            actions.append("improve reports/quality gate until go_for_submission=true")
        if not release.get("go_for_live_submission", False):
            actions.append("complete live Coral run and catalog snapshot for real-data submission")

    if not actions:
        actions.append("no pending actions; proceed with submission")

    return {
        "pending_count": len(actions),
        "actions": actions,
    }


def write_next_actions(report_dir: Path, out_json: Path, out_md: Path) -> dict[str, Any]:
    payload = build_next_actions(report_dir)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = ["# Next Actions", ""]
    lines.extend([f"- {a}" for a in payload["actions"]])
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload

