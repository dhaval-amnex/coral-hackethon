-- SQL 02: Incident to Recent Deploy Correlation

WITH incident_window AS (
  SELECT
    i.id AS incident_id,
    i.title,
    i.created_at AS incident_started_at,
    i.service_id
  FROM pagerduty.incidents i
  WHERE i.id = '{{INCIDENT_ID}}'
),
recent_deploys AS (
  SELECT
    d.repo,
    d.sha,
    d.author,
    d.deployed_at,
    d.environment,
    d.url
  FROM github.deployments d
)
SELECT
  iw.incident_id,
  iw.title,
  rd.repo,
  rd.sha,
  rd.author,
  rd.deployed_at,
  rd.environment,
  rd.url AS deploy_url
FROM incident_window iw
JOIN recent_deploys rd
  ON rd.deployed_at BETWEEN iw.incident_started_at - INTERVAL '2 hours'
                        AND iw.incident_started_at + INTERVAL '1 hour'
ORDER BY rd.deployed_at DESC;
