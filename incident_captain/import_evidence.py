from __future__ import annotations

from pathlib import Path
import shutil


def import_live_evidence(
    *,
    tables_file: Path,
    columns_file: Path,
    filters_file: Path,
    live_metrics_file: Path,
    output_root: Path,
) -> dict[str, str]:
    catalog_dir = output_root / "catalog"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    out_tables = catalog_dir / "catalog_tables.json"
    out_columns = catalog_dir / "catalog_columns.json"
    out_filters = catalog_dir / "catalog_filters.json"

    shutil.copy2(tables_file, out_tables)
    shutil.copy2(columns_file, out_columns)
    shutil.copy2(filters_file, out_filters)

    out_metrics = output_root / "run_metrics.jsonl"
    shutil.copy2(live_metrics_file, out_metrics)

    return {
        "catalog_tables": str(out_tables),
        "catalog_columns": str(out_columns),
        "catalog_filters": str(out_filters),
        "run_metrics": str(out_metrics),
    }

