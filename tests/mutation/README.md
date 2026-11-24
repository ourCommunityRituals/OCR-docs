# Mutation testing for the brain's gate scripts

Every spoke checks out `ocr-docs-brain/scripts` and runs two of them as gates:
`check_brain_contract.py` (brain conformance) and `check_cross_repo_imports.py`
(invariant #22). Their self-tests in `ocr-docs-brain/tests/` say the gates
work. Mutation testing checks that the self-tests would notice if a gate
stopped working.

Each mutant in `script-mutants.json` writes one fault into a rule a gate
enforces (a violation ignored, a failure that exits 0, block mode that only
warns). `script_mutation.py` runs the mutant's kill tests with the fault in
place, then puts the source back. A mutant must be killed: a kill test exits
non-zero and its own `N pass / M fail` summary reports a failed case.

It fails closed. A test that crashed with no summary is an error, not a kill.
The kill tests must pass on the unchanged source first. A mutant whose `find`
text no longer occurs exactly once fails the catalog check, so a mutant
cannot silently hit the wrong line after the source moves.

## Running

    python3 tests/mutation/script_mutation.py --check   # the catalog only
    python3 tests/mutation/script_mutation.py           # baseline, then every mutant
    python3 tests/mutation/test_script_mutation.py      # the runner's self-test

`.github/workflows/mutation-testing.yml` runs both nightly, on demand, and on
a pull request that touches the gate scripts, their tests or this folder. The
run takes about 10 seconds.

## First run (2026-11-24)

12 of 12 mutants killed. The gate scripts' self-tests have teeth for every
rule in the catalog.

## Across the fleet

This is one layer of a series. The others:

- ourCommunityRituals: StrykerJS on `@ocr/flags` (unit and integration),
  `@ocr/tokens` and `@ocr/ui`, with per-file floors.
- ourWKRP: StrykerJS at the unit and integration layers, and hand-written
  end-to-end mutants judged by Playwright (`mutation/e2e-mutants.json`).
- ourSharedEvents: StrykerJS at the unit layer, and hand-written integration
  and end-to-end mutants (`mutation/layer-mutants.json`), because its worker
  tests run inside workerd where Stryker cannot reach.
