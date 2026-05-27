from pathlib import Path
import subprocess

from incident_captain.coral import CoralClient, CoralError, render_sql_from_template


def test_render_sql_from_template(tmp_path: Path) -> None:
    sql_file = tmp_path / "x.sql"
    sql_file.write_text("select '{{INCIDENT_ID}}' as incident_id", encoding="utf-8")
    rendered = render_sql_from_template(sql_file, {"INCIDENT_ID": "INC-100"})
    assert "INC-100" in rendered


def test_coral_client_retries_timeout(monkeypatch) -> None:
    calls = {"n": 0}

    def fake_run(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] < 2:
            raise subprocess.TimeoutExpired(cmd="coral sql", timeout=0.01)
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="[]", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = CoralClient("coral", timeout_sec=0.01, retries=2, backoff_sec=0.0)
    rows, _ = client.run_sql("select 1")
    assert rows == []
    assert calls["n"] == 2


def test_coral_client_timeout_exhausted(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="coral sql", timeout=0.01)

    monkeypatch.setattr(subprocess, "run", fake_run)
    client = CoralClient("coral", timeout_sec=0.01, retries=1, backoff_sec=0.0)
    try:
        client.run_sql("select 1")
        assert False, "expected timeout CoralError"
    except CoralError as exc:
        assert exc.category == "network"

