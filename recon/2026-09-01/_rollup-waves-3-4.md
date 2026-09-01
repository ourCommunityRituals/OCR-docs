# Waves 3 + 4 rollup — the spokes have no code

> **Date:** 2026-09-01 · **Waves:** 3 (OSR, OSG, OSM) and 4 (OAW, OER, OSP)
> **Workers dispatched: none.** That is the finding, and the reasoning is below.
> **Method:** lead-session survey of all six clones. Every number here came from `git ls-files` and `diff -rq` against fresh shallow clones.

## The measurement

| Repo | HEAD | Last commit | Tracked files | Code files (`.ts`/`.tsx`/`.js`/`.py`) | Markdown | Workflows |
|---|---|---|---|---|---|---|
| ourSharedRecords | `5ed41d1` | 2026-08-29 | 31 | **0** | 27 | 2 |
| ourSharedGames | `7589075` | 2026-08-29 | 31 | **0** | 27 | 2 |
| ourSharedMagnets | `95341b9` | 2026-08-29 | 31 | **0** | 27 | 2 |
| ourAirwaves | `907a3c5` | 2026-08-29 | 31 | **0** | 27 | 2 |
| ourSharedPulse | `5438120` | 2026-08-25 | 31 | **0** | 27 | 2 |
| ourEventRings | `8a4b8cc` | 2026-04-19 | **2** | **0** | 1 | 0 |

Five of the six are the same scaffold. Their entire `.ocr-standards/` trees — 27 files — are **byte-identical** across all five (verified by `diff -rq`; only `CLAUDE.md`, `README.md`, `SKILL.md` and `brain-contract-check.yml` differ, carrying the per-repo name). ourEventRings is not even that: a `README.md` and a `.gitignore`, untouched since 2026-04-19.

## Gate Queue

**1. This is not drift. Every one of the five declares its own state accurately.**
Each CLAUDE.md says, in as many words, *"This repo is currently documentation-as-code. Application code will be added when…"* — OSR when the archive format is defined, OSG when the format is ready for OSE integration, OSM as the platform matures, OAW as the white-label model is defined, OSP because it is human-delivered with tech-optional support. `drift-auditor` exists to find the gap between what docs claim and what code does. **Here there is no gap, because there is no claim.** Recording a green is the honest output, and it is worth more than five reports saying "no code found."

**2. The register asserts enforcement on surfaces that cannot carry it.**
`applies_to` assigns 8 invariants to `osm`, 1 to `osr`, 1 to `osg`, 1 to `oureventring`, and 7 to `oaw` — 18 invariant-surface pairs across repos containing **zero lines of enforceable code between them**. Invariant #14 `mobile_workability` is scoped to `osr` and `osg`: a documentation repo has no mobile surface to be workable. Invariant #4 `ncr_data_accumulation` is scoped to `oureventring`, a repo holding a README.

Combined with Wave 1 Gate #5 — the register is blind to `schema-lexicon` and `cost-metric-never-who`, both PR-blocking in OSE — **the register is wrong in both directions at once: it undercounts enforcement where code exists and overcounts surfaces where it does not.** Any conformance percentage computed from it today is measuring a denominator that does not correspond to the estate.

**3. Standards propagate by byte-copy, and nothing detects divergence.**
`docs-ci.yml` in each spoke carries this comment: *"Inlined from OCR-docs/.github/workflows/docs-ci.yml because private-to-private `workflow_call` never resolved (0s failures since 2026-04-05)."* So the org's standards reach the spokes as copies, not as a reusable workflow. Today the copies are identical — verified. Nothing checks that they stay so. This bears directly on invariant #20 `standards_propagation_completeness` (`applies_to: [ocr]`, `status: partial`), whose own `enforces` text is about the brain not being a YAML silo. The propagation mechanism is a five-month-old workaround for a platform limitation, and it is unmonitored.

**4. ourEventRings is not a spoke; it is an empty repo with a wave assigned to it.**
Two files, dormant since 2026-04-19 — four and a half months. It was missing from the hub's sibling list entirely (fixed 2026-08-31). It should be dropped from the wave rotation until it has content, and its register entry (#4) either removed or explicitly marked aspirational.

**5. Across the whole estate, there is one application.**
Of the ten repos: ourSharedEvents is a substantial codebase; ourCommunityRituals hosts five shared packages; OCR-docs is the brain plus a `dashboard.py`. **The other seven hold no application code**, and ourWKRP is out of scope for this session by R3 and unassessed here. "Applying the fleet across all applications" therefore has a much smaller true surface than the repo count suggests — and knowing that is worth more than the six wave-rollups it replaces.

---

## Why no workers were dispatched

Kill condition 6 is *"two consecutive waves produce Gate Queues you take no action on — the fleet is generating text, not findings."* Dispatching four to six workers against each of six repos, five of them byte-identical and one nearly empty, would have produced roughly thirty reports whose common content is "this repo contains no code." That is the kill condition arriving **by construction**, before drift, and it would have consumed the review budget that Wave 1's five real findings still need.

Declining to spend the fleet where there is nothing to find is not a reduction in scope. It is the discipline the kill conditions exist to enforce, applied before the cost rather than after it. The measurement above took six clones and two commands.

**Waves 3 and 4 are closed.** Re-open a repo's wave when `git ls-files '*.ts' '*.js' '*.py'` returns non-zero. That is a one-line trigger and a better scheduler than a calendar.
