from pathlib import Path
import json
from argparse import Namespace

from incident_captain.batch import write_batch_summary
from incident_captain.briefing import QUERY_FILES
from incident_captain.cli import cmd_batch_run
from incident_captain.coral import CoralClient


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


def test_batch_run(tmp_path: Path, monkeypatch) -> None:
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir(parents=True, exist_ok=True)
    for _, file_name in QUERY_FILES:
        (sql_dir / file_name).write_text("SELECT 1", encoding="utf-8")

    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps([{"manual_minutes": 30, "assisted_minutes": 10}]),
        encoding="utf-8",
    )

    def fake_run_sql(self, sql: str):
        return ([{"title": "x", "service": "checkout", "text": "incident"}], 1)

    monkeypatch.setattr(CoralClient, "run_sql", fake_run_sql)

    out_root = tmp_path / "batch"
    args = Namespace(
        incident_ids="INC-A,INC-B",
        output_root=str(out_root),
        baseline_file=str(baseline),
        sql_dir=str(sql_dir),
        coral_bin="coral",
        min_success_rate=0.0,
        min_improvement_percent=0.0,
    )
    rc = cmd_batch_run(args)
    assert rc == 0
    assert (out_root / "batch_summary.json").exists()
