#!/usr/bin/env python3
"""
check_drift.py — Verify consumer repos have latest security_gate.py
======================================================================
Fails if any consumer repo's vendored copy diverges from the canonical.
Run this in OCR-docs CI to catch drift before it breaks downstream gates.

Exit codes:
  0  all consumers in sync (or absent)
  1  one or more consumers out of sync — run sync_to_repos.py
"""
import sys
from pathlib import Path

CANONICAL = Path(__file__).parent / 'security_gate.py'
SIBLING_DIR = Path(__file__).parent.parent.parent

CONSUMERS = [
    'ourSharedEvents/tests/_shared/security_gate.py',
    'ourWKRP/tests/_shared/security_gate.py',
]


def main() -> int:
    if not CANONICAL.exists():
        print(f'[FAIL]  canonical not found at {CANONICAL}')
        return 1
    canonical_bytes = CANONICAL.read_bytes()
    drift = []
    for rel in CONSUMERS:
        dest = SIBLING_DIR / rel
        if not dest.parent.parent.exists():
            print(f'  SKIP   {rel}  (consumer repo not present)')
            continue
        if not dest.exists():
            print(f'  FAIL   {rel}  MISSING vendored copy')
            drift.append(rel)
            continue
        if dest.read_bytes() != canonical_bytes:
            print(f'  FAIL   {rel}  OUT OF SYNC with canonical')
            drift.append(rel)
            continue
        print(f'  OK     {rel}')
    print()
    if drift:
        print(f'DRIFT DETECTED in {len(drift)} consumer(s).')
        print(f'Fix: cd OCR-docs && py shared/sync_to_repos.py')
        print(f'Then commit the updated tests/_shared/security_gate.py in each affected repo.')
        return 1
    print(f'All {len(CONSUMERS)} consumer(s) in sync with canonical.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
