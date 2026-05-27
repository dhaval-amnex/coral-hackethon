# Release Process

Use this flow to keep submission history clean and reproducible.

## 1. Pre-release checks

Run locally:

```bash
python -m pytest -q
python -m incident_captain.cli ship-readiness --incident-id <INCIDENT_ID> --root . --output-dir output --report-dir output/report --metrics-log output/run_metrics_live_clean.jsonl --recent-runs 1 --min-progress-percent 90 --min-scorecard-overall 70
```

Confirm:
- `output/report/release_check.json` has `go_for_submission=true`
- `output/report/handoff_note.md` and `output/report/status_dashboard.md` are regenerated

## 2. Push and CI

```bash
git push origin main
```

Wait for GitHub Actions `CI` workflow to pass for all Python versions.

## 3. Create release tag

Use semantic, submission-friendly tags:
- `v0.1.0`
- `v0.1.1`

```bash
git tag -a v0.1.0 -m "submission-ready release v0.1.0"
git push origin v0.1.0
```

## 4. Final artifacts

```bash
python -m incident_captain.cli judge-pack --bundle-root output/bundles --output-zip output/judge_pack.zip
```

Submit:
- repository URL
- release tag
- `output/judge_pack.zip`

