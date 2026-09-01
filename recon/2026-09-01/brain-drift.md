# brain-drift — does the documented law match what the brain enforces?

> **Agent:** `drift-auditor` · **Date:** 2026-09-01 · **Repo:** OCR-docs @ `a460614` · Wave 5
> The worker executed the pyramid itself: `python3 ocr-docs-brain/tests/run_all.py` → **10/10 levels PASS, 2.1s.**
> **Lead verification:** the two top claims re-checked. Confirmed.

## Gate Queue

**1. `nightly-sync-check.yml` computes five drift hashes and compares none of them.**
**Verified:** lines 63–78 build `CLAUDE_HASH`, `SKILL_HASH`, `ADR_HASH`, `VISION_HASH`, `DEPMAP_HASH` via `sha256sum`, under a comment reading *"Get current template hashes for drift detection."* None of the five is read again anywhere in the file. The only comparison performed (line 114) fetches `REMOTE_VISION_HASH` — a **git blob SHA**, not a content hash, not even the same algorithm — and checks only whether it is `MISSING`.

So the check is presence-only. A spoke carrying a stale-content copy of a standards file reports ✅. Combined with #2 below, **nothing anywhere detects standards divergence after propagation.** This looks precisely like a check designed correctly and left half-wired.

**2. `propagate-standards.yml` only pushes; it never audits standing divergence.**
It detects source-side change (`git diff HEAD~1 HEAD`) and target-side difference at write time (`git add -A && git diff --cached`, line 227). There is no scheduled or on-demand job that re-diffs an already-propagated spoke's `.ocr-standards/` against current source. Given private-to-private `workflow_call` has been broken since 2026-04-05 and standards therefore travel as byte-copies, this is the propagation chain's blind spot — and it bears directly on invariant #20.

**3. `brain-location-audit.yml` is non-blocking on the only trigger that matters.**
`continue-on-error: ${{ github.event_name == 'pull_request' }}` at line 147, with **no** unconditional final failing step — unlike `phantom-scan.yml`, which has exactly that at line 178 (`Fail job if phantoms were found` → `exit 1`). **Verified: `phantom-scan.yml` has the pattern, `brain-location-audit.yml` does not.** A PR adding brain-enforcement code outside its allowed home merges green; the violation surfaces up to 24h later on the 09:00 schedule, and then only via a Linear ticket that no-ops silently if `LINEAR_API_KEY` is unset. This is the non-blocking-reporting-job shape Case 1 of the case-study pack is about.

**4. The brain's flagship confidential doc overstates what exists and misnames a product.**
`ocr-docs-brain/README.md:11` states as present-tense fact that *"the org-level CI/CD pipeline (`ocr-platform-tests`) parses these files and validates every commit, every deploy, and every data write against them."* `product-registry.yaml` lists `ocr-platform-tests` with `repo_status: planned`. The same file's architecture diagram (line 65) still shows `OWL (OurWhiteList)`, renamed to `ourAirwaves`/`oaw` in `CLAUDE.md:30` and the registry. `OWL` also persists in `docs/standards/OCR_STANDARD_namingConvention.md:37` and in an enforceable description field at `ocr-docs-brain/event-taxonomy.yaml:100`. This is the document marked CONFIDENTIAL and *"it has teeth"* — the one most likely to be trusted at face value.

**5. All four fleet-status docs are 3.5+ months stale, and one cites a file that no longer exists.**
`STATUS.md` ("Week of 2026-05-15"), `OCR_STATUS_project.md` ("2026-04-09"), `CURRENT_STATE_INVENTORY.md` ("2026-05-15"), `OCR_LOG_session.md` (April runs). All predate the `recon/`, `docs/adr/` and `docs/proposals/` trees that now exist. `CURRENT_STATE_INVENTORY.md:180` cites `PROJECT-STATUS.md` as an extant near-duplicate; that file was merged away and is absent. Lowest blast radius here — these are generated snapshots, not enforcement surfaces — but they are the first thing a human reads to answer "where are we."

## Traffic lights

| Area | Light | Note |
|---|---|---|
| Brain pyramid (levels 0–9) | 🟢 | Runs, 10/10 pass; `run_all.py` gates on 0/1 and propagates any level's failure to exit code. No silent-pass shape. |
| `brain-validate.yml` | 🟢 | No `continue-on-error`, no `\|\| true`. |
| `phantom-scan.yml` | 🟢 | `continue-on-error` on the scan step, but an unconditional final fail step re-propagates. Correctly blocking. |
| `actions-selftest.yml` | 🟢 | Runs composite actions for real against a fixture. |
| `docs-ci.yml` | 🟡 | Required-files check blocks; markdown lint (`\|\| true`, :56) and link check (:72) never fail the job. |
| `brain-location-audit.yml` | 🟡 | Gate #3. |
| `nightly-sync-check.yml` | 🟡 | Gate #1. |
| `propagate-standards.yml` | 🟡 | Gate #2. |
| `scan_phantom_invariants.py` scope | 🔴 | Its only definition of "phantom" is a prose reference `invariant #N` where N is not a registry id (`:52-107`). Zero logic touching `applies_to` or `code_present`. It could not have caught the code-empty-surface defect — that is a structurally different category. |
| Register internal consistency | 🔴 | #21 and #25 — see `brain-invariants.md`. `level2_schema.py:121-127` requires `test_file` be a non-empty string and never reads its content, so `"(…planned…)"` under `status: live` passes clean. |
| Status snapshot docs | 🔴 | Gate #5. |
| Archived-path references | 🔴 | Gate #4. |
| Orphaned scripts | 🟡 | `.validate.py` and `.integration-test.py` (dot-prefixed) referenced by no workflow and not by `run_all.py`. `.validate.py`'s docstring claims coverage of "all 10 invariants"; there are 25. Dead code making a stale claim. |

## Verification (lead session)

| Claim | Result |
|---|---|
| Five hashes computed, never compared | ✅ `nightly-sync-check.yml:59-78`; only `REMOTE_VISION_HASH` at :114, a blob SHA, MISSING-check only |
| `brain-location-audit` lacks the final fail step `phantom-scan` has | ✅ confirmed in both files |
| `product-registry.yaml` carries `code_present: false` for osm/osp/osr/osg/oaw | ✅ confirmed |
| Pyramid passes 10/10 today | ✅ worker executed it; result reported |
