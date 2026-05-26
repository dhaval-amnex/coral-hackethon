from pathlib import Path
import json

from incident_captain.reporting import write_demo_report


def test_write_demo_report(tmp_path: Path) -> None:
    metrics = tmp_path / "run_metrics.jsonl"
    metrics.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "incident_id": "INC-1",
                        "total_duration_ms": 100,
                        "confidence": "high",
                        "evidence_count": 4,
                        "query_errors": 0,
                    }
                ),
                json.dumps(
                    {
                        "incident_id": "INC-2",
                        "total_duration_ms": 200,
                        "confidence": "medium",
                        "evidence_count": 2,
                        "query_errors": 1,
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    out_json = tmp_path / "demo_report.json"
    out_md = tmp_path / "demo_report.md"
    summary = write_demo_report(metrics, out_json, out_md)

    assert summary["total_runs"] == 2
    assert summary["avg_duration_ms"] == 150.0
    assert summary["confidence_distribution"]["high"] == 1
    assert summary["confidence_distribution"]["medium"] == 1
    assert out_json.exists()
    assert out_md.exists()

