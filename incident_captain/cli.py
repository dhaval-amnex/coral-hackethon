from __future__ import annotations

import argparse
import json
from pathlib import Path

from .briefing import compose_brief, run_incident_queries
from .coral import CoralClient, CoralError
from .exporters import write_json, write_markdown


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

    health = sub.add_parser("health", help="Run source health checks.")
    health.add_argument(
        "--sources",
        nargs="+",
        default=["pagerduty", "github", "slack", "datadog"],
        help="Source names to test.",
    )
    return parser


def cmd_analyze(args: argparse.Namespace) -> int:
    coral = CoralClient(coral_bin=args.coral_bin)
    sql_dir = Path(args.sql_dir)
    mock_data_dir = Path(args.mock_data_dir) if args.mock_data_dir else None
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    runs, errors = run_incident_queries(coral, sql_dir, args.incident_id, mock_data_dir)
    brief = compose_brief(args.incident_id, runs, errors)

    json_path = output_dir / f"{args.incident_id}.json"
    md_path = output_dir / f"{args.incident_id}.md"
    write_json(json_path, brief)
    write_markdown(md_path, brief)

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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "analyze":
            return cmd_analyze(args)
        if args.command == "health":
            return cmd_health(args)
        parser.error("unknown command")
        return 2
    except CoralError as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
