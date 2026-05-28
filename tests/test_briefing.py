from incident_captain.briefing import QUERY_FILES, compose_brief
from incident_captain.coral import QueryRun
from incident_captain.briefing import run_incident_queries
from incident_captain.coral import CoralClient
from pathlib import Path


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
    assert "coverage" in brief.diagnostics


def test_compose_brief_missing_families_reduces_confidence() -> None:
    runs = [
        QueryRun(
            name="telemetry_context",
            duration_ms=80,
            rows=[
                {
                    "metric_name": "cpu_usage",
                    "value": 93.2,
                    "timestamp": "2026-05-28T10:00:00Z",
                    "service": "checkout",
                }
            ],
        )
    ]
    brief = compose_brief("INC-9", runs, [])
    assert brief.confidence == "low"
    assert "coverage" in brief.diagnostics
    coverage = brief.diagnostics["coverage"]
    assert isinstance(coverage, dict)
    assert coverage["score"] <= 1


def test_compose_brief_low_confidence_when_no_data() -> None:
    brief = compose_brief("INC-2", [], ["query failed"])
    assert brief.confidence == "low"
    assert "Insufficient evidence" in brief.probable_root_cause
    assert len(brief.executive_summary) == 6


def test_run_incident_queries(tmp_path: Path, monkeypatch) -> None:
    for _, file_name in QUERY_FILES:
        (tmp_path / file_name).write_text("SELECT 1", encoding="utf-8")

    def fake_run_sql(self, sql: str):
        return ([{"x": 1}], 1)

    monkeypatch.setattr(CoralClient, "run_sql", fake_run_sql)

    runs, errors = run_incident_queries(
        CoralClient("coral"),
        sql_dir=tmp_path,
        incident_id="INC-3",
        extra_vars={"GITHUB_OWNER": "o", "GITHUB_REPO": "r"},
    )
    assert len(runs) == 5
    assert errors == []
