from __future__ import annotations

import os
from dataclasses import dataclass


SOURCE_REQUIRED_ENV: dict[str, list[str]] = {
    "github": ["GITHUB_TOKEN"],
    "pagerduty": ["PAGERDUTY_API_TOKEN"],
    "slack": ["SLACK_TOKEN"],
    "datadog": ["DD_API_KEY", "DD_APPLICATION_KEY"],
}


@dataclass
class ConfigValidationResult:
    ok: bool
    missing: dict[str, list[str]]


def validate_source_env(sources: list[str]) -> ConfigValidationResult:
    missing: dict[str, list[str]] = {}
    for source in sources:
        needed = SOURCE_REQUIRED_ENV.get(source, [])
        source_missing = [k for k in needed if not os.getenv(k)]
        if source_missing:
            missing[source] = source_missing
    return ConfigValidationResult(ok=not missing, missing=missing)

