from pathlib import Path
import json

from incident_captain.next_actions import write_next_actions


def test_write_next_actions(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "progress_report.json").write_text(
        json.dumps({"pending_checks": ["x"]}),
        encoding="utf-8",
    )
    (report_dir / "live_readiness.json").write_text(
        json.dumps({"blockers": ["no_live_runs_recorded"]}),
        encoding="utf-8",
    )
    (report_dir / "release_check.json").write_text(
        json.dumps({"go_for_submission": False, "go_for_live_submission": False}),
        encoding="utf-8",
    )

    out_json = report_dir / "next_actions.json"
    out_md = report_dir / "next_actions.md"
    payload = write_next_actions(report_dir, out_json, out_md)
    assert payload["pending_count"] >= 1
    assert out_json.exists()
    assert out_md.exists()

