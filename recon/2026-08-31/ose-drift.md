# ose-drift — ourSharedEvents drift audit

> **Wave:** 1 (calibration) · **Agent:** `drift-auditor` · **Date:** 2026-08-31
> **Repo:** ourSharedEvents @ `14f5c3b` · **Baseline:** `.claude/documents/RECONCILIATION.md` (2026-03-27, updated 2026-04-09)
> **Lead verification:** all five Gate Queue items independently re-checked before this artifact was written. Results in §Verification.

## Gate Queue

| # | Finding | Evidence | Verified |
|---|---|---|---|
| 1 | Security-baseline docs name a deleted file as the production trust boundary | `docs/security/SECURITY_BASELINE-ROOT.md:52-53` maps `oursharedevents-prod` and `-staging` to `worker/src/router.ts`; `worker/` does not exist (deleted `0ebbb4b`, 2026-04-05). Real router is `workers/oursharedevents/src/router.ts` (1,555 lines). | ✅ |
| 2 | CLAUDE.md documents a **closed** tenant-isolation hole as open | `CLAUDE.md:139` and `:175` both call object-level brand scoping "a known gap tracked in OSE-1080". OSE-1080 shipped 2026-08-29: `workers/oursharedevents/src/lib/admin-object-scope.ts` (8,393 B) exists and is wired at router dispatch. | ✅ |
| 3 | The doc-sync loop CLAUDE.md mandates has stalled across the last 6 merged PRs, including HEAD | OSE-1080, -1081, -868, -982, -1135, -1138 each return **zero** hits in `STORIES.md`. CLAUDE.md §5 steps 8/10 require a STORIES.md update per merge. HEAD's own commit is unrecorded. | ✅ |
| 4 | `TEST-MANIFEST.md` documents a test framework that is not in the repo | Lists Jest as one of 5 active frameworks with a `jest.config.js`. No `jest.config*` exists; `grep '"jest"' package.json` → 0. `package.json:20` `test:schemas:jest` runs `vitest run`. | ✅ |
| 5 | `docs/INDEX.md` — the map the audit was told to trust — is itself stale | Lists `docs/env/` as a live 4-file section; the directory does not exist. Documents ~11 files under `docs/features/`; actual count is **21**. Smaller undercounts in `qa/` and `deployment/`. | ✅ |

**Throughline:** code moves, docs don't — and the DAC protocol meant to catch that at every merge is itself the thing currently drifting (#3). #1 and #2 are the dangerous pair: one points a security reviewer at a file that no longer exists, the other tells them a live vulnerability is open when it was closed two days before HEAD.

---

## Delta from the 2026-03-27 / 04-09 baseline

| Area | Mar 27 | Apr 9 | Now (Aug 31) | Evidence |
|---|---|---|---|---|
| Dual Worker | 🔴 Gap | 🟡 Resolved in practice | 🟢 structurally resolved / 🔴 **docs never caught up** | `worker/` deleted `0ebbb4b`; ~11 live docs still cite the tree (Gate #1) |
| D1 schema | 🟡 Ahead of docs | 🟢 Aligned | 🟢 Aligned | 68 main + 13 forms migrations on disk, matches CLAUDE.md exactly |
| CI/CD stage1/stage2 | 🟡 Mixed | 🟢 Aligned | 🟢 Resolved | moved to `.github/workflow-archive/` |
| Postman/Newman | 🟡 Stale | 🟢 Aligned | 🟢 Resolved, improved | `newman.config.json` documents the OSE-838 GAS retirement to avoid false-green; new collections wired into CI T2 |
| Test-suite docs | 🟢 Strong | 🟢 Strong | 🟡 Drift | Gate #4 |
| Security docs / trust boundary | — | — | 🔴 **New gap** | Gate #1 |
| Object-level brand scoping | — | — | 🟡 Docs behind code | Gate #2 |
| CLAUDE.md ↔ STORIES.md sync | (was the drift) | 🟡 13-day gap | 🔴 **Recurring, current** | Gate #3 |
| `docs/INDEX.md` accuracy | — | — | 🟡 Drift | Gate #5 |
| Ecosystem products | 🔴 Docs only | 🔴 Docs only | ⛔ **Boundary** | CLAUDE.md §2 now lists live repo paths for OW/OSG/OSR/OSP/OSM/OA. Verifying requires reading those repos — out of scope per R3. Flagged, not assessed. |

**Every March/April headline finding is now resolved or resolved-with-a-doc-lag.** All five current Gate items are net-new: either impossible to see in March (OSE-1080's fix; HEAD's own commit missing from STORIES.md) or a compounded form of a problem the baseline underestimated.

---

## Verification (lead session)

Case 3 of the CCR case-study pack — a scout agent citing confident, fabricated paths — is the reason this section exists. Every Gate item was re-checked directly against the working tree before this artifact was written. All five confirmed.

One claim was **overstated and is corrected here**: the report said 9 further docs "repeat the same stale path." The exact string `worker/src/router.ts` appears on 6 lines across 3 files (`SECURITY_BASELINE-ROOT.md`, `ROUTE_CLASSIFICATION_POLICY.md`, `RUNBOOK-SEC-4.2-SINGLE-WORKER-ROUTE.md`). The other 8 files cite *different* paths inside the same deleted `worker/` tree (1–7 refs each; `LOGGING_STANDARD.md` has 7). The substance holds — ~11 live docs point into a directory deleted five months ago — but it is the deleted **tree**, not one repeated path. Recorded because the distinction changes the fix: a single find-and-replace does not close it.

## Appendix — below the fold, not gate-worthy

- Root clutter (`fix-test-infrastructure.sh`, `fix_alert.sh`, `fix_include.patch`, `fix_test_infrastructure.py`, `test-deployment.js`) dates to the 2026-03-24 initial commit. Pre-existing, never flagged.
- `route-backups/` (OSE-162, 2026-04-11) holds only `.gitignore` and `README.md`. Vestigial, low stakes.
- `.ocr-standards/` is new since March; likely an OCR-docs sync artifact, not assessed in depth.
- CLAUDE.md §7 claims "237 test files across 6 frameworks"; a raw `.spec.ts`/`.test.ts` count returns 362. Worth a recount; not verified framework-by-framework, so not promoted.

## Calibration verdict

**The prompt produced signal.** It did not rediscover the dual-Worker problem — it established that the problem was fixed five months ago and that the *documentation* of it is now the live risk. That is the inversion Wave 1 was run to detect. `drift-auditor` is cleared to spend on Waves 2–6 as written.
