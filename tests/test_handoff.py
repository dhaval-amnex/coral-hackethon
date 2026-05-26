from pathlib import Path
import json

from incident_captain.handoff import write_handoff_note


def test_write_handoff_note(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "progress_report.json").write_text(json.dumps({"progress_percent": 100}), encoding="utf-8")
    (report_dir / "live_readiness.json").write_text(json.dumps({"blockers": ["x"]}), encoding="utf-8")
    (report_dir / "release_check.json").write_text(
        json.dumps({"go_for_submission": True, "go_for_live_submission": False}),
        encoding="utf-8",
    )
    (report_dir / "scorecard.json").write_text(json.dumps({"overall_score": 90}), encoding="utf-8")
    (report_dir / "next_actions.json").write_text(json.dumps({"actions": ["do-a"]}), encoding="utf-8")
    out = report_dir / "handoff_note.md"
    payload = write_handoff_note(report_dir, out)
    assert out.exists()
    assert payload["scorecard_overall"] == 90

