SELECT
  i.id AS incident_id,
  i.title,
  i.urgency,
  i.status,
  i.service__id AS service_id,
  i.service__name AS service,
  i.created_at,
  i.html_url AS incident_url
FROM pagerduty.incidents i
ORDER BY i.created_at DESC
LIMIT 25;
