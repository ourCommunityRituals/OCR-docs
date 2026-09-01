# brain-invariants — the register checked against the repo that hosts it

> **Agent:** `invariant-sweeper` · **Date:** 2026-09-01 · **Repo:** OCR-docs @ `a460614`
> **Lead verification:** both top claims re-checked directly. Confirmed.

## Gate Queue

**1. The register asserts LIVE invariants on repos its own checker deliberately skips.**
`check_brain_contract.py:405` short-circuits on `product.get('code_present') is False` — prints `[SKIP]`, emits a single PASS, exits 0, before any check runs. **Verified.** The skip is honest and documented ("stub repo, no application code to validate. Flip the flag when code lands").

The defect is not the skip. It is that `applies_to` binds **status: live** invariants to those same repos: `osm` carries five live (#1 `anonymous_id`, #3 `uec_encoding`, #10, #11, #12); `oaw` carries four (#10, #11, #12, #22 `cross_repo_import_isolation`). The register's own status enum defines `live` as *"currently enforced in CI."* So the brain simultaneously claims these contracts are enforced in those repos and instructs its checker not to look. Fix the `status`/`applies_to` pairing, or the flag — not the escape hatch.

`oureventring` is worse-formed still: invariant #4 (`ncr_data_accumulation`, live) names it in `applies_to`, but it is a top-level warehouse key in `product-registry.yaml`, not an entry in the `products:` array. `find_product()` would return `None` and `sys.exit(2)` if ever invoked against it.

**2. Two parallel invariant systems exist, and neither cites the other.**
`docs/CHOICE-INVARIANTS.md` defines a complete second rule set — Anonymous A-1..A-8, Identity I-1..I-8, Bridge B-1..B-7, Universal U-1..U-7 — with real enforcement code shipped as composite actions (`identity-contract/identity_contract_check.py`, `universal-checks/universal_checks.py`). Neither document names the other's rule IDs anywhere.

Where they overlap, the CHOICE side is the weaker: **verified** at `identity_contract_check.py:304-306`, B-3 ("no query may join an anonymous scan to a named person") is `WARN`, and **B-4 — "SharedReport shows the total only, never the split" — is `INFO`**, a hardcoded label, never actually scanned. A-1 ("no PII in the main event database") is `WARN`. B-4 is the "never who, always how many" doctrine stated almost verbatim, and it is the least-enforced rule in the system.

In fairness: the checker's header is honest about this, reserving `FAIL` for unambiguous cross-coupling "so the gate never flakes." It is a disclosed design choice, not a hidden failure. But the doctrine's most central clause is currently unchecked, and no numbered invariant covers it either.

**3. The banned-term lexicon does not exist in the register at all.**
Ids run 1–25 with no gaps. The lexicon lives only as an unmerged draft — `docs/proposals/PROPOSAL_invariants-26-27-mutual-acceptance-honesty-lexicon.md` stages #26 and #27, the latter pointing at OSE's `schema-lexicon.spec.ts` (live there since OSE-801). The proposal's own preamble notes that OSE migrations already cite "#25" for this doctrine — **a citation of law that does not exist in the committed registry.** This is the mirror of the Wave 1 finding: OSE enforces it, the brain has not registered it, and code in OSE already cites a number for it.

**4. #25 tells three different stories about its own status, on the same entry.**
`status: live`; `test_file` annotated *"(OSE repo — planned, OSE-663 / OSE-662)"*; `references.activation_criterion` reads forward-looking (*"Promote to partial at floor+cap coverage; live at full adversarial set green"*); only `enforcement_statement` asserts live with a date. Same defect class as #21, previously undetected. Nothing cross-checks a `test_file`'s parenthetical against its `status` — `level2_schema.py` requires only that the string be non-empty.

**5. #23 and #24 are ABSENT in this repo, not merely partial.**
`#23 red_team_coverage` → `test_file: tests/red-team/ (OSE repo — in construction)`; no threat ledger, no born-red harness, no workflow that checks out OSE to validate one. `#24 auditability` → `tests/audit-layer.spec.ts (OSE repo — in construction)`; no trace of the described audit tables or conformance generator anywhere here. `check_invariant_test_files()` explicitly treats a missing `test_file` on a `partial` invariant as acceptable, so nothing flags either.

## Classification — the four ocr-scoped invariants

| # | Verdict | Evidence |
|---|---|---|
| #13 `brain_enforcement_location` | **MECHANICAL, with a caveat** | `level2_schema.py` `inv13_*` checks run via `run_all.py` → `brain-validate.yml` on every PR. But they only assert the audit workflow *has* the right triggers and *calls* the right script — they never re-run the scan. The content scan itself is `continue-on-error` on `pull_request` (`brain-location-audit.yml:147`). |
| #20 `standards_propagation_completeness` | **MECHANICAL — harder than documented** | `level2_schema.py:848-876`. An in-code comment calls it "soft-pass," but `check()` has no soft/hard distinction: any failure increments `failed` and the script exits 1. The rare inverse of the usual gap — enforcement stronger than its own docs claim. |
| #23 `red_team_coverage` | **ABSENT** (register says partial) | Gate #5 |
| #24 `auditability` | **ABSENT** (register says partial) | Gate #5 |

## Enforcement present but unregistered

- `level0_security.py` + `shared/security_gate.py` — secret scan, PII-shaped pattern scan, forbidden-URL scan, and a `no_world_open_grant` check (`public_read: true` + `auth_required: false`) against the brain's own governance YAML. `gate=True`, so it blocks every subsequent level, on every PR and push. No numbered invariant claims it.
- The entire CHOICE A/I/B/U system — Gate #2. The largest unregistered surface found.
- `scan_phantom_invariants.py` + `phantom-scan.yml` — genuinely blocking (the `continue-on-error` exists only so the PR comment posts before an unconditional `Fail job` step re-propagates). Governance-of-the-governance, no invariant number.
- `level4_regression.py` — `ncr_7_levels` and `oureventring_is_aggregate`, pinned doctrine with no invariant number.

## Note on `ocr` as an applies_to value

Not a defect. `ocr` is a deliberately whitelisted org-level pseudo-entity in `level5_boundary.py:118` and `level7_contract.py:97`. The comment there cites "#13, #20"; #13's `applies_to` is actually `[]` and the real users are #20/#23/#24 — a stale comment, not a broken reference.
