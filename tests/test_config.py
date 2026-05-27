import os

from incident_captain.config import validate_source_env


def test_validate_source_env_missing(monkeypatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("SLACK_TOKEN", raising=False)
    result = validate_source_env(["github", "slack"])
    assert result.ok is False
    assert "github" in result.missing
    assert "GITHUB_TOKEN" in result.missing["github"]
    assert "slack" in result.missing
    assert "SLACK_TOKEN" in result.missing["slack"]


def test_validate_source_env_ok(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.setenv("SLACK_TOKEN", "x")
    result = validate_source_env(["github", "slack"])
    assert result.ok is True
    assert result.missing == {}

