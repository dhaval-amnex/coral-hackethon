from pathlib import Path
import json

from incident_captain.plan_audit import build_plan_audit


def test_build_plan_audit(tmp_path: Path) -> None:
    report_dir = tmp_path / "output" / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "progress_report.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    (report_dir / "live_readiness.json").write_text(
        json.dumps({"blockers": ["catalog_snapshot_missing_or_empty"]}),
        encoding="utf-8",
    )
    (report_dir / "release_check.json").write_text(
        json.dumps({"go_for_submission": True, "go_for_live_submission": False}),
        encoding="utf-8",
    )
    payload = build_plan_audit(tmp_path)
    assert payload["go_for_submission"] is True
    assert payload["go_for_live_submission"] is False
    assert payload["pending_items"]

