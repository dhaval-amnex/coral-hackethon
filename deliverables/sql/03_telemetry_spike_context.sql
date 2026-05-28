-- SQL 03: Alerting Monitor Context (Datadog)
-- Coral's Datadog connector exposes monitors and incidents; no raw metrics table exists.
-- Alerting monitors (Alert/Warn/No Data) serve as the telemetry proxy.

SELECT
  m.name AS metric_name,
  m.status AS value,
  m.tags,
  m.type AS service,
  m.modified AS timestamp
FROM datadog.monitors m
WHERE m.status IN ('Alert', 'Warn', 'No Data')
  AND m.modified >= now() - interval '{{WINDOW_HOURS}} hour'
ORDER BY m.modified DESC
LIMIT 30;
