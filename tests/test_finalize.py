from pathlib import Path
import json
import subprocess
import sys

from incident_captain.finalize import write_final_summary


def test_write_final_summary(tmp_path: Path) -> None:
    out = tmp_path / "final_summary.json"
    payload = {"ok": True}
    write_final_summary(out, payload)
    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8"))["ok"] is True


def test_finalize_mock(tmp_path: Path) -> None:
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

    out_dir = tmp_path / "output"
    report_dir = out_dir / "report"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "incident_captain.cli",
            "finalize",
            "--incident-id",
            "INC-Z1",
            "--mock-data-dir",
            str(mock_dir),
            "--output-dir",
            str(out_dir),
            "--report-dir",
            str(report_dir),
            "--bundle-root",
            str(out_dir / "bundles"),
            "--metrics-log",
            str(out_dir / "run_metrics.jsonl"),
            "--workflow-log",
            str(out_dir / "workflow_log.json"),
            "--baseline-file",
            str(baseline),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    # offline mode may fail live readiness in release-check; summary file must exist regardless
    assert (report_dir / "final_summary.json").exists(), proc.stderr or proc.stdout

