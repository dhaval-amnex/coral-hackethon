from pathlib import Path
import json
import subprocess
import sys


def test_close_live_loop_mocked_import(tmp_path: Path) -> None:
    # prepare importable live evidence files
    tables = tmp_path / "catalog_tables.json"
    columns = tmp_path / "catalog_columns.json"
    filters = tmp_path / "catalog_filters.json"
    metrics = tmp_path / "run_metrics_live.jsonl"
    tables.write_text(json.dumps([{"schema_name": "x", "table_name": "y"}]), encoding="utf-8")
    columns.write_text(json.dumps([{"schema_name": "x", "table_name": "y", "column_name": "z"}]), encoding="utf-8")
    filters.write_text(json.dumps([{"schema_name": "x", "table_name": "y", "filter_name": "f"}]), encoding="utf-8")
    metrics.write_text(json.dumps({"mode": "live"}) + "\n", encoding="utf-8")

    # provide mock query data for finalize analyze step fallback would be live;
    # here we only assert command wiring path exists, not success status
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "incident_captain.cli",
            "close-live-loop",
            "--incident-id",
            "INC-CLOSE",
            "--tables-file",
            str(tables),
            "--columns-file",
            str(columns),
            "--filters-file",
            str(filters),
            "--live-metrics-file",
            str(metrics),
            "--output-root",
            str(tmp_path / "output"),
            "--report-dir",
            str(tmp_path / "output" / "report"),
            "--bundle-root",
            str(tmp_path / "output" / "bundles"),
            "--workflow-log",
            str(tmp_path / "output" / "workflow_log.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    # may fail later if no live coral query possible in test env; import stage must still have copied files
    assert (tmp_path / "output" / "catalog" / "catalog_tables.json").exists(), proc.stderr or proc.stdout

