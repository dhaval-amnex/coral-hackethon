from pathlib import Path

from incident_captain.import_evidence import import_live_evidence


def test_import_live_evidence(tmp_path: Path) -> None:
    tables = tmp_path / "tables.json"
    columns = tmp_path / "columns.json"
    filters = tmp_path / "filters.json"
    metrics = tmp_path / "metrics.jsonl"
    tables.write_text("[]", encoding="utf-8")
    columns.write_text("[]", encoding="utf-8")
    filters.write_text("[]", encoding="utf-8")
    metrics.write_text('{"mode":"live"}\n', encoding="utf-8")

    result = import_live_evidence(
        tables_file=tables,
        columns_file=columns,
        filters_file=filters,
        live_metrics_file=metrics,
        output_root=tmp_path / "output",
    )
    assert Path(result["catalog_tables"]).exists()
    assert Path(result["catalog_columns"]).exists()
    assert Path(result["catalog_filters"]).exists()
    assert Path(result["run_metrics"]).exists()

