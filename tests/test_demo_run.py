from pathlib import Path
import json
import subprocess
import sys


def test_demo_run_mock(tmp_path: Path) -> None:
    mock_dir = tmp_path / "mock"
    mock_dir.mkdir(parents=True, exist_ok=True)
    for name in [
        "active_incidents.json",
        "deploy_correlation.json",
        "telemetry_context.json",
        "team_comms.json",
        "final_dataset.json",
    ]:
        (mock_dir / name).write_text(
            json.dumps([{"title": "x", "service": "checkout", "text": "incident"}]),
            encoding="utf-8",
        )

    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps([{"manual_minutes": 30, "assisted_minutes": 10}]),
        encoding="utf-8",
    )

    output_dir = tmp_path / "out"
    report_dir = output_dir / "report"
    bundle_root = output_dir / "bundles"
    metrics_log = output_dir / "run_metrics.jsonl"
    workflow_log = output_dir / "workflow_log.json"

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "incident_captain.cli",
            "demo-run",
            "--incident-id",
            "INC-2001",
            "--mock-data-dir",
            str(mock_dir),
            "--output-dir",
            str(output_dir),
            "--report-dir",
            str(report_dir),
            "--bundle-root",
            str(bundle_root),
            "--metrics-log",
            str(metrics_log),
            "--workflow-log",
            str(workflow_log),
            "--baseline-file",
            str(baseline),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert (output_dir / "INC-2001.json").exists()
    assert (report_dir / "demo_report.json").exists()
    assert (report_dir / "impact_report.json").exists()
    assert any(bundle_root.glob("submission_bundle_INC-2001_*"))

