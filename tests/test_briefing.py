from incident_captain.briefing import compose_brief
from incident_captain.coral import QueryRun


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


def test_compose_brief_low_confidence_when_no_data() -> None:
    brief = compose_brief("INC-2", [], ["query failed"])
    assert brief.confidence == "low"
    assert "Insufficient evidence" in brief.probable_root_cause

