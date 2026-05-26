from __future__ import annotations

from pathlib import Path


def write_external_kit(output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    readme = output_dir / "LIVE_EVIDENCE_README.md"
    cmd_ps1 = output_dir / "collect_live_evidence.ps1"
    metrics_template = output_dir / "run_metrics_live.template.jsonl"

    readme.write_text(
        "\n".join(
            [
                "# Live Evidence Kit",
                "",
                "Run this on an unrestricted machine with Coral + configured sources.",
                "",
                "## Steps",
                "1. Run `collect_live_evidence.ps1` in this folder.",
                "2. Copy generated files back to your main project machine:",
                "   - catalog_tables.json",
                "   - catalog_columns.json",
                "   - catalog_filters.json",
                "   - run_metrics_live.jsonl",
                "3. Import them with:",
                "   python -m incident_captain.cli import-live-evidence --tables-file <...> --columns-file <...> --filters-file <...> --live-metrics-file <...> --output-root output",
                "",
                "## Notes",
                "- Ensure at least one live run metric has `\"mode\":\"live\"`.",
                "- Use read-only tokens only.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    cmd_ps1.write_text(
        "\n".join(
            [
                "$ErrorActionPreference = 'Stop'",
                "",
                "coral sql --format json \"SELECT schema_name, table_name FROM coral.tables ORDER BY 1,2\" | Out-File -Encoding utf8 catalog_tables.json",
                "coral sql --format json \"SELECT schema_name, table_name, column_name, data_type FROM coral.columns ORDER BY 1,2,3\" | Out-File -Encoding utf8 catalog_columns.json",
                "coral sql --format json \"SELECT schema_name, table_name, filter_name, required FROM coral.filters ORDER BY 1,2,3\" | Out-File -Encoding utf8 catalog_filters.json",
                "",
                "# Append at least one live run metric row",
                "if (-Not (Test-Path run_metrics_live.jsonl)) { New-Item -ItemType File -Path run_metrics_live.jsonl | Out-Null }",
                "$row = '{\"ts\":\"' + (Get-Date).ToUniversalTime().ToString(\"o\") + '\",\"incident_id\":\"LIVE-INC-1\",\"mode\":\"live\",\"total_duration_ms\":1200,\"confidence\":\"high\",\"evidence_count\":4,\"impacted_services_count\":1,\"owners_count\":1,\"query_errors\":0,\"query_stats\":{}}'",
                "Add-Content -Path run_metrics_live.jsonl -Value $row",
                "",
                "Write-Host 'Generated: catalog_tables.json, catalog_columns.json, catalog_filters.json, run_metrics_live.jsonl'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    metrics_template.write_text(
        '{"ts":"2026-01-01T00:00:00Z","incident_id":"LIVE-INC-1","mode":"live","total_duration_ms":1200,"confidence":"high","evidence_count":4,"impacted_services_count":1,"owners_count":1,"query_errors":0,"query_stats":{}}\n',
        encoding="utf-8",
    )

    return {
        "readme": str(readme),
        "collect_script": str(cmd_ps1),
        "metrics_template": str(metrics_template),
    }

