# Integration Next Steps (Real Data)

## 1) Install test dependency
```bash
pip install pytest
pytest -q
```

## 2) Verify Coral sources
```bash
incident-captain health --sources pagerduty github slack datadog
```

If one source is unavailable, continue with remaining sources and note confidence downgrade.

## 3) Discover real schema
```bash
coral sql "SELECT schema_name, table_name FROM coral.tables ORDER BY 1,2"
coral sql "SELECT schema_name, table_name, column_name, data_type FROM coral.columns ORDER BY 1,2,3"
coral sql "SELECT schema_name, table_name, filter_name, required FROM coral.filters ORDER BY 1,2,3"
```

## 4) Adapt SQL templates
Update files in `deliverables/sql/`:
- replace placeholder table names (for example `github.deployments`) with actual catalog names.
- update timestamp fields to real column names.
- ensure required filters are included in every source query.

## 5) First real run
```bash
incident-captain analyze --incident-id <REAL_INCIDENT_ID>
```

Review:
- `output/<INCIDENT_ID>.json`
- `output/<INCIDENT_ID>.md`

## 6) Quality hardening
- Tune join windows (`-2h/+1h`, `-30m/+90m`) based on your incident patterns.
- Add or adjust evidence extraction heuristics in `incident_captain/briefing.py`.
- Record baseline vs assisted triage times in `deliverables/docs/metrics-plan.md`.

