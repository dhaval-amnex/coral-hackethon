from __future__ import annotations

import argparse
import json
from pathlib import Path

from .batch import write_batch_summary
from .bundling import create_submission_bundle
from .coral import CoralClient, CoralError
from .exporters import write_json, write_markdown
from .finalize import write_final_summary
from .impact import write_impact_report
from .metrics import append_run_metrics
from .next_actions import write_next_actions
from .orchestration import run_deterministic_workflow, write_workflow_log
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
    parser.add_argument("--coral-bin", default="coral", help="Path to coral executable.")
    parser.add_argument(
        "--sql-dir",
        default="deliverables/sql",
        help="Directory containing SQL templates.",
    )
    parser.add_argument(
        "--mock-data-dir",
        default="",
        help="Optional directory containing mock JSON files per query name.",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="Run incident analysis workflow.")
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

    health = sub.add_parser("health", help="Run source health checks.")
    health.add_argument(
        "--sources",
        nargs="+",
        default=["pagerduty", "github", "slack", "datadog"],
        help="Source names to test.",
    )

    snapshot = sub.add_parser("snapshot-catalog", help="Export Coral catalog metadata to JSON.")
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

    demo = sub.add_parser("demo-run", help="Run full demo pipeline end-to-end.")
    demo.add_argument("--incident-id", required=True, help="Incident identifier.")
    demo.add_argument("--output-dir", default="output", help="Primary output directory.")
    demo.add_argument("--report-dir", default="output/report", help="Report output directory.")
    demo.add_argument("--bundle-root", default="output/bundles", help="Bundle destination root.")
    demo.add_argument("--metrics-log", default="output/run_metrics.jsonl", help="Metrics log path.")
    demo.add_argument("--workflow-log", default="output/workflow_log.json", help="Workflow log path.")
    demo.add_argument("--baseline-file", default="deliverables/mock/baseline_times.json", help="Baseline file.")
    demo.add_argument("--mock-data-dir", default="", help="Optional mock data directory.")
    demo.add_argument("--sql-dir", default="deliverables/sql", help="SQL templates directory.")
    demo.add_argument("--coral-bin", default="coral", help="Path to coral executable.")
    demo.add_argument("--min-success-rate", type=float, default=0.7, help="Quality gate threshold.")
    demo.add_argument("--min-improvement-percent", type=float, default=10.0, help="Quality gate threshold.")

    batch = sub.add_parser("batch-run", help="Run demo pipeline across multiple incidents.")
    batch.add_argument("--incident-ids", required=True, help="Comma-separated incident IDs.")
    batch.add_argument("--output-root", default="output/batch", help="Root output directory for batch runs.")
    batch.add_argument("--mock-data-dir", default="", help="Optional mock data directory.")
    batch.add_argument("--sql-dir", default="deliverables/sql", help="SQL templates directory.")
    batch.add_argument("--coral-bin", default="coral", help="Path to coral executable.")
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

    finalize = sub.add_parser("finalize", help="Run full finalization pipeline and emit final summary.")
    finalize.add_argument("--incident-id", required=True, help="Incident identifier.")
    finalize.add_argument("--root", default=".", help="Project root path.")
    finalize.add_argument("--output-dir", default="output", help="Primary output directory.")
    finalize.add_argument("--report-dir", default="output/report", help="Report output directory.")
    finalize.add_argument("--bundle-root", default="output/bundles", help="Bundle destination root.")
    finalize.add_argument("--metrics-log", default="output/run_metrics.jsonl", help="Metrics log path.")
    finalize.add_argument("--workflow-log", default="output/workflow_log.json", help="Workflow log path.")
    finalize.add_argument("--baseline-file", default="deliverables/mock/baseline_times.json", help="Baseline file.")
    finalize.add_argument("--mock-data-dir", default="", help="Optional mock data directory.")
    finalize.add_argument("--sql-dir", default="deliverables/sql", help="SQL templates directory.")
    finalize.add_argument("--coral-bin", default="coral", help="Path to coral executable.")
    finalize.add_argument("--min-success-rate", type=float, default=0.7, help="Quality gate threshold.")
    finalize.add_argument("--min-improvement-percent", type=float, default=10.0, help="Quality gate threshold.")

    next_cmd = sub.add_parser("next-actions", help="Generate prioritized pending actions from report artifacts.")
    next_cmd.add_argument("--report-dir", default="output/report", help="Directory containing report artifacts.")
    next_cmd.add_argument("--output-dir", default="output/report", help="Directory for next-actions output.")
    return parser


def cmd_analyze(args: argparse.Namespace) -> int:
    coral = CoralClient(coral_bin=args.coral_bin)
    sql_dir = Path(args.sql_dir)
    mock_data_dir = Path(args.mock_data_dir) if args.mock_data_dir else None
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    workflow = run_deterministic_workflow(
        coral=coral,
        incident_id=args.incident_id,
        sql_dir=sql_dir,
        mock_data_dir=mock_data_dir,
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
    coral = CoralClient(coral_bin=args.coral_bin)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tables_sql = "SELECT schema_name, table_name FROM coral.tables ORDER BY 1,2"
    columns_sql = "SELECT schema_name, table_name, column_name, data_type FROM coral.columns ORDER BY 1,2,3"
    filters_sql = "SELECT schema_name, table_name, filter_name, required FROM coral.filters ORDER BY 1,2,3"

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
    analyze_args.command = "analyze"
    analyze_args.incident_id = args.incident_id
    analyze_args.output_dir = args.output_dir
    analyze_args.view = "executive"
    analyze_args.metrics_log = args.metrics_log
    analyze_args.workflow_log = args.workflow_log
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
        parser.error("unknown command")
        return 2
    except CoralError as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
