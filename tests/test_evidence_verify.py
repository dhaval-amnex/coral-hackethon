from pathlib import Path
import json

from incident_captain.evidence_verify import verify_evidence


def test_verify_evidence_pass(tmp_path: Path) -> None:
    tables = tmp_path / "tables.json"
    columns = tmp_path / "columns.json"
    filters = tmp_path / "filters.json"
    metrics = tmp_path / "live.jsonl"
    tables.write_text(json.dumps([{"a": 1}]), encoding="utf-8")
    columns.write_text(json.dumps([{"a": 1}]), encoding="utf-8")
    filters.write_text(json.dumps([{"a": 1}]), encoding="utf-8")
    metrics.write_text(json.dumps({"mode": "live"}) + "\n", encoding="utf-8")

    report = verify_evidence(
        tables_file=tables,
        columns_file=columns,
        filters_file=filters,
        live_metrics_file=metrics,
    )
    assert report["passed"] is True


def test_verify_evidence_fail(tmp_path: Path) -> None:
    tables = tmp_path / "tables.json"
    columns = tmp_path / "columns.json"
    filters = tmp_path / "filters.json"
    metrics = tmp_path / "live.jsonl"
    tables.write_text("[]", encoding="utf-8")
    columns.write_text("[]", encoding="utf-8")
    filters.write_text("[]", encoding="utf-8")
    metrics.write_text(json.dumps({"mode": "mock"}) + "\n", encoding="utf-8")

    report = verify_evidence(
        tables_file=tables,
        columns_file=columns,
        filters_file=filters,
        live_metrics_file=metrics,
    )
    assert report["passed"] is False

