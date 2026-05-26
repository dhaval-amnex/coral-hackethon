from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .progress import build_progress_report
from .readiness import build_live_readiness_report
from .scorecard import build_scorecard


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def build_release_check(root: Path) -> dict[str, Any]:
    output_dir = root / "output"
    report_dir = output_dir / "report"

    progress = build_progress_report(root)
    readiness = build_live_readiness_report(root)

    demo_report = _read_json(report_dir / "demo_report.json")
    impact_report = _read_json(report_dir / "impact_report.json")
    quality_gate = _read_json(report_dir / "quality_gate.json")
    scorecard = build_scorecard(
        demo_report=demo_report,
        impact_report=impact_report,
        quality_gate=quality_gate,
    )

    go_for_submission = (
        progress["progress_percent"] >= 90.0
        and bool(quality_gate.get("passed", False))
        and scorecard["overall_score"] >= 75.0
    )
    go_for_live_submission = go_for_submission and readiness["ready_for_live_submission"]

    next_actions: list[str] = []
    if not go_for_submission:
        next_actions.append("regenerate demo artifacts and ensure quality gate passes")
    if not readiness["ready_for_live_submission"]:
        next_actions.append("resolve live-readiness blockers for real-data evidence")
    if scorecard["overall_score"] < 75.0:
        next_actions.append("improve reliability/speed/impact metrics before submission")
    if not next_actions:
        next_actions.append("submission-ready")

    return {
        "go_for_submission": go_for_submission,
        "go_for_live_submission": go_for_live_submission,
        "progress_percent": progress["progress_percent"],
        "scorecard_overall": scorecard["overall_score"],
        "quality_gate_passed": bool(quality_gate.get("passed", False)),
        "live_readiness": readiness["ready_for_live_submission"],
        "live_blockers": readiness["blockers"],
        "next_actions": next_actions,
    }


def write_release_check(root: Path, out_json: Path, out_md: Path) -> dict[str, Any]:
    report = build_release_check(root)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Release Check",
        "",
        f"- Go for submission: {report['go_for_submission']}",
        f"- Go for live submission: {report['go_for_live_submission']}",
        f"- Progress percent: {report['progress_percent']}",
        f"- Scorecard overall: {report['scorecard_overall']}",
        f"- Quality gate passed: {report['quality_gate_passed']}",
        f"- Live readiness: {report['live_readiness']}",
        "",
        "## Next Actions",
    ]
    lines.extend([f"- {a}" for a in report["next_actions"]])
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report

