-- SQL 01: Active Critical Incidents
-- Replace table/column names after discovery.

WITH active_incidents AS (
  SELECT
    i.id AS incident_id,
    i.title,
    i.urgency,
    i.status,
    i.service_id,
    i.created_at,
    i.url
  FROM pagerduty.incidents i
  WHERE i.urgency IN ('high', 'critical')
    AND i.status IN ('triggered', 'acknowledged')
)
SELECT *
FROM active_incidents
ORDER BY created_at DESC
LIMIT 25;
