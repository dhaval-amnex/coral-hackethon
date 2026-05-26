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

## Run analysis
```bash
incident-captain analyze --incident-id INC-1234
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

