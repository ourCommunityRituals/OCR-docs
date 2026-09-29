# OCR_REFERENCE — CI-surface baseline (ADR-008 Phase 1 go/no-go)

Append-only. ADR-008 permits Phase 1 (moving the workers into the hub) only if all three measures below **fall** relative to the entry taken before it. Add a new dated section; never edit an old one.

## 2026-09-29 — after Phase 0 (CCR OSE-1393, measured from local checkouts)

| Measure | Value | Notes |
|---|---|---|
| Workflow files, OSE + OW + hub (the ADR's original 3-repo scope) | **38** (OSE 27, OW 6, hub 5) | The ADR's 2026-09-04 figure of 30 (OSE 19 + OW 6 + hub 5) reproduces from history. |
| Workflow files, whole fleet (10 repos) | **64** | Was 57 before 2026-09-29. Phase 0 added `design-system-check.yml` to OA, OSG, OSM, OSP, OSR, OER and OCR-docs. |
| Propagation commits, trailing 30 days (OSE + OW) | **17** (OSE 8, OW 9) | The ADR text said 12; the recount gives 17 for 2026-08-05..09-04 and for the trailing 30 days. |
| Cross-repo secret mentions (`OCR_PROPAGATE_TOKEN` occurrences in `.github/workflows/*`, comments included) | **OSE 53, OW 29, hub 5, OCR-docs 13, OA/OSG/OSM/OSP/OSR 2 each, OER 1** | Counted with `grep -o`. OW's count rose when OW-150 moved the token from one workflow-level line onto each staging step: more lines, far fewer steps that can read it. When comparing, count the steps that can read the token, not the lines. |

The Phase 0 change raised two of the three measures. That is acceptable for Phase 0, which the ADR scopes as "one gate", but it is the baseline Phase 1 must beat.
