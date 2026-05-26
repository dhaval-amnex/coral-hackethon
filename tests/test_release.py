from pathlib import Path
import json

from incident_captain.release import write_release_check


def test_write_release_check(tmp_path: Path) -> None:
    report_dir = tmp_path / "output" / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "demo_report.json").write_text(
        json.dumps({"success_rate": 1.0, "avg_duration_ms": 10.0}),
        encoding="utf-8",
    )
    (report_dir / "impact_report.json").write_text(
        json.dumps({"improvement_percent": 50.0}),
        encoding="utf-8",
    )
    (report_dir / "quality_gate.json").write_text(
        json.dumps({"passed": True, "checks": [{"passed": True}]}),
        encoding="utf-8",
    )

    # files for progress checks
    (tmp_path / "deliverables" / "ops").mkdir(parents=True, exist_ok=True)
    (tmp_path / "deliverables" / "ops" / "commands.md").write_text("x", encoding="utf-8")
    (tmp_path / "deliverables" / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "deliverables" / "docs" / "schema-map.md").write_text("x", encoding="utf-8")
    (tmp_path / "deliverables" / "sql").mkdir(parents=True, exist_ok=True)
    (tmp_path / "deliverables" / "sql" / "05_final_incident_brief_dataset.sql").write_text("x", encoding="utf-8")
    (tmp_path / "incident_captain").mkdir(parents=True, exist_ok=True)
    (tmp_path / "incident_captain" / "orchestration.py").write_text("x", encoding="utf-8")
    (tmp_path / "incident_captain" / "cli.py").write_text("x", encoding="utf-8")
    (tmp_path / "incident_captain" / "metrics.py").write_text("x", encoding="utf-8")
    (tmp_path / "incident_captain" / "bundling.py").write_text("x", encoding="utf-8")

    out_json = report_dir / "release_check.json"
    out_md = report_dir / "release_check.md"
    result = write_release_check(tmp_path, out_json, out_md)
    assert result["go_for_submission"] is True
    assert out_json.exists()
    assert out_md.exists()

