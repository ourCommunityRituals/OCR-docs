# OCR — Multi-App Dashboard (v2)

Single-file Python tool that renders an **index page listing every app** in the
OurCommunityRituals portfolio, plus a detail page per app and a **Story-Flow
lane view** showing how the Brain's Linear stories fan out to downstream apps
in CI/CD.

## Why this exists

- Brain (OCR-docs) is the orchestrator. When it kicks a Linear story, CI work
  first occurs on the Brain, then propagates to QA in each affected repo.
- Portfolio visibility: one place to see every app's verification surface
  (live probes, test pyramid, drift vs. origin/main) without bouncing between
  GitHub Actions, Linear, and each repo.
- CI-dark resilience: the dashboard reads live endpoints + git state + its own
  test cache — it doesn't need GitHub Actions to be green (or even reachable).

## Files produced

| File | Purpose |
|---|---|
| `index.html` | Roster of all apps + overview donuts + trend chart + Story Flow lanes |
| `app-<key>.html` | Per-app detail: live probes, test pyramid, drift, copy-able commands |
| `dashboard.html` | Back-compat redirect to `index.html` |
| `.state.json` | Last-run cache keyed by suite key |
| `.history.json` | Append-only snapshot log — every `--run-tests` appends a row so day/week/month trends populate over time |
| `.stories.json` | **You provide this** (or wire Linear API). Lane-view feed. See `.stories.json.example` |

## Apps (roster order)

Brain first (validates cross-app sync), then downstream apps:

| Key | Role | Repo | Live? |
|---|---|---|---|
| `ocr-brain` | Orchestrator | `OCR-docs` | no HTTP surface |
| `ose-staging` | Downstream | `ourSharedEvents` | `stg.oursharedevents.com` |
| `ose-prod` | Downstream | `ourSharedEvents` | `oursharedevents.com` |
| `wkrp` | Downstream | `ourWKRP` | reserved (stg.ourwkrp.com) — not deployed |
| `osg` | Stub | `ourSharedGames` | no deployment yet |
| `osm` | Stub | `ourSharedMagnets` | no deployment yet |
| `osp` | Stub | `ourSharedPulse` | no deployment yet |
| `osr` | Stub | `ourSharedRecords` | no deployment yet |
| `oa` | Stub | `ourAirwaves` (renamed from `ourWhiteList` 2026-04-17) | no deployment yet |

The **Story-Flow lane view** dedupes `ose-staging` + `ose-prod` into one `ose`
column — so it has 8 lane columns (one per app), matching the logical
orchestration topology.

## Story Flow — lane view

One row per in-flight Linear story, one column per app. Each cell is a
status dot:

| Dot | Meaning |
|---|---|
| 🟢 | Pass — CI green in that repo |
| 🔴 | Fail — CI red |
| 🔵 | Running — workflow in progress |
| 🟣 | Pending — queued, waiting on dependency |
| 🟡 | Skipped |
| ⚫ | Not affected |

Stories with multiple apps are unified by an `umbrella` label (so issues in
different backlogs with different numbers roll up to one row).

### Data source

Today: hand-maintained `.stories.json`. See `.stories.json.example` for the
schema. Copy that to `.stories.json` and re-run to see lanes populate.

Planned (not yet wired): Linear API + GitHub Actions workflow-run feed. The
`source` field at the top of `.stories.json` declares which feeder produced
the file.

## Run it

```powershell
# Fast: probe every app + read git + read cached tests (~10-20s)
py C:\Users\mzdan\dev\ourCommunityRituals\OCR-docs\dashboard\dashboard.py

# ...and open index.html
py dashboard.py --open

# Regenerate only one app's detail page
py dashboard.py --app ocr-brain

# Run a specific suite and update state + history cache
py dashboard.py --run-tests brain
py dashboard.py --run-tests t0-unit
py dashboard.py --run-tests t2-security-smoke

# Run everything (slow — 3–10 minutes)
py dashboard.py --run-tests all
```

## UX affordances in the detail view

- Every URL is clickable (endpoint paths, aliases, redirect targets, commit
  SHAs, compare links).
- Cloudflare Access redirects are collapsed to `CF Access login →` — full URL
  available on hover.
- Sticky top nav with `1`–`n` keyboard shortcuts to jump between sections.
- Filter box + "Only failing" toggle on each table.
- Copy-to-clipboard button on every command.
- Freshness indicator ticks every second since last probe.

## What's next (anticipated architecture)

Once `.stories.json` is fed by Linear + GitHub Actions, the lane view becomes
a live operational picture: you'll see the Brain light up green first, then
each downstream QA column turn blue-then-green (or blue-then-red) as CI
completes per repo — all simultaneously for multi-app stories.

---

## Paths, and why they are derived (2026-09-01)

`BRAIN_REPO` was previously the absolute constant
`C:/Users/mzdan/dev/ourCommunityRituals/OCR-docs`, with `OSE_REPO` and
`SIBLING_DIR` alongside it. That made the tool produce output on exactly one
checkout. Everywhere else `Path("C:/...")` is a **relative** path, so the script
logged `Wrote ...` for all eleven pages while creating a directory literally
named `C:` and writing nothing where it belonged — a silent false success, and
the reason no CI job could ever run it.

Paths now derive from the file's own location:

| Constant | Derivation | Override |
|---|---|---|
| `BRAIN_REPO` | `dashboard/dashboard.py` → repo root | `OCR_BRAIN_REPO` |
| `SIBLING_ROOT` | `BRAIN_REPO.parent` | `OCR_SIBLING_DIR` |
| `OSE_REPO` | `SIBLING_ROOT / "ourSharedEvents"` | — |

`canon_path()` still handles `Our` vs `our` casing. A checkout with a different
layout sets the two env vars rather than editing source.

## What is committed, and what is not

| File | Tracked | Why |
|---|---|---|
| `dashboard.py`, `README.md`, `.stories.json.example` | ✅ | the generator and its docs |
| `index.html`, `app-*.html`, `dashboard.html` | ❌ | derived — regenerable exactly from the generator |
| `.state.json` | ❌ | last-run cache, per-machine |
| **`.history.json`** | **✅** | **append-only trend log — irreplaceable** |
| `.stories.json` | ❌ | local feed, may carry unshipped Linear content |

`.history.json` is the one output that cannot be regenerated: every `--run-tests`
appends a row, and the day/week/month trend charts are built from the series. It
was previously ignored, which meant the history lived only on whichever machine
ran last and died on a fresh clone — the trend data most worth keeping was the
one thing guaranteed not to be kept.

## Scheduled regeneration

`.github/workflows/dashboard.yml` regenerates the dashboard daily and uploads it
as a run artifact. The repo is private, so a run artifact — not GitHub Pages —
is the appropriate surface: no publishing of infra state, no Pages entitlement
needed on a private org repo. Download it from the workflow run.
