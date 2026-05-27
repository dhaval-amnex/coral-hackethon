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


def build_live_playbook(report_dir: Path) -> dict[str, Any]:
    readiness = _read_json(report_dir / "live_readiness.json")
    blockers = readiness.get("blockers", []) if readiness else []

    steps: list[str] = []
    if "catalog_snapshot_missing_or_empty" in blockers:
        steps.append(
            "Collect live catalog files on unrestricted machine: catalog_tables.json, catalog_columns.json, catalog_filters.json."
        )
    if "no_live_runs_recorded" in blockers:
        steps.append("Collect run_metrics_live.jsonl containing at least one row with mode=live.")

    steps.extend(
        [
            "Verify files: python -m incident_captain.cli evidence-verify --tables-file <...> --columns-file <...> --filters-file <...> --live-metrics-file <...> --output-file output/report/evidence_verify.json",
            "Import files: python -m incident_captain.cli import-live-evidence --tables-file <...> --columns-file <...> --filters-file <...> --live-metrics-file <...> --output-root output",
            "Run close loop: python -m incident_captain.cli close-live-loop --incident-id <INCIDENT_ID> --tables-file <...> --columns-file <...> --filters-file <...> --live-metrics-file <...> --output-root output --report-dir output/report --bundle-root output/bundles --workflow-log output/workflow_log.json --baseline-file output/baseline_times.json",
            "Create final zip: python -m incident_captain.cli judge-pack --bundle-root output/bundles --output-zip output/judge_pack.zip",
        ]
    )

    return {
        "blockers": blockers,
        "steps": steps,
    }


def write_live_playbook(report_dir: Path, output_file: Path) -> dict[str, Any]:
    payload = build_live_playbook(report_dir)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Live Playbook", ""]
    lines.extend([f"- {s}" for s in payload["steps"]])
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload
