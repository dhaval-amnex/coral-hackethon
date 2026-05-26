from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class CoralError(RuntimeError):
    pass


@dataclass
class QueryRun:
    name: str
    rows: list[dict[str, Any]]
    duration_ms: int


class CoralClient:
    def __init__(self, coral_bin: str = "coral") -> None:
        self.coral_bin = coral_bin

    def run_sql(self, sql: str) -> tuple[list[dict[str, Any]], int]:
        started = time.perf_counter()
        try:
            proc = subprocess.run(
                [self.coral_bin, "sql", "--format", "json", sql],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise CoralError(self._not_found_message()) from exc
        duration_ms = int((time.perf_counter() - started) * 1000)
        if proc.returncode != 0:
            raise CoralError(proc.stderr.strip() or proc.stdout.strip() or "coral sql failed")
        stdout = proc.stdout.strip()
        if not stdout:
            return [], duration_ms
        try:
            return json.loads(stdout), duration_ms
        except json.JSONDecodeError as exc:
            raise CoralError(f"invalid JSON from coral sql: {exc}") from exc

    def source_health(self, sources: list[str]) -> dict[str, str]:
        result: dict[str, str] = {}
        for src in sources:
            try:
                proc = subprocess.run(
                    [self.coral_bin, "source", "test", src],
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except FileNotFoundError as exc:
                raise CoralError(self._not_found_message()) from exc
            result[src] = "ok" if proc.returncode == 0 else "failed"
        return result

    def _not_found_message(self) -> str:
        resolved = shutil.which(self.coral_bin)
        if resolved:
            return f"Coral binary exists but was not executable: {resolved}"
        return (
            "Coral binary not found. Install Coral or pass --coral-bin with full path, "
            "for example: --coral-bin \"C:\\path\\to\\coral.exe\""
        )


def render_sql_from_template(path: Path, incident_id: str) -> str:
    sql = path.read_text(encoding="utf-8")
    return sql.replace("{{INCIDENT_ID}}", incident_id)
