from pathlib import Path
import json

from incident_captain.impact import write_impact_report


def test_write_impact_report(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            [
                {"manual_minutes": 30, "assisted_minutes": 10},
                {"manual_minutes": 20, "assisted_minutes": 8},
            ]
        ),
        encoding="utf-8",
    )
    metrics = tmp_path / "metrics.jsonl"
    metrics.write_text(
        "\n".join(
            [
                json.dumps({"total_duration_ms": 1000}),
                json.dumps({"total_duration_ms": 2000}),
            ]
        ),
        encoding="utf-8",
    )
    out_json = tmp_path / "impact_report.json"
    out_md = tmp_path / "impact_report.md"
    summary = write_impact_report(baseline, metrics, out_json, out_md)
    assert summary["avg_manual_minutes"] == 25.0
    assert summary["avg_assisted_minutes"] == 9.0
    assert summary["minutes_saved"] == 16.0
    assert out_json.exists()
    assert out_md.exists()

