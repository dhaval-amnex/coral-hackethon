from pathlib import Path
import json
from argparse import Namespace

from incident_captain.briefing import QUERY_FILES
from incident_captain.cli import cmd_demo_run
from incident_captain.coral import CoralClient


def test_demo_run(tmp_path: Path, monkeypatch) -> None:
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

    output_dir = tmp_path / "out"
    report_dir = output_dir / "report"
    bundle_root = output_dir / "bundles"
    args = Namespace(
        coral_bin="coral",
        sql_dir=str(sql_dir),
        env_file="",
        incident_id="INC-2001",
        output_dir=str(output_dir),
        report_dir=str(report_dir),
        bundle_root=str(bundle_root),
        metrics_log=str(output_dir / "run_metrics.jsonl"),
        workflow_log=str(output_dir / "workflow_log.json"),
        baseline_file=str(baseline),
        min_success_rate=0.0,
        min_improvement_percent=0.0,
        github_owner="o",
        github_repo="r",
    )
    rc = cmd_demo_run(args)
    assert rc == 0
    assert (output_dir / "INC-2001.json").exists()
    assert (report_dir / "demo_report.json").exists()
    assert (report_dir / "impact_report.json").exists()
    assert any(bundle_root.glob("submission_bundle_INC-2001_*"))
