from pathlib import Path
import json

from incident_captain.live_playbook import write_live_playbook


def test_write_live_playbook(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "live_readiness.json").write_text(
        json.dumps({"blockers": ["catalog_snapshot_missing_or_empty", "no_live_runs_recorded"]}),
        encoding="utf-8",
    )
    out = report_dir / "live_playbook.md"
    payload = write_live_playbook(report_dir, out)
    assert out.exists()
    assert payload["blockers"]
    assert len(payload["steps"]) >= 3

