from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import IncidentBrief


def append_run_metrics(
    path: Path,
    *,
    incident_id: str,
    mode: str,
    total_duration_ms: int,
    brief: IncidentBrief,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "incident_id": incident_id,
        "mode": mode,
        "total_duration_ms": total_duration_ms,
        "confidence": brief.confidence,
        "evidence_count": len(brief.evidence),
        "impacted_services_count": len(brief.impacted_services),
        "owners_count": len(brief.owners),
        "query_errors": len(brief.diagnostics.get("errors", [])),
        "query_stats": brief.diagnostics.get("queries", {}),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")

