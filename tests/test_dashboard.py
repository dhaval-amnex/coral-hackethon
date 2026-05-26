from pathlib import Path
import json

from incident_captain.dashboard import write_dashboard


def test_write_dashboard(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "scorecard.json").write_text(json.dumps({"overall_score": 90}), encoding="utf-8")
    (report_dir / "quality_gate.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    (report_dir / "live_readiness.json").write_text(json.dumps({"ready_for_live_submission": False}), encoding="utf-8")
    (report_dir / "release_check.json").write_text(json.dumps({"go_for_submission": True}), encoding="utf-8")
    (report_dir / "next_actions.json").write_text(json.dumps({"actions": ["x"]}), encoding="utf-8")
    out = tmp_path / "status.md"
    payload = write_dashboard(report_dir, out)
    assert out.exists()
    assert payload["scorecard"]["overall_score"] == 90

