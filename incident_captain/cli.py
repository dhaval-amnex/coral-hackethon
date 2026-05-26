from __future__ import annotations

import argparse
import json
from pathlib import Path

from .batch import write_batch_summary
from .bundling import create_submission_bundle
from .coral import CoralClient, CoralError, find_coral_bin, load_env_file
from .dashboard import write_dashboard
from .doctor import build_doctor_report
from .evidence_verify import verify_evidence
from .exporters import write_json, write_markdown
from .external_kit import write_external_kit
from .finalize import write_final_summary
from .handoff import write_handoff_note
from .impact import write_impact_report
from .import_evidence import import_live_evidence
from .judge_pack import create_judge_pack
from .live_unblock import write_live_unblock_summary
from .live_playbook import write_live_playbook
from .metrics import append_run_metrics
from .next_actions import write_next_actions
from .orchestration import run_deterministic_workflow, write_workflow_log
from .plan_audit import build_plan_audit
from .progress import write_progress_report
from .quality import run_quality_gate
from .readiness import write_live_readiness_report
from .release import write_release_check
from .reporting import write_demo_report
from .scorecard import write_scorecard


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="incident-captain",
        description="Coral-powered enterprise incident investigation CLI.",
    )

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--coral-bin", default=find_coral_bin(), help="Path to coral executable.")
    common.add_argument(
        "--sql-dir",
        default="deliverables/sql",
        help="Directory containing SQL templates.",
    )
    common.add_argument(
        "--mock-data-dir",
        default="",
        help="Optional directory containing mock JSON files per query name.",
    )
    common.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file with API credentials (loaded before live queries).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", parents=[common], help="Run incident analysis workflow.")
    analyze.add_argument("--incident-id", required=True, help="Incident identifier.")
    analyze.add_argument(
        "--output-dir",
        default="output",
        help="Directory for generated artifacts.",
    )
    analyze.add_argument(
        "--view",
        choices=["full", "executive"],
        default="full",
        help="Console output style.",
    )
    analyze.add_argument(
        "--metrics-log",
        default="output/run_metrics.jsonl",
        help="Path to JSONL metrics log.",
    )
    analyze.add_argument(
        "--workflow-log",
        default="output/workflow_log.json",
        help="Path to workflow step log JSON.",
    )
    analyze.add_argument("--github-owner", default="", help="GitHub org/user for deploy correlation.")
    analyze.add_argument("--github-repo", default="", help="GitHub repo name for deploy correlation.")

    health = sub.add_parser("health", parents=[common], help="Run source health checks.")
    health.add_argument(
        "--sources",
        nargs="+",
        default=["pagerduty", "github", "slack", "datadog"],
        help="Source names to test.",
    )

    snapshot = sub.add_parser("snapshot-catalog", parents=[common], help="Export Coral catalog metadata to JSON.")
    snapshot.add_argument(
        "--output-dir",
        default="output/catalog",
        help="Directory for catalog snapshots.",
    )

    report = sub.add_parser("demo-report", help="Generate judge-ready report from run metrics.")
    report.add_argument(
        "--metrics-log",
        default="output/run_metrics.jsonl",
        help="Path to JSONL metrics log.",
    )
    report.add_argument(
        "--output-dir",
        default="output/report",
        help="Directory for generated report files.",
    )

    bundle = sub.add_parser("submission-bundle", help="Create a judge-ready artifact bundle.")
    bundle.add_argument("--incident-id", required=True, help="Incident identifier to bundle.")
    bundle.add_argument("--output-dir", default="output", help="Directory containing brief/workflow/metrics.")
    bundle.add_argument("--report-dir", default="output/report", help="Directory containing demo report artifacts.")
    bundle.add_argument("--bundle-root", default="output/bundles", help="Destination root for bundle folders.")

    impact = sub.add_parser("impact-report", help="Generate time-saved impact report.")
    impact.add_argument("--baseline-file", default="deliverables/mock/baseline_times.json", help="Baseline JSON file.")
    impact.add_argument("--metrics-log", default="output/run_metrics.jsonl", help="Run metrics JSONL file.")
    impact.add_argument("--output-dir", default="output/report", help="Directory for impact report output.")

    quality = sub.add_parser("quality-gate", help="Run submission readiness checks.")
    quality.add_argument("--incident-id", required=True, help="Incident identifier.")
    quality.add_argument("--output-dir", default="output", help="Output artifact directory.")
    quality.add_argument("--report-dir", default="output/report", help="Report artifact directory.")
    quality.add_argument("--min-success-rate", type=float, default=0.7, help="Minimum demo success rate.")
    quality.add_argument(
        "--min-improvement-percent",
        type=float,
        default=10.0,
        help="Minimum time-saved improvement percent.",
    )

    demo = sub.add_parser("demo-run", parents=[common], help="Run full demo pipeline end-to-end.")
    demo.add_argument("--incident-id", required=True, help="Incident identifier.")
    demo.add_argument("--output-dir", default="output", help="Primary output directory.")
    demo.add_argument("--report-dir", default="output/report", help="Report output directory.")
    demo.add_argument("--bundle-root", default="output/bundles", help="Bundle destination root.")
    demo.add_argument("--metrics-log", default="output/run_metrics.jsonl", help="Metrics log path.")
    demo.add_argument("--workflow-log", default="output/workflow_log.json", help="Workflow log path.")
    demo.add_argument("--baseline-file", default="deliverables/mock/baseline_times.json", help="Baseline file.")
    demo.add_argument("--min-success-rate", type=float, default=0.7, help="Quality gate threshold.")
    demo.add_argument("--min-improvement-percent", type=float, default=10.0, help="Quality gate threshold.")
    demo.add_argument("--github-owner", default="", help="GitHub org/user for deploy correlation.")
    demo.add_argument("--github-repo", default="", help="GitHub repo name for deploy correlation.")

    batch = sub.add_parser("batch-run", parents=[common], help="Run demo pipeline across multiple incidents.")
    batch.add_argument("--incident-ids", required=True, help="Comma-separated incident IDs.")
    batch.add_argument("--output-root", default="output/batch", help="Root output directory for batch runs.")
    batch.add_argument("--baseline-file", default="deliverables/mock/baseline_times.json", help="Baseline file.")
    batch.add_argument("--min-success-rate", type=float, default=0.7, help="Quality gate threshold.")
    batch.add_argument("--min-improvement-percent", type=float, default=10.0, help="Quality gate threshold.")

    scorecard = sub.add_parser("scorecard", help="Generate judge-facing scorecard from reports.")
    scorecard.add_argument("--report-dir", default="output/report", help="Directory containing demo and impact reports.")
    scorecard.add_argument(
        "--quality-gate-file",
        default="output/report/quality_gate.json",
        help="Path to quality gate result JSON file.",
    )
    scorecard.add_argument("--output-dir", default="output/report", help="Directory for scorecard output.")

    progress = sub.add_parser("progress-report", help="Generate implementation progress report.")
    progress.add_argument("--root", default=".", help="Project root path.")
    progress.add_argument("--output-dir", default="output/report", help="Directory for progress report output.")

    readiness = sub.add_parser("live-readiness", help="Check readiness for real-data submission.")
    readiness.add_argument("--root", default=".", help="Project root path.")
    readiness.add_argument("--output-dir", default="output/report", help="Directory for readiness report output.")

    release = sub.add_parser("release-check", help="Generate final go/no-go release decision report.")
    release.add_argument("--root", default=".", help="Project root path.")
    release.add_argument("--output-dir", default="output/report", help="Directory for release report output.")

    finalize = sub.add_parser("finalize", parents=[common], help="Run full finalization pipeline and emit final summary.")
    finalize.add_argument("--incident-id", required=True, help="Incident identifier.")
    finalize.add_argument("--root", default=".", help="Project root path.")
    finalize.add_argument("--output-dir", default="output", help="Primary output directory.")
    finalize.add_argument("--report-dir", default="output/report", help="Report output directory.")
    finalize.add_argument("--bundle-root", default="output/bundles", help="Bundle destination root.")
    finalize.add_argument("--metrics-log", default="output/run_metrics.jsonl", help="Metrics log path.")
    finalize.add_argument("--workflow-log", default="output/workflow_log.json", help="Workflow log path.")
    finalize.add_argument("--baseline-file", default="deliverables/mock/baseline_times.json", help="Baseline file.")
    finalize.add_argument("--min-success-rate", type=float, default=0.7, help="Quality gate threshold.")
    finalize.add_argument("--min-improvement-percent", type=float, default=10.0, help="Quality gate threshold.")
    finalize.add_argument("--github-owner", default="", help="GitHub org/user for deploy correlation.")
    finalize.add_argument("--github-repo", default="", help="GitHub repo name for deploy correlation.")

    next_cmd = sub.add_parser("next-actions", help="Generate prioritized pending actions from report artifacts.")
    next_cmd.add_argument("--report-dir", default="output/report", help="Directory containing report artifacts.")
    next_cmd.add_argument("--output-dir", default="output/report", help="Directory for next-actions output.")

    import_cmd = sub.add_parser(
        "import-live-evidence",
        help="Import live catalog snapshots and live run metrics from another machine.",
    )
    import_cmd.add_argument("--tables-file", required=True, help="Path to catalog_tables.json from live environment.")
    import_cmd.add_argument("--columns-file", required=True, help="Path to catalog_columns.json from live environment.")
    import_cmd.add_argument("--filters-file", required=True, help="Path to catalog_filters.json from live environment.")
    import_cmd.add_argument("--live-metrics-file", required=True, help="Path to live run_metrics.jsonl.")
    import_cmd.add_argument("--output-root", default="output", help="Project output root directory.")

    verify_cmd = sub.add_parser("evidence-verify", help="Verify external live evidence file quality.")
    verify_cmd.add_argument("--tables-file", required=True, help="Path to catalog_tables.json from live environment.")
    verify_cmd.add_argument("--columns-file", required=True, help="Path to catalog_columns.json from live environment.")
    verify_cmd.add_argument("--filters-file", required=True, help="Path to catalog_filters.json from live environment.")
    verify_cmd.add_argument("--live-metrics-file", required=True, help="Path to live run_metrics.jsonl.")
    verify_cmd.add_argument("--output-file", default="output/report/evidence_verify.json", help="Verification report JSON.")

    kit_cmd = sub.add_parser("external-kit", help="Generate a handoff kit for collecting live evidence externally.")
    kit_cmd.add_argument("--output-dir", default="output/external_kit", help="Directory for generated kit files.")

    unblock_cmd = sub.add_parser("live-unblock", help="Run unblock checks after importing live evidence.")
    unblock_cmd.add_argument("--root", default=".", help="Project root path.")
    unblock_cmd.add_argument("--report-dir", default="output/report", help="Directory for report artifacts.")

    doctor_cmd = sub.add_parser("doctor", help="Run local environment diagnostics.")
    doctor_cmd.add_argument("--root", default=".", help="Project root path.")

    close_cmd = sub.add_parser("close-live-loop", help="Import live evidence and run live-unblock + finalize flow.")
    close_cmd.add_argument("--incident-id", required=True, help="Incident identifier.")
    close_cmd.add_argument("--tables-file", required=True, help="Path to catalog_tables.json from live environment.")
    close_cmd.add_argument("--columns-file", required=True, help="Path to catalog_columns.json from live environment.")
    close_cmd.add_argument("--filters-file", required=True, help="Path to catalog_filters.json from live environment.")
    close_cmd.add_argument("--live-metrics-file", required=True, help="Path to live run_metrics.jsonl.")
    close_cmd.add_argument("--output-root", default="output", help="Project output root directory.")
    close_cmd.add_argument("--report-dir", default="output/report", help="Directory for report artifacts.")
    close_cmd.add_argument("--bundle-root", default="output/bundles", help="Bundle destination root.")
    close_cmd.add_argument("--workflow-log", default="output/workflow_log.json", help="Workflow log path.")
    close_cmd.add_argument("--baseline-file", default="deliverables/mock/baseline_times.json", help="Baseline file.")

    dash_cmd = sub.add_parser("status-dashboard", help="Generate one-page status dashboard from reports.")
    dash_cmd.add_argument("--report-dir", default="output/report", help="Directory containing report artifacts.")
    dash_cmd.add_argument("--output-file", default="output/report/status_dashboard.md", help="Output markdown file.")

    pack_cmd = sub.add_parser("judge-pack", help="Create a single ZIP pack for judge submission/review.")
    pack_cmd.add_argument("--source-dir", default="", help="Source directory to zip (defaults to latest bundle).")
    pack_cmd.add_argument("--bundle-root", default="output/bundles", help="Bundle root to auto-pick latest from.")
    pack_cmd.add_argument("--output-zip", default="output/judge_pack.zip", help="Output zip file path.")

    handoff_cmd = sub.add_parser("handoff-note", help="Generate a concise handoff markdown from latest reports.")
    handoff_cmd.add_argument("--report-dir", default="output/report", help="Directory containing report artifacts.")
    handoff_cmd.add_argument("--output-file", default="output/report/handoff_note.md", help="Output markdown file.")

    audit_cmd = sub.add_parser("plan-audit", help="Audit current state against implementation phases.")
    audit_cmd.add_argument("--root", default=".", help="Project root path.")
    audit_cmd.add_argument("--output-file", default="output/report/plan_audit.json", help="Output JSON file.")

    playbook_cmd = sub.add_parser("live-playbook", help="Generate step-by-step live unblocking playbook.")
    playbook_cmd.add_argument("--report-dir", default="output/report", help="Directory containing report artifacts.")
    playbook_cmd.add_argument("--output-file", default="output/report/live_playbook.md", help="Output markdown file.")

    setup_cmd = sub.add_parser("setup-sources", parents=[common], help="Configure Coral data sources from credentials.")
    setup_cmd.add_argument(
        "--sources",
        nargs="+",
        default=["pagerduty", "github", "slack", "datadog"],
        help="Source names to configure.",
    )
    setup_cmd.add_argument(
        "--skip-test",
        action="store_true",
        help="Skip connectivity test after adding sources.",
    )

    snapshot_live = sub.add_parser("snapshot-schema", parents=[common], help="Snapshot live Coral schema to output/catalog.")
    snapshot_live.add_argument("--output-dir", default="output/catalog", help="Directory for catalog snapshots.")

    return parser


def _load_env(args: argparse.Namespace) -> None:
    env_file = getattr(args, "env_file", ".env")
    if env_file:
        load_env_file(Path(env_file))


def cmd_analyze(args: argparse.Namespace) -> int:
    if not getattr(args, "mock_data_dir", ""):
        _load_env(args)
    coral = CoralClient(coral_bin=args.coral_bin)
    sql_dir = Path(args.sql_dir)
    mock_data_dir = Path(args.mock_data_dir) if args.mock_data_dir else None
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    extra_vars: dict[str, str] = {}
    if getattr(args, "github_owner", ""):
        extra_vars["GITHUB_OWNER"] = args.github_owner
    if getattr(args, "github_repo", ""):
        extra_vars["GITHUB_REPO"] = args.github_repo

    workflow = run_deterministic_workflow(
        coral=coral,
        incident_id=args.incident_id,
        sql_dir=sql_dir,
        mock_data_dir=mock_data_dir,
        extra_vars=extra_vars or None,
    )
    brief = workflow.brief

    json_path = output_dir / f"{args.incident_id}.json"
    md_path = output_dir / f"{args.incident_id}.md"
    write_json(json_path, brief)
    write_markdown(md_path, brief)
    write_workflow_log(Path(args.workflow_log), workflow.workflow_log)
    append_run_metrics(
        Path(args.metrics_log),
        incident_id=args.incident_id,
        mode="mock" if mock_data_dir else "live",
        total_duration_ms=workflow.total_duration_ms,
        brief=brief,
    )

    if args.view == "executive":
        payload = {
            "incident_id": brief.incident_id,
            "confidence": brief.confidence,
            "executive_summary": brief.executive_summary,
            "recommended_actions": brief.recommended_actions[:3],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(brief.to_dict(), indent=2))
    print(f"\nWrote: {json_path}")
    print(f"Wrote: {md_path}")
    print(f"Wrote metrics: {args.metrics_log}")
    print(f"Wrote workflow log: {args.workflow_log}")
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    if not args.mock_data_dir:
        _load_env(args)
    if args.mock_data_dir:
        mock_data_dir = Path(args.mock_data_dir)
        required = [
            "active_incidents.json",
            "deploy_correlation.json",
            "telemetry_context.json",
            "team_comms.json",
            "final_dataset.json",
        ]
        status = {}
        for file_name in required:
            status[file_name] = "ok" if (mock_data_dir / file_name).exists() else "missing"
        print(json.dumps(status, indent=2))
        return 0 if all(v == "ok" for v in status.values()) else 1

    coral = CoralClient(coral_bin=args.coral_bin)
    status = coral.source_health(args.sources)
    print(json.dumps(status, indent=2))
    return 0 if all(v == "ok" for v in status.values()) else 1


def cmd_snapshot_catalog(args: argparse.Namespace) -> int:
    _load_env(args)
    coral = CoralClient(coral_bin=args.coral_bin)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tables_sql = "SELECT schema_name, table_name FROM coral.tables ORDER BY 1,2"
    columns_sql = "SELECT schema_name, table_name, column_name, data_type FROM coral.columns ORDER BY 1,2,3"
    filters_sql = "SELECT schema_name, table_name, filter_name, is_required FROM coral.filters ORDER BY 1,2,3"

    tables, _ = coral.run_sql(tables_sql)
    columns, _ = coral.run_sql(columns_sql)
    filters, _ = coral.run_sql(filters_sql)

    (out_dir / "catalog_tables.json").write_text(json.dumps(tables, indent=2), encoding="utf-8")
    (out_dir / "catalog_columns.json").write_text(json.dumps(columns, indent=2), encoding="utf-8")
    (out_dir / "catalog_filters.json").write_text(json.dumps(filters, indent=2), encoding="utf-8")

    print(f"Wrote: {out_dir / 'catalog_tables.json'}")
    print(f"Wrote: {out_dir / 'catalog_columns.json'}")
    print(f"Wrote: {out_dir / 'catalog_filters.json'}")
    return 0


def cmd_demo_report(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    out_json = out_dir / "demo_report.json"
    out_md = out_dir / "demo_report.md"
    summary = write_demo_report(Path(args.metrics_log), out_json, out_md)
    print(json.dumps(summary, indent=2))
    print(f"Wrote: {out_json}")
    print(f"Wrote: {out_md}")
    return 0


def cmd_submission_bundle(args: argparse.Namespace) -> int:
    manifest = create_submission_bundle(
        incident_id=args.incident_id,
        output_dir=Path(args.output_dir),
        report_dir=Path(args.report_dir),
        bundle_root=Path(args.bundle_root),
        include_docs_dir=Path("deliverables/docs"),
    )
    print(json.dumps(manifest, indent=2))
    return 0


def cmd_impact_report(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    out_json = out_dir / "impact_report.json"
    out_md = out_dir / "impact_report.md"
    summary = write_impact_report(
        baseline_path=Path(args.baseline_file),
        metrics_path=Path(args.metrics_log),
        out_json=out_json,
        out_md=out_md,
    )
    print(json.dumps(summary, indent=2))
    print(f"Wrote: {out_json}")
    print(f"Wrote: {out_md}")
    return 0


def cmd_quality_gate(args: argparse.Namespace) -> int:
    result = run_quality_gate(
        incident_id=args.incident_id,
        output_dir=Path(args.output_dir),
        report_dir=Path(args.report_dir),
        min_success_rate=args.min_success_rate,
        min_improvement_percent=args.min_improvement_percent,
    )
    print(json.dumps(result, indent=2))
    qg_path = Path(args.report_dir) / "quality_gate.json"
    qg_path.parent.mkdir(parents=True, exist_ok=True)
    qg_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote: {qg_path}")
    return 0 if result["passed"] else 1


def cmd_demo_run(args: argparse.Namespace) -> int:
    class Obj:
        pass

    analyze_args = Obj()
    analyze_args.coral_bin = args.coral_bin
    analyze_args.sql_dir = args.sql_dir
    analyze_args.mock_data_dir = args.mock_data_dir
    analyze_args.env_file = getattr(args, "env_file", ".env")
    analyze_args.command = "analyze"
    analyze_args.incident_id = args.incident_id
    analyze_args.output_dir = args.output_dir
    analyze_args.view = "executive"
    analyze_args.metrics_log = args.metrics_log
    analyze_args.workflow_log = args.workflow_log
    analyze_args.github_owner = getattr(args, "github_owner", "")
    analyze_args.github_repo = getattr(args, "github_repo", "")
    rc = cmd_analyze(analyze_args)
    if rc != 0:
        return rc

    report_args = Obj()
    report_args.command = "demo-report"
    report_args.metrics_log = args.metrics_log
    report_args.output_dir = args.report_dir
    rc = cmd_demo_report(report_args)
    if rc != 0:
        return rc

    impact_args = Obj()
    impact_args.command = "impact-report"
    impact_args.baseline_file = args.baseline_file
    impact_args.metrics_log = args.metrics_log
    impact_args.output_dir = args.report_dir
    rc = cmd_impact_report(impact_args)
    if rc != 0:
        return rc

    quality_args = Obj()
    quality_args.command = "quality-gate"
    quality_args.incident_id = args.incident_id
    quality_args.output_dir = args.output_dir
    quality_args.report_dir = args.report_dir
    quality_args.min_success_rate = args.min_success_rate
    quality_args.min_improvement_percent = args.min_improvement_percent
    rc = cmd_quality_gate(quality_args)
    if rc != 0:
        return rc

    bundle_args = Obj()
    bundle_args.command = "submission-bundle"
    bundle_args.incident_id = args.incident_id
    bundle_args.output_dir = args.output_dir
    bundle_args.report_dir = args.report_dir
    bundle_args.bundle_root = args.bundle_root
    rc = cmd_submission_bundle(bundle_args)
    return rc


def cmd_batch_run(args: argparse.Namespace) -> int:
    class Obj:
        pass

    incident_ids = [x.strip() for x in args.incident_ids.split(",") if x.strip()]
    output_root = Path(args.output_root)
    rows = []
    for incident_id in incident_ids:
        incident_root = output_root / incident_id
        out_dir = incident_root / "output"
        report_dir = out_dir / "report"
        bundle_root = out_dir / "bundles"
        metrics_log = out_dir / "run_metrics.jsonl"
        workflow_log = out_dir / "workflow_log.json"

        demo_args = Obj()
        demo_args.command = "demo-run"
        demo_args.incident_id = incident_id
        demo_args.output_dir = str(out_dir)
        demo_args.report_dir = str(report_dir)
        demo_args.bundle_root = str(bundle_root)
        demo_args.metrics_log = str(metrics_log)
        demo_args.workflow_log = str(workflow_log)
        demo_args.baseline_file = args.baseline_file
        demo_args.mock_data_dir = args.mock_data_dir
        demo_args.sql_dir = args.sql_dir
        demo_args.coral_bin = args.coral_bin
        demo_args.min_success_rate = args.min_success_rate
        demo_args.min_improvement_percent = args.min_improvement_percent
        rc = cmd_demo_run(demo_args)
        rows.append(
            {
                "incident_id": incident_id,
                "status": "passed" if rc == 0 else "failed",
                "exit_code": rc,
                "output_dir": str(out_dir),
            }
        )

    summary_path = output_root / "batch_summary.json"
    summary = write_batch_summary(summary_path, rows)
    print(json.dumps(summary, indent=2))
    print(f"Wrote: {summary_path}")
    return 0 if summary["failed"] == 0 else 1


def cmd_scorecard(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    out_json = out_dir / "scorecard.json"
    out_md = out_dir / "scorecard.md"
    scorecard = write_scorecard(
        report_dir=Path(args.report_dir),
        quality_gate_path=Path(args.quality_gate_file),
        out_json=out_json,
        out_md=out_md,
    )
    print(json.dumps(scorecard, indent=2))
    print(f"Wrote: {out_json}")
    print(f"Wrote: {out_md}")
    return 0


def cmd_progress_report(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    out_json = out_dir / "progress_report.json"
    out_md = out_dir / "progress_report.md"
    report = write_progress_report(Path(args.root), out_json, out_md)
    print(json.dumps(report, indent=2))
    print(f"Wrote: {out_json}")
    print(f"Wrote: {out_md}")
    return 0


def cmd_live_readiness(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    out_json = out_dir / "live_readiness.json"
    out_md = out_dir / "live_readiness.md"
    report = write_live_readiness_report(Path(args.root), out_json, out_md)
    print(json.dumps(report, indent=2))
    print(f"Wrote: {out_json}")
    print(f"Wrote: {out_md}")
    return 0 if report["ready_for_live_submission"] else 1


def cmd_release_check(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    out_json = out_dir / "release_check.json"
    out_md = out_dir / "release_check.md"
    report = write_release_check(Path(args.root), out_json, out_md)
    print(json.dumps(report, indent=2))
    print(f"Wrote: {out_json}")
    print(f"Wrote: {out_md}")
    return 0 if report["go_for_submission"] else 1


def cmd_finalize(args: argparse.Namespace) -> int:
    class Obj:
        pass

    demo_args = Obj()
    demo_args.command = "demo-run"
    demo_args.incident_id = args.incident_id
    demo_args.output_dir = args.output_dir
    demo_args.report_dir = args.report_dir
    demo_args.bundle_root = args.bundle_root
    demo_args.metrics_log = args.metrics_log
    demo_args.workflow_log = args.workflow_log
    demo_args.baseline_file = args.baseline_file
    demo_args.mock_data_dir = args.mock_data_dir
    demo_args.sql_dir = args.sql_dir
    demo_args.coral_bin = args.coral_bin
    demo_args.min_success_rate = args.min_success_rate
    demo_args.min_improvement_percent = args.min_improvement_percent
    demo_args.github_owner = getattr(args, "github_owner", "")
    demo_args.github_repo = getattr(args, "github_repo", "")
    rc = cmd_demo_run(demo_args)
    if rc != 0:
        return rc

    score_args = Obj()
    score_args.command = "scorecard"
    score_args.report_dir = args.report_dir
    score_args.quality_gate_file = str(Path(args.report_dir) / "quality_gate.json")
    score_args.output_dir = args.report_dir
    rc = cmd_scorecard(score_args)
    if rc != 0:
        return rc

    prog_args = Obj()
    prog_args.command = "progress-report"
    prog_args.root = args.root
    prog_args.output_dir = args.report_dir
    rc = cmd_progress_report(prog_args)
    if rc != 0:
        return rc

    ready_args = Obj()
    ready_args.command = "live-readiness"
    ready_args.root = args.root
    ready_args.output_dir = args.report_dir
    _ = cmd_live_readiness(ready_args)  # non-blocking for offline mode

    release_args = Obj()
    release_args.command = "release-check"
    release_args.root = args.root
    release_args.output_dir = args.report_dir
    rc_release = cmd_release_check(release_args)

    final_summary = {
        "incident_id": args.incident_id,
        "artifacts": {
            "brief_json": str(Path(args.output_dir) / f"{args.incident_id}.json"),
            "brief_md": str(Path(args.output_dir) / f"{args.incident_id}.md"),
            "report_dir": str(Path(args.report_dir)),
            "bundle_root": str(Path(args.bundle_root)),
        },
        "release_check_exit_code": rc_release,
        "note": "release_check_exit_code may be non-zero in offline-only environments due to live-readiness blockers.",
    }
    out = Path(args.report_dir) / "final_summary.json"
    write_final_summary(out, final_summary)
    print(json.dumps(final_summary, indent=2))
    print(f"Wrote: {out}")
    return 0 if rc_release == 0 else 1


def cmd_next_actions(args: argparse.Namespace) -> int:
    out_dir = Path(args.output_dir)
    out_json = out_dir / "next_actions.json"
    out_md = out_dir / "next_actions.md"
    payload = write_next_actions(Path(args.report_dir), out_json, out_md)
    print(json.dumps(payload, indent=2))
    print(f"Wrote: {out_json}")
    print(f"Wrote: {out_md}")
    return 0


def cmd_import_live_evidence(args: argparse.Namespace) -> int:
    result = import_live_evidence(
        tables_file=Path(args.tables_file),
        columns_file=Path(args.columns_file),
        filters_file=Path(args.filters_file),
        live_metrics_file=Path(args.live_metrics_file),
        output_root=Path(args.output_root),
    )
    print(json.dumps(result, indent=2))
    return 0


def cmd_evidence_verify(args: argparse.Namespace) -> int:
    report = verify_evidence(
        tables_file=Path(args.tables_file),
        columns_file=Path(args.columns_file),
        filters_file=Path(args.filters_file),
        live_metrics_file=Path(args.live_metrics_file),
    )
    out = Path(args.output_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Wrote: {out}")
    return 0 if report["passed"] else 1


def cmd_external_kit(args: argparse.Namespace) -> int:
    result = write_external_kit(Path(args.output_dir))
    print(json.dumps(result, indent=2))
    return 0


def cmd_live_unblock(args: argparse.Namespace) -> int:
    class Obj:
        pass

    ready_args = Obj()
    ready_args.root = args.root
    ready_args.output_dir = args.report_dir
    _ = cmd_live_readiness(ready_args)

    release_args = Obj()
    release_args.root = args.root
    release_args.output_dir = args.report_dir
    _ = cmd_release_check(release_args)

    next_args = Obj()
    next_args.report_dir = args.report_dir
    next_args.output_dir = args.report_dir
    _ = cmd_next_actions(next_args)

    live_readiness = json.loads((Path(args.report_dir) / "live_readiness.json").read_text(encoding="utf-8"))
    release_check = json.loads((Path(args.report_dir) / "release_check.json").read_text(encoding="utf-8"))
    next_actions = json.loads((Path(args.report_dir) / "next_actions.json").read_text(encoding="utf-8"))

    summary = {
        "live_ready": live_readiness.get("ready_for_live_submission", False),
        "go_for_live_submission": release_check.get("go_for_live_submission", False),
        "pending_actions": next_actions.get("actions", []),
    }
    out = Path(args.report_dir) / "live_unblock_summary.json"
    write_live_unblock_summary(out, summary)
    print(json.dumps(summary, indent=2))
    print(f"Wrote: {out}")
    return 0 if summary["go_for_live_submission"] else 1


def cmd_doctor(args: argparse.Namespace) -> int:
    report = build_doctor_report(Path(args.root))
    print(json.dumps(report, indent=2))
    return 0


def cmd_close_live_loop(args: argparse.Namespace) -> int:
    class Obj:
        pass

    import_args = Obj()
    import_args.tables_file = args.tables_file
    import_args.columns_file = args.columns_file
    import_args.filters_file = args.filters_file
    import_args.live_metrics_file = args.live_metrics_file
    import_args.output_root = args.output_root
    rc = cmd_import_live_evidence(import_args)
    if rc != 0:
        return rc

    unblock_args = Obj()
    unblock_args.root = "."
    unblock_args.report_dir = args.report_dir
    _ = cmd_live_unblock(unblock_args)

    finalize_args = Obj()
    finalize_args.incident_id = args.incident_id
    finalize_args.root = "."
    finalize_args.output_dir = args.output_root
    finalize_args.report_dir = args.report_dir
    finalize_args.bundle_root = args.bundle_root
    finalize_args.metrics_log = str(Path(args.output_root) / "run_metrics.jsonl")
    finalize_args.workflow_log = args.workflow_log
    finalize_args.baseline_file = args.baseline_file
    finalize_args.mock_data_dir = ""
    finalize_args.sql_dir = "deliverables/sql"
    finalize_args.coral_bin = "coral"
    finalize_args.min_success_rate = 0.7
    finalize_args.min_improvement_percent = 10.0
    return cmd_finalize(finalize_args)


def cmd_status_dashboard(args: argparse.Namespace) -> int:
    payload = write_dashboard(Path(args.report_dir), Path(args.output_file))
    print(json.dumps({"written": args.output_file, "has_reports": {k: bool(v) for k, v in payload.items()}}, indent=2))
    return 0


def _latest_bundle_dir(bundle_root: Path) -> Path | None:
    if not bundle_root.exists():
        return None
    dirs = [p for p in bundle_root.iterdir() if p.is_dir() and p.name.startswith("submission_bundle_")]
    if not dirs:
        return None
    dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return dirs[0]


def cmd_judge_pack(args: argparse.Namespace) -> int:
    source_dir = Path(args.source_dir) if args.source_dir else None
    if source_dir is None:
        source_dir = _latest_bundle_dir(Path(args.bundle_root))
        if source_dir is None:
            print("Error: no source-dir provided and no submission bundle found.")
            return 1
    if not source_dir.exists():
        print(f"Error: source directory does not exist: {source_dir}")
        return 1
    out = create_judge_pack(source_dir, Path(args.output_zip))
    print(json.dumps({"source_dir": str(source_dir), "output_zip": str(out)}, indent=2))
    return 0


def cmd_handoff_note(args: argparse.Namespace) -> int:
    payload = write_handoff_note(Path(args.report_dir), Path(args.output_file))
    print(json.dumps({"written": args.output_file, "summary": payload}, indent=2))
    return 0


def cmd_plan_audit(args: argparse.Namespace) -> int:
    payload = build_plan_audit(Path(args.root))
    out = Path(args.output_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    print(f"Wrote: {out}")
    return 0


def cmd_live_playbook(args: argparse.Namespace) -> int:
    payload = write_live_playbook(Path(args.report_dir), Path(args.output_file))
    print(json.dumps(payload, indent=2))
    print(f"Wrote: {args.output_file}")
    return 0


def cmd_setup_sources(args: argparse.Namespace) -> int:
    _load_env(args)
    coral = CoralClient(coral_bin=args.coral_bin)
    results: dict[str, str] = {}
    for source in args.sources:
        ok, msg = coral.setup_source(source)
        results[source] = "added" if ok else f"failed: {msg}"
        status = "ok" if ok else "FAILED"
        print(f"  [{status}] {source}: {msg}")

    if not args.skip_test:
        print("\nTesting source connectivity...")
        try:
            health = coral.source_health(args.sources)
        except CoralError as exc:
            print(f"Health check error: {exc}")
            health = {}
        for src, state in health.items():
            print(f"  [{state.upper()}] {src}")
    else:
        health = {}

    summary = {"setup": results, "health": health}
    print(json.dumps(summary, indent=2))
    return 0 if all(v == "added" for v in results.values()) else 1


def cmd_snapshot_schema(args: argparse.Namespace) -> int:
    _load_env(args)
    coral = CoralClient(coral_bin=args.coral_bin)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tables_sql = "SELECT schema_name, table_name FROM coral.tables ORDER BY 1,2"
    columns_sql = "SELECT schema_name, table_name, column_name, data_type FROM coral.columns ORDER BY 1,2,3"
    filters_sql = "SELECT schema_name, table_name, filter_name, is_required FROM coral.filters ORDER BY 1,2,3"

    tables, _ = coral.run_sql(tables_sql)
    columns, _ = coral.run_sql(columns_sql)
    filters, _ = coral.run_sql(filters_sql)

    (out_dir / "catalog_tables.json").write_text(json.dumps(tables, indent=2), encoding="utf-8")
    (out_dir / "catalog_columns.json").write_text(json.dumps(columns, indent=2), encoding="utf-8")
    (out_dir / "catalog_filters.json").write_text(json.dumps(filters, indent=2), encoding="utf-8")

    print(f"Wrote: {out_dir / 'catalog_tables.json'} ({len(tables)} tables)")
    print(f"Wrote: {out_dir / 'catalog_columns.json'} ({len(columns)} columns)")
    print(f"Wrote: {out_dir / 'catalog_filters.json'} ({len(filters)} filters)")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "analyze":
            return cmd_analyze(args)
        if args.command == "health":
            return cmd_health(args)
        if args.command == "snapshot-catalog":
            return cmd_snapshot_catalog(args)
        if args.command == "demo-report":
            return cmd_demo_report(args)
        if args.command == "submission-bundle":
            return cmd_submission_bundle(args)
        if args.command == "impact-report":
            return cmd_impact_report(args)
        if args.command == "quality-gate":
            return cmd_quality_gate(args)
        if args.command == "demo-run":
            return cmd_demo_run(args)
        if args.command == "batch-run":
            return cmd_batch_run(args)
        if args.command == "scorecard":
            return cmd_scorecard(args)
        if args.command == "progress-report":
            return cmd_progress_report(args)
        if args.command == "live-readiness":
            return cmd_live_readiness(args)
        if args.command == "release-check":
            return cmd_release_check(args)
        if args.command == "finalize":
            return cmd_finalize(args)
        if args.command == "next-actions":
            return cmd_next_actions(args)
        if args.command == "import-live-evidence":
            return cmd_import_live_evidence(args)
        if args.command == "evidence-verify":
            return cmd_evidence_verify(args)
        if args.command == "external-kit":
            return cmd_external_kit(args)
        if args.command == "live-unblock":
            return cmd_live_unblock(args)
        if args.command == "doctor":
            return cmd_doctor(args)
        if args.command == "close-live-loop":
            return cmd_close_live_loop(args)
        if args.command == "status-dashboard":
            return cmd_status_dashboard(args)
        if args.command == "judge-pack":
            return cmd_judge_pack(args)
        if args.command == "handoff-note":
            return cmd_handoff_note(args)
        if args.command == "plan-audit":
            return cmd_plan_audit(args)
        if args.command == "live-playbook":
            return cmd_live_playbook(args)
        if args.command == "setup-sources":
            return cmd_setup_sources(args)
        if args.command == "snapshot-schema":
            return cmd_snapshot_schema(args)
        parser.error("unknown command")
        return 2
    except CoralError as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
