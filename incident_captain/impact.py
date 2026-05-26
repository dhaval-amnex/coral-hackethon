from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .reporting import load_metrics


def load_baseline(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    return []


def build_impact_summary(
    baseline_rows: list[dict[str, Any]],
    run_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    manual = [float(r.get("manual_minutes", 0.0)) for r in baseline_rows]
    assisted = [float(r.get("assisted_minutes", 0.0)) for r in baseline_rows]
    if not assisted:
        assisted = [float(r.get("total_duration_ms", 0.0)) / 60000.0 for r in run_rows]

    avg_manual = (sum(manual) / len(manual)) if manual else 0.0
    avg_assisted = (sum(assisted) / len(assisted)) if assisted else 0.0
    delta = avg_manual - avg_assisted
    improvement_pct = ((delta / avg_manual) * 100.0) if avg_manual else 0.0

    return {
        "baseline_samples": len(baseline_rows),
        "run_samples": len(run_rows),
        "avg_manual_minutes": round(avg_manual, 2),
        "avg_assisted_minutes": round(avg_assisted, 2),
        "minutes_saved": round(delta, 2),
        "improvement_percent": round(improvement_pct, 2),
    }


def write_impact_report(
    baseline_path: Path,
    metrics_path: Path,
    out_json: Path,
    out_md: Path,
) -> dict[str, Any]:
    baseline_rows = load_baseline(baseline_path)
    run_rows = load_metrics(metrics_path)
    summary = build_impact_summary(baseline_rows, run_rows)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = [
        "# Impact Report",
        "",
        f"- Baseline samples: {summary['baseline_samples']}",
        f"- Run samples: {summary['run_samples']}",
        f"- Average manual triage time (min): {summary['avg_manual_minutes']}",
        f"- Average assisted time (min): {summary['avg_assisted_minutes']}",
        f"- Minutes saved: {summary['minutes_saved']}",
        f"- Improvement (%): {summary['improvement_percent']}",
    ]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary

