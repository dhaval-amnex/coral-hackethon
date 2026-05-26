from pathlib import Path
import json
import subprocess
import sys

from incident_captain.batch import write_batch_summary


def test_write_batch_summary(tmp_path: Path) -> None:
    summary = write_batch_summary(
        tmp_path / "batch_summary.json",
        [
            {"incident_id": "INC-1", "status": "passed"},
            {"incident_id": "INC-2", "status": "failed"},
        ],
    )
    assert summary["total_incidents"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 1


def test_batch_run_mock(tmp_path: Path) -> None:
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

    out_root = tmp_path / "batch"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "incident_captain.cli",
            "batch-run",
            "--incident-ids",
            "INC-A,INC-B",
            "--output-root",
            str(out_root),
            "--mock-data-dir",
            str(mock_dir),
            "--baseline-file",
            str(baseline),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert (out_root / "batch_summary.json").exists()

