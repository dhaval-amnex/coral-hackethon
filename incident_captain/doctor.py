from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import validate_source_env
from .coral import find_coral_bin


def build_doctor_report(root: Path) -> dict[str, Any]:
    output_dir = root / "output"
    report_dir = output_dir / "report"

    coral_bin = find_coral_bin()
    coral_path = shutil.which(coral_bin) or (coral_bin if Path(coral_bin).exists() else "")
    coral_available = bool(coral_path)

    coral_version = ""
    configured_sources: list[str] = []
    if coral_available:
        try:
            v = subprocess.run([coral_bin, "--version"], capture_output=True, text=True, check=False)
            coral_version = v.stdout.strip() or v.stderr.strip()
            ls = subprocess.run([coral_bin, "source", "list"], capture_output=True, text=True, check=False)
            for line in ls.stdout.strip().splitlines()[1:]:
                parts = line.split()
                if parts:
                    configured_sources.append(parts[0])
        except Exception:
            pass

    checks = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "coral_available": coral_available,
        "coral_path": coral_path,
        "coral_version": coral_version,
        "configured_sources": configured_sources,
        "output_dir_exists": output_dir.exists(),
        "report_dir_exists": report_dir.exists(),
        "has_demo_report": (report_dir / "demo_report.json").exists(),
        "has_impact_report": (report_dir / "impact_report.json").exists(),
        "has_quality_gate": (report_dir / "quality_gate.json").exists(),
        "has_scorecard": (report_dir / "scorecard.json").exists(),
    }
    sources_to_validate = configured_sources or ["pagerduty", "github", "slack", "datadog"]
    env_validation = validate_source_env(sources_to_validate)
    checks["env_validation_ok"] = env_validation.ok
    checks["env_missing"] = env_validation.missing
    return checks

