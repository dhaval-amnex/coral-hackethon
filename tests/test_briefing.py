from incident_captain.briefing import compose_brief
from incident_captain.coral import QueryRun
from incident_captain.briefing import run_incident_queries
from incident_captain.coral import CoralClient
from pathlib import Path
import json


def test_compose_brief_high_confidence() -> None:
    runs = [
        QueryRun(
            name="final_dataset",
            duration_ms=120,
            rows=[
                {
                    "repo": "api",
                    "sha": "abc123",
                    "author": "alice",
                    "metric_name": "error_rate",
                    "value": 12.1,
                    "service": "checkout",
                    "user_name": "bob",
                    "text": "seeing errors after deploy",
                }
            ],
        )
    ]
    brief = compose_brief("INC-1", runs, [])
    assert brief.incident_id == "INC-1"
    assert brief.confidence in {"medium", "high"}
    assert len(brief.evidence) >= 1
    assert brief.impacted_services
    assert len(brief.executive_summary) == 6


def test_compose_brief_low_confidence_when_no_data() -> None:
    brief = compose_brief("INC-2", [], ["query failed"])
    assert brief.confidence == "low"
    assert "Insufficient evidence" in brief.probable_root_cause
    assert len(brief.executive_summary) == 6


def test_run_incident_queries_mock_mode(tmp_path: Path) -> None:
    files = [
        "active_incidents.json",
        "deploy_correlation.json",
        "telemetry_context.json",
        "team_comms.json",
        "final_dataset.json",
    ]
    for file_name in files:
        (tmp_path / file_name).write_text(json.dumps([{"x": 1}]), encoding="utf-8")

    runs, errors = run_incident_queries(
        CoralClient("coral"),
        sql_dir=tmp_path,
        incident_id="INC-3",
        mock_data_dir=tmp_path,
    )
    assert len(runs) == 5
    assert errors == []
