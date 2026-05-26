from pathlib import Path
import json

from incident_captain.quality import run_quality_gate


def test_quality_gate_pass(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    report_dir = tmp_path / "report"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "INC-11.json").write_text("{}", encoding="utf-8")
    (output_dir / "INC-11.md").write_text("# x", encoding="utf-8")
    (output_dir / "workflow_log.json").write_text("[]", encoding="utf-8")
    (output_dir / "run_metrics.jsonl").write_text("{}", encoding="utf-8")
    (report_dir / "demo_report.json").write_text(
        json.dumps({"success_rate": 0.9}),
        encoding="utf-8",
    )
    (report_dir / "impact_report.json").write_text(
        json.dumps({"improvement_percent": 25}),
        encoding="utf-8",
    )

    result = run_quality_gate(
        incident_id="INC-11",
        output_dir=output_dir,
        report_dir=report_dir,
    )
    assert result["passed"] is True


def test_quality_gate_fail(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    report_dir = tmp_path / "report"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    (report_dir / "demo_report.json").write_text(
        json.dumps({"success_rate": 0.2}),
        encoding="utf-8",
    )
    (report_dir / "impact_report.json").write_text(
        json.dumps({"improvement_percent": 2}),
        encoding="utf-8",
    )

    result = run_quality_gate(
        incident_id="INC-11",
        output_dir=output_dir,
        report_dir=report_dir,
    )
    assert result["passed"] is False

