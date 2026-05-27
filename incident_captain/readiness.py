from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> list[dict[str, Any]] | dict[str, Any]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, (list, dict)):
            return payload
    except json.JSONDecodeError:
        pass
    return []


def _has_rows(path: Path) -> bool:
    payload = _read_json(path)
    return isinstance(payload, list) and len(payload) > 0


def build_live_readiness_report(root: Path) -> dict[str, Any]:
    output_dir = root / "output"
    report_dir = output_dir / "report"
    catalog_dir = output_dir / "catalog"
    metrics_path = output_dir / "run_metrics.jsonl"

    tables_path = catalog_dir / "catalog_tables.json"
    columns_path = catalog_dir / "catalog_columns.json"
    filters_path = catalog_dir / "catalog_filters.json"
    quality_gate_path = report_dir / "quality_gate.json"

    catalog_ready = _has_rows(tables_path) and _has_rows(columns_path) and _has_rows(filters_path)

    live_runs = 0
    mock_runs = 0
    if metrics_path.exists():
        for line in metrics_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            mode = str(row.get("mode", "")).lower()
            if mode == "live":
                live_runs += 1
            elif mode == "mock":
                mock_runs += 1

    quality_gate = _read_json(quality_gate_path)
    quality_gate_passed = bool(quality_gate.get("passed")) if isinstance(quality_gate, dict) else False

    blockers: list[str] = []
    if not catalog_ready:
        blockers.append("catalog_snapshot_missing_or_empty")
    if live_runs == 0:
        blockers.append("no_live_runs_recorded")
    if not quality_gate_passed:
        blockers.append("quality_gate_not_passed")

    ready_for_live_submission = len(blockers) == 0

    return {
        "ready_for_live_submission": ready_for_live_submission,
        "blockers": blockers,
        "signals": {
            "catalog_ready": catalog_ready,
            "live_runs": live_runs,
            "mock_runs": mock_runs,
            "quality_gate_passed": quality_gate_passed,
        },
        "expected_next_actions": [
            "run snapshot-catalog with live Coral access",
            "run analyze/demo-run with live source credentials",
            "regenerate quality-gate, scorecard, and submission bundle",
        ],
    }


def write_live_readiness_report(root: Path, out_json: Path, out_md: Path) -> dict[str, Any]:
    report = build_live_readiness_report(root)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Live Readiness Report",
        "",
        f"- Ready for live submission: {report['ready_for_live_submission']}",
        f"- Catalog ready: {report['signals']['catalog_ready']}",
        f"- Live runs: {report['signals']['live_runs']}",
        f"- Mock runs: {report['signals']['mock_runs']}",
        f"- Quality gate passed: {report['signals']['quality_gate_passed']}",
        "",
        "## Blockers",
    ]
    if report["blockers"]:
        lines.extend([f"- {b}" for b in report["blockers"]])
    else:
        lines.append("- none")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report
