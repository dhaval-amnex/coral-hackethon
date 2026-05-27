from pathlib import Path
import json
from argparse import Namespace

from incident_captain.briefing import QUERY_FILES
from incident_captain.cli import cmd_finalize
from incident_captain.coral import CoralClient
from incident_captain.finalize import write_final_summary


def test_write_final_summary(tmp_path: Path) -> None:
    out = tmp_path / "final_summary.json"
    payload = {"ok": True}
    write_final_summary(out, payload)
    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8"))["ok"] is True


def test_finalize(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PAGERDUTY_API_TOKEN", "x")
    monkeypatch.setenv("DD_API_KEY", "x")
    monkeypatch.setenv("DD_APPLICATION_KEY", "x")
    monkeypatch.setenv("SLACK_TOKEN", "x")
    monkeypatch.setenv("GITHUB_TOKEN", "x")

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

    out_dir = tmp_path / "output"
    report_dir = out_dir / "report"
    args = Namespace(
        incident_id="INC-Z1",
        root=str(tmp_path),
        output_dir=str(out_dir),
        report_dir=str(report_dir),
        bundle_root=str(out_dir / "bundles"),
        metrics_log=str(out_dir / "run_metrics.jsonl"),
        workflow_log=str(out_dir / "workflow_log.json"),
        baseline_file=str(baseline),
        sql_dir=str(sql_dir),
        coral_bin="coral",
        min_success_rate=0.0,
        min_improvement_percent=0.0,
        min_progress_percent=0.0,
        min_scorecard_overall=0.0,
        github_owner="o",
        github_repo="r",
        env_file="",
    )
    _ = cmd_finalize(args)
    assert (report_dir / "final_summary.json").exists()
