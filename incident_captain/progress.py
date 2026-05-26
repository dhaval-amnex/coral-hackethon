from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _exists(path: Path) -> bool:
    return path.exists()


def build_progress_report(root: Path) -> dict[str, Any]:
    output_dir = root / "output"
    report_dir = output_dir / "report"

    checks = {
        "phase0_setup": _exists(root / "deliverables" / "ops" / "commands.md"),
        "phase1_schema_template": _exists(root / "deliverables" / "docs" / "schema-map.md"),
        "phase2_sql_templates": _exists(root / "deliverables" / "sql" / "05_final_incident_brief_dataset.sql"),
        "phase3_orchestration": _exists(root / "incident_captain" / "orchestration.py"),
        "phase4_cli_surface": _exists(root / "incident_captain" / "cli.py"),
        "phase5_metrics": _exists(root / "incident_captain" / "metrics.py"),
        "phase6_submission_bundle": _exists(root / "incident_captain" / "bundling.py"),
        "demo_report_generated": _exists(report_dir / "demo_report.json"),
        "impact_report_generated": _exists(report_dir / "impact_report.json"),
        "quality_gate_generated": _exists(report_dir / "quality_gate.json"),
        "scorecard_generated": _exists(report_dir / "scorecard.json"),
    }

    completed = [k for k, v in checks.items() if v]
    pending = [k for k, v in checks.items() if not v]
    progress_pct = round((len(completed) / len(checks)) * 100.0, 2) if checks else 0.0

    phase_summary = {
        "phase0_setup_access": checks["phase0_setup"],
        "phase1_data_contract": checks["phase1_schema_template"],
        "phase2_sql_core": checks["phase2_sql_templates"],
        "phase3_mcp_orchestration": checks["phase3_orchestration"],
        "phase4_product_surface": checks["phase4_cli_surface"],
        "phase5_reliability_security_telemetry": checks["phase5_metrics"],
        "phase6_demo_submission": checks["phase6_submission_bundle"],
    }

    return {
        "progress_percent": progress_pct,
        "completed_checks": completed,
        "pending_checks": pending,
        "phase_summary": phase_summary,
        "raw_checks": checks,
    }


def write_progress_report(root: Path, out_json: Path, out_md: Path) -> dict[str, Any]:
    report = build_progress_report(root)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Progress Report",
        "",
        f"- Progress: {report['progress_percent']}%",
        "",
        "## Phase Summary",
    ]
    for k, v in report["phase_summary"].items():
        lines.append(f"- {k}: {'complete' if v else 'pending'}")
    lines.extend(["", "## Pending Checks"])
    if report["pending_checks"]:
        lines.extend([f"- {x}" for x in report["pending_checks"]])
    else:
        lines.append("- none")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report

