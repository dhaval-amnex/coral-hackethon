from pathlib import Path

from incident_captain.bundling import create_submission_bundle


def test_create_submission_bundle(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    report_dir = tmp_path / "report"
    docs_dir = tmp_path / "docs"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "INC-10.json").write_text("{}", encoding="utf-8")
    (output_dir / "INC-10.md").write_text("# brief", encoding="utf-8")
    (output_dir / "workflow_log.json").write_text("[]", encoding="utf-8")
    (output_dir / "run_metrics.jsonl").write_text("", encoding="utf-8")
    (report_dir / "demo_report.json").write_text("{}", encoding="utf-8")
    (report_dir / "demo_report.md").write_text("# report", encoding="utf-8")
    (docs_dir / "architecture-plan.md").write_text("# arch", encoding="utf-8")
    (docs_dir / "metrics-plan.md").write_text("# metrics", encoding="utf-8")
    (docs_dir / "security-checklist.md").write_text("# sec", encoding="utf-8")

    manifest = create_submission_bundle(
        incident_id="INC-10",
        output_dir=output_dir,
        report_dir=report_dir,
        bundle_root=tmp_path / "bundles",
        include_docs_dir=docs_dir,
    )

    bundle_dir = Path(manifest["bundle_dir"])
    assert bundle_dir.exists()
    assert (bundle_dir / "INC-10.json").exists()
    assert (bundle_dir / "INC-10.md").exists()
    assert (bundle_dir / "bundle_manifest.txt").exists()

