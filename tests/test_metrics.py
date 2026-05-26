from pathlib import Path
import json

from incident_captain.metrics import append_run_metrics
from incident_captain.models import IncidentBrief


def test_append_run_metrics(tmp_path: Path) -> None:
    path = tmp_path / "run_metrics.jsonl"
    brief = IncidentBrief(
        incident_id="INC-7",
        summary="summary",
        probable_root_cause="cause",
        confidence="high",
    )
    append_run_metrics(
        path,
        incident_id="INC-7",
        mode="mock",
        total_duration_ms=123,
        brief=brief,
    )
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["incident_id"] == "INC-7"
    assert payload["mode"] == "mock"
    assert payload["total_duration_ms"] == 123

