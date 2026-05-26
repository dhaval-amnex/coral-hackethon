from pathlib import Path
import json

from incident_captain.readiness import write_live_readiness_report


def test_live_readiness_reports_blockers(tmp_path: Path) -> None:
    out_json = tmp_path / "out" / "live_readiness.json"
    out_md = tmp_path / "out" / "live_readiness.md"
    report = write_live_readiness_report(tmp_path, out_json, out_md)
    assert report["ready_for_live_submission"] is False
    assert "no_live_runs_recorded" in report["blockers"]
    assert out_json.exists()
    assert out_md.exists()


def test_live_readiness_passes_when_live_signals_present(tmp_path: Path) -> None:
    catalog = tmp_path / "output" / "catalog"
    report_dir = tmp_path / "output" / "report"
    catalog.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    (catalog / "catalog_tables.json").write_text(json.dumps([{"x": 1}]), encoding="utf-8")
    (catalog / "catalog_columns.json").write_text(json.dumps([{"x": 1}]), encoding="utf-8")
    (catalog / "catalog_filters.json").write_text(json.dumps([{"x": 1}]), encoding="utf-8")
    (tmp_path / "output" / "run_metrics.jsonl").write_text(
        json.dumps({"mode": "live"}) + "\n",
        encoding="utf-8",
    )
    (report_dir / "quality_gate.json").write_text(
        json.dumps({"passed": True}),
        encoding="utf-8",
    )

    out_json = tmp_path / "out" / "live_readiness.json"
    out_md = tmp_path / "out" / "live_readiness.md"
    report = write_live_readiness_report(tmp_path, out_json, out_md)
    assert report["ready_for_live_submission"] is True
    assert report["blockers"] == []

