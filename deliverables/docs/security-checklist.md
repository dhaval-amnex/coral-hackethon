# Security Checklist

## Token Scope
- [ ] PagerDuty token is read-only and minimum scope.
- [ ] GitHub token is read-only and minimum repo/org scope.
- [ ] Slack token has only required read scopes.
- [ ] Datadog/OpenObserve token is read-only.

## Secret Handling
- [ ] All secrets entered through `coral source add` inputs.
- [ ] Secret values never committed to repo.
- [ ] No screenshots show terminal secret prompts.
- [ ] No logs print auth headers.

## Runtime Trust Boundaries
- [ ] MCP client is trusted for local source access.
- [ ] Custom source specs reviewed before install.
- [ ] Config directory remains local/private.

## Demo Safety
- [ ] Use sanitized incident data where needed.
- [ ] Remove customer-identifying text before recording.
- [ ] Mask channel/user data if required.
