from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bundling import create_submission_bundle
from .coral import CoralClient, CoralError
from .exporters import write_json, write_markdown
from .impact import write_impact_report
from .metrics import append_run_metrics
from .orchestration import run_deterministic_workflow, write_workflow_log
from .quality import run_quality_gate
from .reporting import write_demo_report


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
    return 0 if result["passed"] else 1


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
        parser.error("unknown command")
        return 2
    except CoralError as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
