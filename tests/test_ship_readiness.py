from argparse import Namespace
import json
from pathlib import Path

from incident_captain.cli import cmd_ship_readiness


def test_ship_readiness_generates_consistent_reports(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    report_dir = output_dir / "report"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "INC-1.json").write_text(json.dumps({"incident_id": "INC-1"}), encoding="utf-8")
    (output_dir / "INC-1.md").write_text("# Incident", encoding="utf-8")
    (output_dir / "workflow_log.json").write_text("[]", encoding="utf-8")
    (output_dir / "run_metrics.jsonl").write_text(
        json.dumps(
            {
                "incident_id": "INC-1",
                "total_duration_ms": 1000,
                "confidence": "high",
                "evidence_count": 4,
                "query_errors": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (report_dir / "impact_report.json").write_text(
        json.dumps({"improvement_percent": 25.0}),
        encoding="utf-8",
    )

    args = Namespace(
        incident_id="INC-1",
        root=str(tmp_path),
        output_dir=str(output_dir),
        report_dir=str(report_dir),
        metrics_log=str(output_dir / "run_metrics.jsonl"),
        recent_runs=1,
        min_success_rate=0.7,
        min_improvement_percent=10.0,
        min_progress_percent=0.0,
        min_scorecard_overall=0.0,
        status_output_file=str(report_dir / "status_dashboard.md"),
        handoff_output_file=str(report_dir / "handoff_note.md"),
    )
    rc = cmd_ship_readiness(args)
    assert rc == 0
    assert (report_dir / "demo_report.json").exists()
    assert (report_dir / "quality_gate.json").exists()
    assert (report_dir / "scorecard.json").exists()
    assert (report_dir / "release_check.json").exists()
    assert (report_dir / "status_dashboard.md").exists()
    assert (report_dir / "handoff_note.md").exists()
