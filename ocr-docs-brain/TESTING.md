# Brain test pyramid

Eight levels, 437 checks, runs in under 2 seconds.

## Quick run (all levels)

```bash
python3 tests/run_all.py
```

Level 0 (lint) is a gate — if it fails, nothing else runs. All other levels run to completion.

## Run specific levels

```bash
python3 tests/run_all.py --level 3    # run levels 0-3 only
python3 tests/run_all.py --from 5     # run levels 5+ only
```

## The pyramid

| Level | File | What it tests | Check count |
|---|---|---|---|
| 0 | `level0_lint.py` | Syntax, encoding, formatting, semver, no tabs, no duplicate keys, file size bounds | ~51 |
| 1 | `level1_schema.py` | Required fields per record type, type validation, enum constraints | ~209 |
| 2 | `level2_unit.py` | Taxonomy counts, UEC uniqueness, UEC prefix matching, invariant sequencing, tier monotonicity | ~20 |
| 3 | `level3_regression.py` | Pinned governance values: locked product IDs, identity layers, faith-free commitment, minimum invariant count, schema version floors | ~25 |
| 4 | `level4_boundary.py` | Edge cases: orphaned datasets, empty origins, invalid refs, identity contradictions, circular funnels, invalid tier refs | ~28 |
| 5 | `level5_integration.py` | Cross-file workflows: scan event chain, HIPAA/COPPA routing, tier gating, faith sponsor, invariant claims | ~12 |
| 6 | `level6_contract.py` | Provider-side contracts: what the brain promises to every consumer | ~62 |
| 7 | `level7_pact.py` | Consumer-driven contracts: what OSE, WKRP, OAW, OSM each expect from the brain | ~30 |

## CI wiring

### Brain's own CI (OCR-docs repo)

```yaml
name: Brain validate
on: [pull_request, push]
jobs:
  validate:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install pyyaml packaging
      - run: python3 ocr-docs-brain/tests/run_all.py
      - run: python3 ocr-docs-brain/tests/run_script_tests.py
```

### Product repo CI (e.g. OSE)

Product repos run the brain's pyramid first, then run their own conformance checks against it. See `brain-contract-check.yml` in the governance loop package.

## Script self-tests

The pyramid (`run_all.py`) validates the brain *data*. A separate suite locks
the *behavior* of the helper scripts in `scripts/` that the spokes check out
and run at CI time (`open_drift_ticket.py`, `check_brain_contract.py`, …):

```bash
python3 tests/run_script_tests.py   # discovers + runs every tests/test_*.py
```

`run_script_tests.py` auto-discovers `tests/test_*.py`, so new self-tests are
picked up with no registration step. It is wired into `brain-validate.yml`
alongside the pyramid, so a defect in a helper is caught in OCR-docs before a
spoke runs the script at runtime. The suites are hermetic — the Linear GraphQL
transport is monkeypatched, so no network or `LINEAR_API_KEY` is needed.

Any workflow that calls a helper script SHOULD have a matching `test_*.py`
here. Current coverage:

| Test file | Locks |
|---|---|
| `test_open_drift_ticket.py` | dedup (`$teamId: ID!`), owner + priority on create, create-vs-update, team routing |
| `test_check_brain_contract.py` | `_resolve_test_file`, pool/tag checks, `pipeline_present`/`code_present` stub exemptions |
| `test_helper_cli_contracts.py` | helper CLI arg signatures the workflows depend on |

## Adding tests

New contract to the brain? Add the test at the appropriate level:

- New file or field → Level 0 (lint) + Level 1 (schema)
- New computed property → Level 2 (unit)
- New locked value → Level 3 (regression)
- New edge case → Level 4 (boundary)
- New cross-file workflow → Level 5 (integration)
- New promise to consumers → Level 6 (contract)
- New consumer expectation → Level 7 (pact)

Level 3 (regression) is governance-critical. Every value pinned there represents a deliberate commitment. If a regression test needs to change, the change must be discussed and documented before the assertion is updated.
