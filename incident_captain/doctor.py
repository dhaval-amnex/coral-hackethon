from __future__ import annotations

import platform
import shutil
from pathlib import Path
from typing import Any


def build_doctor_report(root: Path) -> dict[str, Any]:
    output_dir = root / "output"
    report_dir = output_dir / "report"
    coral_path = shutil.which("coral")

    checks = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "coral_available": bool(coral_path),
        "coral_path": coral_path or "",
        "output_dir_exists": output_dir.exists(),
        "report_dir_exists": report_dir.exists(),
        "has_demo_report": (report_dir / "demo_report.json").exists(),
        "has_impact_report": (report_dir / "impact_report.json").exists(),
        "has_quality_gate": (report_dir / "quality_gate.json").exists(),
        "has_scorecard": (report_dir / "scorecard.json").exists(),
    }
    return checks

