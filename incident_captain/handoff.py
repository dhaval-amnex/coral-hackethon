from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def write_handoff_note(report_dir: Path, output_file: Path) -> dict[str, Any]:
    progress = _read_json(report_dir / "progress_report.json")
    readiness = _read_json(report_dir / "live_readiness.json")
    release = _read_json(report_dir / "release_check.json")
    scorecard = _read_json(report_dir / "scorecard.json")
    next_actions = _read_json(report_dir / "next_actions.json")

    payload = {
        "progress_percent": progress.get("progress_percent", "N/A"),
        "go_for_submission": release.get("go_for_submission", "N/A"),
        "go_for_live_submission": release.get("go_for_live_submission", "N/A"),
        "scorecard_overall": scorecard.get("overall_score", "N/A"),
        "live_blockers": readiness.get("blockers", []),
        "next_actions": next_actions.get("actions", []),
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Handoff Note",
        "",
        f"- Progress percent: {payload['progress_percent']}",
        f"- Go for submission: {payload['go_for_submission']}",
        f"- Go for live submission: {payload['go_for_live_submission']}",
        f"- Scorecard overall: {payload['scorecard_overall']}",
        "",
        "## Live Blockers",
    ]
    if payload["live_blockers"]:
        lines.extend([f"- {b}" for b in payload["live_blockers"]])
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Next Actions",
        ]
    )
    if payload["next_actions"]:
        lines.extend([f"- {a}" for a in payload["next_actions"]])
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Recommended Commands",
            "- `python -m incident_captain.cli live-unblock --root . --report-dir output/report`",
            "- `python -m incident_captain.cli close-live-loop --incident-id INC-1001 --tables-file <...> --columns-file <...> --filters-file <...> --live-metrics-file <...> --output-root output --report-dir output/report --bundle-root output/bundles --workflow-log output/workflow_log.json --baseline-file deliverables/mock/baseline_times.json`",
            "- `python -m incident_captain.cli judge-pack --bundle-root output/bundles --output-zip output/judge_pack.zip`",
        ]
    )
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload

