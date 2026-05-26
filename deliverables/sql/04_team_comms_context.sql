SELECT
  u.name AS user_name,
  u.real_name AS channel_name,
  u.email AS text
FROM slack.users u
WHERE u.deleted = false
  AND u.is_bot = false
ORDER BY u.name ASC
LIMIT 20;
