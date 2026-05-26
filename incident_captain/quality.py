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


def run_quality_gate(
    *,
    incident_id: str,
    output_dir: Path,
    report_dir: Path,
    min_success_rate: float = 0.7,
    min_improvement_percent: float = 10.0,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    required_files = [
        output_dir / f"{incident_id}.json",
        output_dir / f"{incident_id}.md",
        output_dir / "workflow_log.json",
        output_dir / "run_metrics.jsonl",
        report_dir / "demo_report.json",
        report_dir / "impact_report.json",
    ]
    for file_path in required_files:
        checks.append(
            {
                "check": f"file_exists:{file_path.name}",
                "passed": file_path.exists(),
                "detail": str(file_path),
            }
        )

    demo_report = _read_json(report_dir / "demo_report.json")
    impact_report = _read_json(report_dir / "impact_report.json")

    success_rate = float(demo_report.get("success_rate", 0.0))
    improvement_percent = float(impact_report.get("improvement_percent", 0.0))

    checks.append(
        {
            "check": "success_rate_threshold",
            "passed": success_rate >= min_success_rate,
            "detail": {"actual": success_rate, "required": min_success_rate},
        }
    )
    checks.append(
        {
            "check": "improvement_percent_threshold",
            "passed": improvement_percent >= min_improvement_percent,
            "detail": {"actual": improvement_percent, "required": min_improvement_percent},
        }
    )

    passed = all(bool(c.get("passed")) for c in checks)
    return {
        "passed": passed,
        "incident_id": incident_id,
        "checks": checks,
        "summary": {
            "success_rate": success_rate,
            "improvement_percent": improvement_percent,
        },
    }

