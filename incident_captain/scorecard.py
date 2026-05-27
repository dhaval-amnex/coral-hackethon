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


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _speed_score(avg_duration_ms: float) -> float:
    # Linear speed score with a practical live-run floor:
    # 0 ms => 100, 60,000+ ms => 0.
    return _clamp(100.0 - (avg_duration_ms / 600.0))


def build_scorecard(
    *,
    demo_report: dict[str, Any],
    impact_report: dict[str, Any],
    quality_gate: dict[str, Any],
) -> dict[str, Any]:
    success_rate = float(demo_report.get("success_rate", 0.0))
    avg_duration_ms = float(demo_report.get("avg_duration_ms", 0.0))
    improvement_percent = float(impact_report.get("improvement_percent", 0.0))
    passed = bool(quality_gate.get("passed", False))
    checks = quality_gate.get("checks", [])
    checks_passed = sum(1 for c in checks if c.get("passed"))
    checks_total = len(checks) if isinstance(checks, list) else 0

    reliability = _clamp(success_rate * 100.0)
    speed = _speed_score(avg_duration_ms)
    impact = _clamp(improvement_percent)
    completeness = _clamp((checks_passed / checks_total) * 100.0) if checks_total else 0.0
    accuracy_proxy = _clamp((reliability * 0.6) + (completeness * 0.4))

    overall = round((accuracy_proxy + reliability + speed + impact + completeness) / 5.0, 2)

    return {
        "overall_score": overall,
        "dimensions": {
            "accuracy_proxy": round(accuracy_proxy, 2),
            "reliability": round(reliability, 2),
            "speed": round(speed, 2),
            "impact": round(impact, 2),
            "completeness": round(completeness, 2),
        },
        "quality_gate_passed": passed,
        "inputs": {
            "success_rate": success_rate,
            "avg_duration_ms": avg_duration_ms,
            "improvement_percent": improvement_percent,
            "checks_passed": checks_passed,
            "checks_total": checks_total,
        },
    }


def write_scorecard(
    *,
    report_dir: Path,
    quality_gate_path: Path,
    out_json: Path,
    out_md: Path,
) -> dict[str, Any]:
    demo_report = _read_json(report_dir / "demo_report.json")
    impact_report = _read_json(report_dir / "impact_report.json")
    quality_gate = _read_json(quality_gate_path)
    scorecard = build_scorecard(
        demo_report=demo_report,
        impact_report=impact_report,
        quality_gate=quality_gate,
    )

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(scorecard, indent=2), encoding="utf-8")

    d = scorecard["dimensions"]
    lines = [
        "# Judge Scorecard",
        "",
        f"- Overall score: {scorecard['overall_score']}",
        f"- Quality gate passed: {scorecard['quality_gate_passed']}",
        "",
        "## Dimensions (0-100)",
        f"- Accuracy proxy: {d['accuracy_proxy']}",
        f"- Reliability: {d['reliability']}",
        f"- Speed: {d['speed']}",
        f"- Impact: {d['impact']}",
        f"- Completeness: {d['completeness']}",
    ]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return scorecard
