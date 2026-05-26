from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_batch_summary(path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    total = len(rows)
    passed = sum(1 for r in rows if r.get("status") == "passed")
    failed = total - passed
    summary = {
        "total_incidents": total,
        "passed": passed,
        "failed": failed,
        "success_rate": round((passed / total), 4) if total else 0.0,
        "runs": rows,
    }
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary

