from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class CoralError(RuntimeError):
    pass


def find_coral_bin() -> str:
    """Locate the coral binary, checking PATH then common install locations."""
    found = shutil.which("coral")
    if found:
        return found
    candidates: list[Path] = [
        Path.home() / ".local" / "bin" / "coral",
    ]
    if sys.platform == "win32":
        candidates.append(Path.home() / ".local" / "bin" / "coral.exe")
    for c in candidates:
        if c.exists():
            return str(c)
    return "coral"


def load_env_file(path: Path) -> None:
    """Load key=value pairs from a .env file into os.environ (skips already-set keys)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass
class QueryRun:
    name: str
    rows: list[dict[str, Any]]
    duration_ms: int


class CoralClient:
    def __init__(self, coral_bin: str = "coral") -> None:
        self.coral_bin = coral_bin

    @staticmethod
    def _strip_comments(sql: str) -> str:
        lines = [ln for ln in sql.splitlines() if not ln.strip().startswith("--")]
        return "\n".join(lines).strip()

    def run_sql(self, sql: str) -> tuple[list[dict[str, Any]], int]:
        sql = self._strip_comments(sql)
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

    def setup_source(self, name: str) -> tuple[bool, str]:
        """Remove then re-add `name` so fresh credentials from os.environ are always used."""
        try:
            subprocess.run(
                [self.coral_bin, "source", "remove", name],
                capture_output=True,
                text=True,
                check=False,
            )
            proc = subprocess.run(
                [self.coral_bin, "source", "add", name],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise CoralError(self._not_found_message()) from exc
        if proc.returncode == 0:
            return True, (proc.stdout.strip() or "ok")
        return False, (proc.stderr.strip() or proc.stdout.strip() or f"coral source add {name} failed")

    def list_sources(self) -> list[str]:
        """Return names of currently configured sources."""
        try:
            proc = subprocess.run(
                [self.coral_bin, "source", "list"],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise CoralError(self._not_found_message()) from exc
        lines = proc.stdout.strip().splitlines()
        names: list[str] = []
        for line in lines[1:]:  # skip header row
            parts = line.split()
            if parts:
                names.append(parts[0])
        return names

    def _not_found_message(self) -> str:
        resolved = shutil.which(self.coral_bin)
        if resolved:
            return f"Coral binary exists but was not executable: {resolved}"
        return (
            "Coral binary not found. Install Coral or pass --coral-bin with full path, "
            "for example: --coral-bin \"C:\\path\\to\\coral.exe\""
        )


def render_sql_from_template(path: Path, variables: dict[str, str]) -> str:
    sql = path.read_text(encoding="utf-8")
    for key, value in variables.items():
        sql = sql.replace(f"{{{{{key}}}}}", value)
    return sql
