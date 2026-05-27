from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _safe_avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def load_metrics(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
        except json.JSONDecodeError:
            continue
    return rows


def build_demo_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_runs = len(rows)
    durations = [float(r.get("total_duration_ms", 0)) for r in rows]
    evidence_counts = [int(r.get("evidence_count", 0)) for r in rows]
    query_errors = [int(r.get("query_errors", 0)) for r in rows]

    confidence_counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
    for row in rows:
        confidence = str(row.get("confidence", "unknown")).lower()
        if confidence not in confidence_counts:
            confidence = "unknown"
        confidence_counts[confidence] += 1

    success_runs = sum(1 for e in query_errors if e == 0)
    success_rate = (success_runs / total_runs) if total_runs else 0.0

    return {
        "total_runs": total_runs,
        "success_rate": round(success_rate, 4),
        "avg_duration_ms": round(_safe_avg(durations), 2),
        "avg_evidence_count": round(_safe_avg([float(e) for e in evidence_counts]), 2),
        "avg_query_errors": round(_safe_avg([float(e) for e in query_errors]), 2),
        "confidence_distribution": confidence_counts,
        "latest_incident_id": rows[-1].get("incident_id") if rows else "",
    }


def write_demo_report(
    metrics_path: Path,
    out_json: Path,
    out_md: Path,
    *,
    recent_runs: int = 0,
) -> dict[str, Any]:
    rows = load_metrics(metrics_path)
    if recent_runs > 0:
        rows = rows[-recent_runs:]
    summary = build_demo_summary(rows)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# Demo Report",
        "",
        f"- Total runs: {summary['total_runs']}",
        f"- Success rate: {summary['success_rate']}",
        f"- Avg duration (ms): {summary['avg_duration_ms']}",
        f"- Avg evidence count: {summary['avg_evidence_count']}",
        f"- Avg query errors: {summary['avg_query_errors']}",
        f"- Latest incident: {summary['latest_incident_id'] or 'N/A'}",
        "",
        "## Confidence Distribution",
        f"- High: {summary['confidence_distribution']['high']}",
        f"- Medium: {summary['confidence_distribution']['medium']}",
        f"- Low: {summary['confidence_distribution']['low']}",
        f"- Unknown: {summary['confidence_distribution']['unknown']}",
    ]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary
