from __future__ import annotations

import json
from pathlib import Path

from .models import IncidentBrief


def write_json(path: Path, brief: IncidentBrief) -> None:
    path.write_text(json.dumps(brief.to_dict(), indent=2), encoding="utf-8")


def write_markdown(path: Path, brief: IncidentBrief) -> None:
    lines: list[str] = [
        f"# Incident Brief: {brief.incident_id}",
        "",
        f"**Confidence:** {brief.confidence}",
        "",
        "## Summary",
        brief.summary,
        "",
        "## Probable Root Cause",
        brief.probable_root_cause,
        "",
        "## Impacted Services",
    ]
    if brief.impacted_services:
        lines.extend([f"- {s}" for s in brief.impacted_services])
    else:
        lines.append("- No services inferred")

    lines.extend(["", "## Owners"])
    if brief.owners:
        lines.extend([f"- {o}" for o in brief.owners])
    else:
        lines.append("- No owners inferred")

    lines.extend(["", "## Evidence"])
    if brief.evidence:
        for ev in brief.evidence:
            suffix = f" ({ev.link})" if ev.link else ""
            lines.append(f"- [{ev.type}] {ev.detail}{suffix}")
    else:
        lines.append("- No evidence found")

    lines.extend(["", "## Recommended Actions"])
    lines.extend([f"- {a}" for a in brief.recommended_actions])

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

