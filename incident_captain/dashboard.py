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


def build_dashboard(report_dir: Path) -> dict[str, Any]:
    return {
        "demo": _read_json(report_dir / "demo_report.json"),
        "impact": _read_json(report_dir / "impact_report.json"),
        "quality": _read_json(report_dir / "quality_gate.json"),
        "scorecard": _read_json(report_dir / "scorecard.json"),
        "readiness": _read_json(report_dir / "live_readiness.json"),
        "release": _read_json(report_dir / "release_check.json"),
        "next_actions": _read_json(report_dir / "next_actions.json"),
    }


def write_dashboard(report_dir: Path, out_md: Path) -> dict[str, Any]:
    d = build_dashboard(report_dir)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Incident Captain Status Dashboard",
        "",
        f"- Scorecard overall: {d['scorecard'].get('overall_score', 'N/A')}",
        f"- Quality gate passed: {d['quality'].get('passed', 'N/A')}",
        f"- Live ready: {d['readiness'].get('ready_for_live_submission', 'N/A')}",
        f"- Go for submission: {d['release'].get('go_for_submission', 'N/A')}",
        f"- Go for live submission: {d['release'].get('go_for_live_submission', 'N/A')}",
        "",
        "## Demo",
        f"- Success rate: {d['demo'].get('success_rate', 'N/A')}",
        f"- Avg duration ms: {d['demo'].get('avg_duration_ms', 'N/A')}",
        "",
        "## Impact",
        f"- Improvement %: {d['impact'].get('improvement_percent', 'N/A')}",
        f"- Minutes saved: {d['impact'].get('minutes_saved', 'N/A')}",
        "",
        "## Next Actions",
    ]
    for action in d["next_actions"].get("actions", []):
        lines.append(f"- {action}")
    if not d["next_actions"].get("actions"):
        lines.append("- none")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return d

