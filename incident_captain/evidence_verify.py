from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _read_json_file(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def verify_evidence(
    *,
    tables_file: Path,
    columns_file: Path,
    filters_file: Path,
    live_metrics_file: Path,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    for key, path in [
        ("tables", tables_file),
        ("columns", columns_file),
        ("filters", filters_file),
    ]:
        payload = _read_json_file(path)
        valid = isinstance(payload, list) and len(payload) > 0
        checks.append(
            {
                "check": f"{key}_json_non_empty_list",
                "passed": valid,
                "detail": str(path),
            }
        )

    live_rows = 0
    metrics_exists = live_metrics_file.exists()
    if metrics_exists:
        for line in live_metrics_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(row.get("mode", "")).lower() == "live":
                live_rows += 1

    checks.append(
        {
            "check": "live_metrics_has_live_rows",
            "passed": live_rows > 0,
            "detail": {"file": str(live_metrics_file), "live_rows": live_rows, "exists": metrics_exists},
        }
    )

    passed = all(c["passed"] for c in checks)
    return {"passed": passed, "checks": checks}

