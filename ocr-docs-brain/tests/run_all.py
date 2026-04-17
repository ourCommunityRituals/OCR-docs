#!/usr/bin/env python3
"""
run_all.py — Brain test pyramid runner
========================================
Executes all test levels in order. Level 0 (lint) is a gate:
if lint fails, nothing else runs. All other levels run to completion
and report aggregated results.

Usage:
  python3 tests/run_all.py            # run all levels
  python3 tests/run_all.py --level 3  # run up to level 3
  python3 tests/run_all.py --from 5   # run levels 5+
"""
import argparse, subprocess, sys, time
from pathlib import Path

TESTS_DIR = Path(__file__).parent

LEVELS = [
    (0, 'level0_lint.py',        'LINT',                   True),   # gate=True: blocks all subsequent
    (1, 'level1_schema.py',      'SCHEMA',                 False),
    (2, 'level2_unit.py',        'UNIT',                   False),
    (3, 'level3_regression.py',  'REGRESSION',             False),
    (4, 'level4_boundary.py',    'BOUNDARY',               False),
    (5, 'level5_integration.py', 'INTEGRATION',            False),
    (6, 'level6_contract.py',    'CONTRACT (provider)',     False),
    (7, 'level7_pact.py',        'PACT (consumer-driven)', False),
    (8, 'level8_academic.py',    'ACADEMIC FOUNDATIONS',    False),
]


def run_level(num, script, label, gate=False):
    path = TESTS_DIR / script
    if not path.exists():
        print(f'  SKIP  Level {num} — {label}  ({script} not found)')
        return None

    start = time.time()
    result = subprocess.run(
        [sys.executable, str(path)],
        capture_output=True, text=True, timeout=60,
    )
    elapsed = time.time() - start

    # Extract pass/fail counts from last line of output
    lines = result.stdout.strip().splitlines()
    summary_line = lines[-2] if len(lines) >= 2 else ''

    status = 'PASS' if result.returncode == 0 else 'FAIL'
    print(f'  {status}  Level {num} — {label:28} {summary_line.strip():>50}  ({elapsed:.1f}s)')

    if result.returncode != 0 and gate:
        print()
        print(f'  GATE FAILURE at Level {num}. Subsequent levels will not run.')
        print(f'  Fix lint issues first.')
        print()
        # Print the failing details
        for line in lines:
            if '[FAIL]' in line:
                print(f'    {line.strip()}')

    return result.returncode


def main():
    ap = argparse.ArgumentParser(description='Brain test pyramid runner')
    ap.add_argument('--level', type=int, help='Run up to this level (inclusive)')
    ap.add_argument('--from', type=int, dest='from_level', help='Run from this level (inclusive)')
    ap.add_argument('--verbose', '-v', action='store_true', help='Show full output of failing levels')
    args = ap.parse_args()

    max_level = args.level if args.level is not None else 99
    min_level = args.from_level if args.from_level is not None else 0

    print()
    print(f'{"="*76}')
    print(f'  BRAIN TEST PYRAMID')
    print(f'  Running levels {min_level} through {min(max_level, LEVELS[-1][0])}')
    print(f'{"="*76}')
    print()

    total_start = time.time()
    level_results = {}
    gate_failed = False

    for num, script, label, gate in LEVELS:
        if num > max_level:
            break
        if num < min_level:
            continue
        if gate_failed:
            print(f'  SKIP  Level {num} — {label}  (blocked by gate failure)')
            level_results[num] = 'SKIP'
            continue

        rc = run_level(num, script, label, gate)
        if rc is None:
            level_results[num] = 'SKIP'
        elif rc == 0:
            level_results[num] = 'PASS'
        else:
            level_results[num] = 'FAIL'
            if gate:
                gate_failed = True

    elapsed = time.time() - total_start
    passed = sum(1 for v in level_results.values() if v == 'PASS')
    failed = sum(1 for v in level_results.values() if v == 'FAIL')
    skipped = sum(1 for v in level_results.values() if v == 'SKIP')

    print()
    print(f'{"-"*76}')
    print(f'  PYRAMID SUMMARY: {passed} pass / {failed} fail / {skipped} skip  ({elapsed:.1f}s)')

    if failed:
        failing = [f'Level {k}' for k, v in level_results.items() if v == 'FAIL']
        print(f'  Failures: {", ".join(failing)}')

    print(f'{"-"*76}')
    print()

    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
