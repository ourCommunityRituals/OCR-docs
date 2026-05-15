# OCR_SKILL_statusRollup — Spec (not yet implemented)

**Status:** SPEC — not yet built
**Date:** 2026-05-15
**Owner:** mzdan + Co-Architect
**Build trigger:** After OSE-272 Session 5 (so the skill can include SharedReport signal as a fleet output)
**Gap closed:** G1 in `CURRENT_STATE_INVENTORY.md` — "No fleet-wide 'where are we' document"

---

## Purpose

A Claude Code skill (`/status-rollup`) that **auto-regenerates** `ourCommunityRituals/STATUS.md` weekly from authoritative sources, so the fleet snapshot stops going stale.

The pain it solves: `OCR-docs/PROJECT-STATUS.md` and `OCR-docs/OCR_STATUS_project.md` are **33–36 days stale** as of 2026-05-15. Neither has a refresh ritual; both drift because they're hand-maintained. The fix is not "be more disciplined about updating them" — the fix is to make the snapshot a **derived artifact**, regenerated from primary sources.

This skill IS the regeneration mechanism. The output `STATUS.md` at workspace root becomes the single answer to "where are we right now?" and any drift is fixable by re-running the skill.

---

## Inputs (what the skill reads)

| Source | What it extracts |
|--------|------------------|
| **Linear API** (workspace "OurSharedEvents") | Stories moved this week (new, in-progress, done, cancelled); cycle progress per team |
| **Git log** across the 7 product repos + workspace root + OCR-docs | Commits this week per repo; PRs merged; PRs open |
| **ADR directories** (`<repo>/docs/adr/` + `OCR-docs/docs/adr/`) | New ADRs since last run; status changes (Proposed → Accepted, etc.) |
| **Brain contracts** (`OCR-docs/ocr-docs-brain/*.yaml`) | Diffs vs last run (new invariants, modified contracts) |
| **SharedReport** (`ourSharedEvents` D1, post-Session 5) | Active venues, total anon returns this week, corridor density baseline drift, sponsor impressions |
| **`CURRENT_STATE_INVENTORY.md`** | Open gaps (G1–G11+) and their status (closing PR or completed) |
| **`OPERATING_SYSTEM.md`** | Routing matrix — referenced for "where to look" notes in output |

---

## Output shape

A single `STATUS.md` at workspace root. Maximum 200 lines. Scannable, not encyclopedic.

```markdown
# OCR Fleet Status — Week of YYYY-MM-DD

## TL;DR
[3-bullet headline: biggest win, biggest blocker, next milestone]

## Per-product status
[Table: repo | phase | branch state | open PR count | last commit | notable this week]

## Engineering this week
[Bulleted: PRs merged, ADRs landed, Brain contracts changed]

## Discovery this week
[Bulleted: interviews logged, findings landed in <repo>/docs/discovery/, fleet themes emerging]

## Open gaps from CURRENT_STATE_INVENTORY.md
[Table: gap ID | status | owner | closing PR if any]

## SharedReport signal (OSE only, post-Session 5)
[Anon returns this week, corridor density delta, sponsor impressions delivered]

## Cadence checks
- [ ] Daily MVP review run? (link to most recent)
- [ ] Friday status rollup run? (this file)
- [ ] Monthly fleet audit due? (date)
- [ ] Per-launch ADR retros up to date? (count behind)

## Pointers
[Quick links: OPERATING_SYSTEM.md routing matrix, current ADR home, current discovery hub]
```

---

## Trigger / cadence

| Trigger | Mechanism |
|---------|-----------|
| **Manual** | `/status-rollup` invoked from any Claude Code session |
| **Friday** | Scheduled task at 09:00 Friday (per `OPERATING_SYSTEM.md §5` cadence) |
| **Per-launch** | Manual invocation immediately after a Phase-N launch milestone |

The Friday automation is the load-bearing case. Manual invocations are for ad-hoc "where are we?" checks.

---

## Implementation notes (for the build phase)

- **Skill location (final):** `OCR-docs/skills/status-rollup.skill.md` or equivalent Claude Code skill convention.
- **Auth:** Linear API token via Doppler (per `feedback_no_onedrive_paths.md` + `reference_doppler.md` doctrine — token lives in `ourcommunityrituals/dev_personal`).
- **SharedReport read:** via the OSE read API (Session 5 deliverable — `GET /api/v2/events/:id/shared-report` + the batch endpoint if WKRP-readiness ratified).
- **Git reads:** local clone or remote `gh api` — local clone is faster for the 9 surfaces.
- **Output write:** the skill writes `STATUS.md` at workspace root and stages it for commit; the operator commits and pushes (per `feedback_no_auto_prod_deploy.md`, no auto-deploy).
- **Failure isolation:** any single source failure (Linear API down, one repo unreachable) degrades the output gracefully — the skill writes a `## Status: degraded` section naming what was missing, doesn't abort.

## Why this is a sketch, not a build

The skill is most valuable when SharedReport signal is one of its inputs. That signal ships in OSE-272 Session 5. Building the skill before then would mean a Phase 1 status rollup that lacks the platform's flagship measurement layer — and once Session 5 ships, the skill would need rework. Better to wait, sketch the contract now (this doc), and build cleanly after Session 5.

In the interim, manual "where are we?" checks use:
1. `CURRENT_STATE_INVENTORY.md` for the fleet map
2. `OPERATING_SYSTEM.md §3` for the routing matrix
3. Linear directly for in-flight work
4. The daily MVP-readiness skill (`reference_mvp_review_prompt.md`) for OSE-scoped status

## Revisit / acceptance criteria

This spec is **ratified** when:

- [ ] The user reads it and confirms the inputs match what they actually want to roll up.
- [ ] The output shape matches the "scannable, not encyclopedic" target.
- [ ] The Friday cadence + manual invocation pattern matches the cadence-table in `OPERATING_SYSTEM.md §5`.

Build phase begins when OSE-272 Session 5 is on `main`. ETA pending Session 4 ratification.

---

## References

- Gap: `CURRENT_STATE_INVENTORY.md` G1
- Routing rationale: `OPERATING_SYSTEM.md §3` (workspace root)
- Cadence rule: `OPERATING_SYSTEM.md §5`
- Doctrine that constrains the skill:
  - `feedback_no_auto_prod_deploy.md` — skill stages output, operator commits
  - `feedback_self_hosted_only.md` — any CI that runs the skill uses self-hosted runners
  - `feedback_no_onedrive_paths.md` — output paths are `ourCommunityRituals/STATUS.md`, never OneDrive
  - `feedback_verify_brain.md` — skill verifies Brain contract state at run time, not from cached YAML
