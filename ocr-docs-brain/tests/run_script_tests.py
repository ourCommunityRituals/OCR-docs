#!/usr/bin/env python3
"""
run_script_tests.py — Runner for the brain's script self-tests.

Why this exists
===============
`run_all.py` runs the conformance *pyramid* (level0..level9). It does NOT
run the `test_*.py` self-tests that lock the behavior of the helper scripts
in `scripts/` (open_drift_ticket.py, check_brain_contract.py, …). Until
2026-08-17 those test files existed but were wired into NO workflow — they
passed locally and were never executed in CI, which is indistinguishable
from having no tests at all.

This runner discovers every `tests/test_*.py`, runs each as its own process,
and aggregates. `brain-validate.yml` invokes it on every PR that touches
`ocr-docs-brain/**`, so a defect in a helper script is caught HERE, in
OCR-docs, before the spokes check the script out at runtime. New test files
are picked up automatically — no registration step to forget.

Exit codes:
  0 — every discovered self-test passed
  1 — at least one self-test failed (or none were discovered)
"""
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
except Exception:
    pass

TESTS_DIR = Path(__file__).parent


def main() -> int:
    test_files = sorted(TESTS_DIR.glob('test_*.py'))

    bar = '=' * 76
    print(bar)
    print('  BRAIN SCRIPT SELF-TESTS')
    print(bar)

    if not test_files:
        # Discovering nothing is a failure, not a pass: it means the wiring
        # broke (renamed dir, bad glob) and would otherwise report green.
        print('  [FAIL]  no test_*.py discovered in tests/ — wiring is broken')
        print('-' * 76)
        return 1

    failed = []
    for tf in test_files:
        start = time.time()
        proc = subprocess.run(
            [sys.executable, str(tf)],
            capture_output=True, text=True, timeout=120,
        )
        elapsed = time.time() - start
        ok = proc.returncode == 0
        marker = '[PASS]' if ok else '[FAIL]'
        # Surface the module's own summary line for context.
        summary = ''
        for line in reversed(proc.stdout.strip().splitlines()):
            if 'pass /' in line and 'fail' in line:
                summary = line.strip()
                break
        print(f'  {marker}  {tf.name:38} {summary:>28}  ({elapsed:.1f}s)')
        if not ok:
            failed.append(tf.name)
            # Echo the failing module's output so CI logs are self-contained.
            print('  ----- output -----')
            for line in proc.stdout.strip().splitlines():
                print(f'    {line}')
            if proc.stderr.strip():
                print('  ----- stderr -----')
                for line in proc.stderr.strip().splitlines():
                    print(f'    {line}')

    print('-' * 76)
    print(f'  {len(test_files) - len(failed)} pass / {len(failed)} fail  '
          f'(total {len(test_files)} self-test files)')
    if failed:
        print(f'  Failing: {", ".join(failed)}')
    print('-' * 76)
    return 0 if not failed else 1


if __name__ == '__main__':
    sys.exit(main())
