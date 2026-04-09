You are running a system-wide QA reconciliation check for the ourSharedEvents project. This is not a code review — it is a drift detection scan across four layers: infrastructure, code, stories, and documentation. Your goal is to find mismatches between what the stories say, what the code does, what the infrastructure has provisioned, and what the docs claim.



## Repository Location

The ourSharedEvents repo is in the user's selected workspace folder. Look for it at the path containing `OneDrive/Documents/GitHub/ourSharedEvents`. If not found, report that the repo is not accessible.



## Layer 1: Story ↔ Code Drift

- Read `STORIES.md` at the repo root. For each story marked "Done" or "In Progress", verify the claimed files/features actually exist in the codebase.

- Check `.claude/sync/LINEAR-MAP.md` for any story IDs with empty Linear IDs ("—").

- Flag: stories marked Done whose acceptance criteria are not met in code.

- Flag: code that exists (migrations, handlers, configs) with no corresponding story or a story still in Backlog.



## Layer 2: Infrastructure ↔ Code Drift

- Read `workers/oursharedevents/wrangler.toml`. Check:

  - Are D1 database bindings using real IDs or placeholders like `<staging-db-id>`?

  - Are secrets listed in the `[vars]` section that don't match what Doppler or GitHub Actions should provide?

  - Do environment names in wrangler.toml match the Doppler environments (dev/stg/prd)?

- Read `workers/oursharedevents/src/handlers/health.ts`. What does the health check validate? Flag if it only checks one data source but the worker uses multiple (e.g., checks Sheets but forms use D1).

- Check if `workers/oursharedevents/src/handlers/events.ts` uses Sheets or D1. Compare against what the Phase plan in STORIES.md says the current data source should be.



## Layer 3: Documentation ↔ Reality Drift

- Read `docs/ARCHITECTURE.md`, `DEPLOYMENT.md`, `RUNBOOK.md`, and `CLAUDE.md`.

- Flag any claims about infrastructure being provisioned that contradict Layer 2 findings (e.g., docs say "D1 is provisioned" but wrangler.toml has placeholder IDs).

- Flag any documented secrets lists that don't match the actual secrets inventory in wrangler.toml.

- Check `docs/VERIFIED-FACT-BASE.md` — flag any facts that are now stale based on your findings.



## Layer 4: Test Coverage Drift

- Count test files in `workers/oursharedevents/tests/` (canonical) vs `worker/tests/` or `tests/` (legacy).

- Flag if more than 50% of test files target the legacy worker directory.

- Check `.github/workflows/oursharedevents-ci.yml` — does the CI pipeline test the canonical worker or the legacy one?



## Output Format

Produce a markdown report with these sections:



```markdown

## System Sync Status — [DATE]



### Summary

- Total drift items found: X

- Critical (blocks deployment): X

- Warning (should fix soon): X  

- Info (awareness only): X



### Critical Drift

[List each item with: what drifted, where it was found, what the correct state should be]



### Warnings

[List each item]



### Info

[List each item]



### Recommended Actions

[Numbered list of specific actions to resolve critical and warning items, with Linear story IDs where applicable]

```



Save the report to the repo at `.claude/outputs/[DATE]-system-sync-status.md` where DATE is today's date in YYYY-MM-DD format.



## Important Notes

- Do NOT make any code changes. This is a read-only audit.

- Do NOT create or modify Linear issues. Only reference existing issue IDs.

- Be specific — cite file paths and line numbers when flagging drift.

- Compare what IS versus what SHOULD BE. The "should be" comes from STORIES.md phase plan and the documented architecture.