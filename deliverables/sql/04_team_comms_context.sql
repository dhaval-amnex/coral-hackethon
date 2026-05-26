-- SQL 04: Team Communication Context

WITH window AS (
  SELECT
    i.id AS incident_id,
    i.created_at AS t0,
    i.title
  FROM pagerduty.incidents i
  WHERE i.id = '{{INCIDENT_ID}}'
)
SELECT
  s.channel_name,
  s.user_name,
  s.ts,
  s.text,
  s.thread_ts
FROM slack.messages s
CROSS JOIN window w
WHERE s.ts BETWEEN w.t0 - INTERVAL '15 minutes' AND w.t0 + INTERVAL '120 minutes'
  AND (
    LOWER(s.text) LIKE CONCAT('%', LOWER(w.title), '%')
    OR LOWER(s.text) LIKE '%incident%'
    OR LOWER(s.text) LIKE '%outage%'
  )
ORDER BY s.ts ASC
LIMIT 300;
