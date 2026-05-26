from pathlib import Path
import json

from incident_captain.live_unblock import write_live_unblock_summary


def test_write_live_unblock_summary(tmp_path: Path) -> None:
    out = tmp_path / "live_unblock_summary.json"
    payload = {"live_ready": False, "go_for_live_submission": False, "pending_actions": ["x"]}
    write_live_unblock_summary(out, payload)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["pending_actions"] == ["x"]

