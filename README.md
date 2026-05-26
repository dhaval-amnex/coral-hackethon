# Incident Captain

Incident Captain is a Track 1 Enterprise Agent project built on Coral. It correlates incidents across PagerDuty, GitHub, telemetry, and Slack to produce a structured root-cause briefing.

## What this includes
- End-to-end execution plan in `plan/`
- Submission assets and templates in `deliverables/`
- Runnable CLI in `incident_captain/`
- SQL workflow templates in `deliverables/sql/`
- Tests in `tests/`

## Prerequisites
- Python 3.10+
- Coral installed and available on PATH
- Configured Coral sources (recommended):
  - `pagerduty`
  - `github`
  - `slack`
  - `datadog` (or `openobserve` by adapting SQL template names)

## Setup
```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e .
pip install pytest
```

## Validate sources
```bash
incident-captain health --sources pagerduty github slack datadog
```

If your machine cannot run Coral source commands, use offline mock mode:
```bash
python -m incident_captain.cli health --mock-data-dir deliverables/mock
```

## Run analysis
```bash
incident-captain analyze --incident-id INC-1234
```

Offline mock run:
```bash
python -m incident_captain.cli analyze --incident-id INC-1001 --mock-data-dir deliverables/mock
```

Executive-view console output for demos:
```bash
python -m incident_captain.cli analyze --incident-id INC-1001 --mock-data-dir deliverables/mock --view executive
```

Capture run metrics:
```bash
python -m incident_captain.cli analyze --incident-id INC-1001 --mock-data-dir deliverables/mock --metrics-log output/run_metrics.jsonl
```

Capture deterministic workflow trace:
```bash
python -m incident_captain.cli analyze --incident-id INC-1001 --mock-data-dir deliverables/mock --workflow-log output/workflow_log.json
```

Catalog snapshot (when Coral access is available):
```bash
python -m incident_captain.cli snapshot-catalog --output-dir output/catalog
```

Generate demo report from run metrics:
```bash
python -m incident_captain.cli demo-report --metrics-log output/run_metrics.jsonl --output-dir output/report
```

Create final submission bundle:
```bash
python -m incident_captain.cli submission-bundle --incident-id INC-1001 --output-dir output --report-dir output/report --bundle-root output/bundles
```

Outputs:
- `output/INC-1234.json`
- `output/INC-1234.md`

## Test
```bash
pytest -q
```

## Next integration step
Replace placeholder table/column names in `deliverables/sql/*.sql` with your live Coral catalog names from:
```bash
coral sql "SELECT schema_name, table_name FROM coral.tables ORDER BY 1,2"
coral sql "SELECT schema_name, table_name, column_name FROM coral.columns ORDER BY 1,2,3"
```
