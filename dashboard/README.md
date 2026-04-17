# OCR Deployment Truth Dashboard

Single-file Python tool that renders `dashboard.html` showing the true state of the OSE staging deployment — independent of whatever GitHub Actions is claiming.

## Why this exists

When CI is dark (billing, outage, misconfiguration), you still need to know:
1. Is staging live and responding?
2. Is it up-to-date with `origin/main`?
3. What's the real pass/fail state of each test pyramid tier?

This answers all three without needing GitHub Actions.

## Run it

```powershell
# Fast: probe endpoints + read git state + read cached test results (~5 seconds)
py C:\Users\mzdan\dev\ourCommunityRituals\OCR-docs\dashboard\dashboard.py

# Same, and open in default browser
py dashboard.py --open

# Run a specific test suite and update the cache
py dashboard.py --run-tests t0-unit
py dashboard.py --run-tests brain
py dashboard.py --run-tests t2-security-smoke

# Run everything — slow (3–10 min depending on tiers)
py dashboard.py --run-tests all
```

## What it probes

- **Live staging endpoints** (stg.oursharedevents.com) — 15 canonical routes including aliases
- **Deployment version** — parsed from `/health` (stg-<sha>-<YYYYMMDD>)
- **Git drift** — commits between deployed SHA and `origin/main`, tagged by whether they touched worker code vs CI/tests
- **Test pyramid** — T0 Gate / T2 Smoke / T3 Contract / T4 Functional + Brain test pyramid; file counts today, pass/fail after you run a suite

## Outputs

- `dashboard.html` — the dashboard (self-contained, no CDN, open in any browser)
- `.state.json` — cached test-run results keyed by suite. Regenerating the dashboard keeps the cache; only `--run-tests` updates it.

## Interpreting the colors

- 🟢 **Pass** — endpoint returned the expected status, or the suite exited 0
- 🔴 **Fail** — unexpected status, or suite exited non-zero
- ⚪ **Never run** — suite has never been executed via this tool; pass/fail shown only as file counts
- 🟡 **Drift warning** — commits since deploy include worker-code changes (staging may be behind)
