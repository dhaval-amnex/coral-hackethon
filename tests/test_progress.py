from pathlib import Path

from incident_captain.progress import write_progress_report


def test_write_progress_report(tmp_path: Path) -> None:
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

    out_json = tmp_path / "output" / "report" / "progress_report.json"
    out_md = tmp_path / "output" / "report" / "progress_report.md"
    report = write_progress_report(tmp_path, out_json, out_md)
    assert report["phase_summary"]["phase6_demo_submission"] is True
    assert out_json.exists()
    assert out_md.exists()

