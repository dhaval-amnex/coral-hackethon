SELECT
  d.repo,
  d.sha,
  d.creator__login AS author,
  d.created_at AS deployed_at,
  d.environment,
  d.url AS deploy_url
FROM github.repo_deployments d
WHERE d.owner = '{{GITHUB_OWNER}}'
  AND d.repo = '{{GITHUB_REPO}}'
ORDER BY d.created_at DESC
LIMIT 10;
