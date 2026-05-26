-- SQL 03: Error and Latency Spike Context

WITH window AS (
  SELECT
    i.id AS incident_id,
    i.created_at AS t0
  FROM pagerduty.incidents i
  WHERE i.id = '{{INCIDENT_ID}}'
)
SELECT
  m.service,
  m.metric_name,
  m.value,
  m.timestamp,
  m.tags
FROM datadog.metrics m
CROSS JOIN window w
WHERE m.timestamp BETWEEN w.t0 - INTERVAL '30 minutes' AND w.t0 + INTERVAL '90 minutes'
  AND m.metric_name IN ('error_rate', 'p95_latency')
ORDER BY m.timestamp ASC;
