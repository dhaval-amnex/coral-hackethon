from pathlib import Path
import json

from incident_captain.scorecard import write_scorecard


def test_write_scorecard(tmp_path: Path) -> None:
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "demo_report.json").write_text(
        json.dumps({"success_rate": 0.9, "avg_duration_ms": 120.0}),
        encoding="utf-8",
    )
    (report_dir / "impact_report.json").write_text(
        json.dumps({"improvement_percent": 35.0}),
        encoding="utf-8",
    )
    quality_file = report_dir / "quality_gate.json"
    quality_file.write_text(
        json.dumps({"passed": True, "checks": [{"passed": True}, {"passed": True}]}),
        encoding="utf-8",
    )

    out_json = report_dir / "scorecard.json"
    out_md = report_dir / "scorecard.md"
    scorecard = write_scorecard(
        report_dir=report_dir,
        quality_gate_path=quality_file,
        out_json=out_json,
        out_md=out_md,
    )

    assert scorecard["overall_score"] > 0
    assert scorecard["quality_gate_passed"] is True
    assert out_json.exists()
    assert out_md.exists()

