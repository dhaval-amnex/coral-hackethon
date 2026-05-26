-- SQL 05: Final Incident Brief Dataset

WITH incident AS (
  SELECT
    i.id AS incident_id,
    i.title,
    i.urgency,
    i.status,
    i.created_at,
    i.service_id,
    i.url AS incident_url
  FROM pagerduty.incidents i
  WHERE i.id = '{{INCIDENT_ID}}'
),
deploys AS (
  SELECT
    d.repo,
    d.sha,
    d.author,
    d.deployed_at,
    d.url AS deploy_url
  FROM github.deployments d
),
metrics AS (
  SELECT
    m.service,
    m.metric_name,
    m.value,
    m.timestamp
  FROM datadog.metrics m
),
comms AS (
  SELECT
    s.channel_name,
    s.user_name,
    s.ts,
    s.text
  FROM slack.messages s
)
SELECT
  i.incident_id,
  i.title,
  i.urgency,
  i.status,
  i.created_at,
  d.repo,
  d.sha,
  d.author,
  d.deployed_at,
  m.metric_name,
  m.value,
  m.timestamp AS metric_ts,
  c.channel_name,
  c.user_name,
  c.ts AS comms_ts,
  c.text,
  i.incident_url,
  d.deploy_url
FROM incident i
LEFT JOIN deploys d
  ON d.deployed_at BETWEEN i.created_at - INTERVAL '2 hours' AND i.created_at + INTERVAL '1 hour'
LEFT JOIN metrics m
  ON m.timestamp BETWEEN i.created_at - INTERVAL '30 minutes' AND i.created_at + INTERVAL '90 minutes'
LEFT JOIN comms c
  ON c.ts BETWEEN i.created_at - INTERVAL '15 minutes' AND i.created_at + INTERVAL '120 minutes'
ORDER BY d.deployed_at DESC, m.timestamp ASC, c.ts ASC;
