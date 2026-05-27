# Incident Captain

Incident Captain is a Track 1 Enterprise Agent project built on Coral. It correlates incidents across PagerDuty, GitHub, telemetry, and Slack to produce a structured root-cause briefing.

## Setup
```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e .
pip install pytest
```

## Configure
```bash
python -m incident_captain.cli setup-sources --env-file .env
python -m incident_captain.cli health --env-file .env
```

## Run
```bash
python -m incident_captain.cli analyze --incident-id <INCIDENT_ID> --env-file .env --github-owner <OWNER> --github-repo <REPO>
python -m incident_captain.cli demo-run --incident-id <INCIDENT_ID> --env-file .env --output-dir output --report-dir output/report --bundle-root output/bundles --metrics-log output/run_metrics.jsonl --workflow-log output/workflow_log.json --baseline-file output/baseline_times.json --github-owner <OWNER> --github-repo <REPO>
```

Optional reliability flags for constrained networks:
```bash
--coral-timeout-sec 45 --coral-retries 3 --coral-backoff-sec 1.0
```

## Release Artifacts
```bash
python -m incident_captain.cli scorecard --report-dir output/report --quality-gate-file output/report/quality_gate.json --output-dir output/report
python -m incident_captain.cli release-check --root . --output-dir output/report --min-progress-percent 90 --min-scorecard-overall 70
python -m incident_captain.cli judge-pack --bundle-root output/bundles --output-zip output/judge_pack.zip
python -m incident_captain.cli ship-readiness --incident-id <INCIDENT_ID> --root . --output-dir output --report-dir output/report --metrics-log output/run_metrics.jsonl --recent-runs 1 --min-progress-percent 90 --min-scorecard-overall 70
```

## Evidence Import Flow
```bash
python -m incident_captain.cli evidence-verify --tables-file <PATH_TABLES_JSON> --columns-file <PATH_COLUMNS_JSON> --filters-file <PATH_FILTERS_JSON> --live-metrics-file <PATH_RUN_METRICS_JSONL> --output-file output/report/evidence_verify.json
python -m incident_captain.cli import-live-evidence --tables-file <PATH_TABLES_JSON> --columns-file <PATH_COLUMNS_JSON> --filters-file <PATH_FILTERS_JSON> --live-metrics-file <PATH_RUN_METRICS_JSONL> --output-root output
python -m incident_captain.cli close-live-loop --incident-id <INCIDENT_ID> --tables-file <PATH_TABLES_JSON> --columns-file <PATH_COLUMNS_JSON> --filters-file <PATH_FILTERS_JSON> --live-metrics-file <PATH_RUN_METRICS_JSONL> --output-root output --report-dir output/report --bundle-root output/bundles --workflow-log output/workflow_log.json --baseline-file output/baseline_times.json
```

## Tests
```bash
python -m pytest -q
```
