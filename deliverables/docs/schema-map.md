# Schema Map Template

Fill this after running Coral discovery queries.

## Source Inventory
| Source | Installed | Tested | Notes |
|---|---|---|---|
| pagerduty |  |  |  |
| github |  |  |  |
| slack |  |  |  |
| datadog/openobserve |  |  |  |
| statusgator (optional) |  |  |  |

## Canonical Keys
| Canonical Key | Source Field(s) | Normalization Rule | Confidence |
|---|---|---|---|
| service_key |  |  |  |
| repo_key |  |  |  |
| incident_id |  |  |  |
| owner_key |  |  |  |

## Required Filters by Table
| Schema.Table | Required Filters | Example Values |
|---|---|---|
|  |  |  |

## Query Windows
- Default lookback: last 6 hours
- Extended lookback: last 24 hours
- Deployment window around incident: -2h to +1h

## Known Gaps
- Missing fields:
- Workarounds:
- Fallback joins:
