from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil


def _copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def create_submission_bundle(
    *,
    incident_id: str,
    output_dir: Path,
    report_dir: Path,
    bundle_root: Path,
    include_docs_dir: Path | None = None,
) -> dict[str, str]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bundle_dir = bundle_root / f"submission_bundle_{incident_id}_{timestamp}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "brief_json": output_dir / f"{incident_id}.json",
        "brief_md": output_dir / f"{incident_id}.md",
        "workflow_log": output_dir / "workflow_log.json",
        "run_metrics": output_dir / "run_metrics.jsonl",
        "demo_report_json": report_dir / "demo_report.json",
        "demo_report_md": report_dir / "demo_report.md",
    }

    manifest: dict[str, str] = {}
    for key, src in files.items():
        dst = bundle_dir / src.name
        manifest[key] = str(dst) if _copy_if_exists(src, dst) else "missing"

    if include_docs_dir is not None and include_docs_dir.exists():
        docs_dst = bundle_dir / "deliverables_docs"
        docs_dst.mkdir(parents=True, exist_ok=True)
        for name in ("architecture-plan.md", "metrics-plan.md", "security-checklist.md"):
            src = include_docs_dir / name
            dst = docs_dst / name
            if _copy_if_exists(src, dst):
                manifest[f"docs_{name}"] = str(dst)

    manifest_path = bundle_dir / "bundle_manifest.txt"
    manifest_lines = ["Submission Bundle Manifest", ""]
    for key, value in manifest.items():
        manifest_lines.append(f"{key}: {value}")
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")
    manifest["manifest"] = str(manifest_path)
    manifest["bundle_dir"] = str(bundle_dir)
    return manifest

