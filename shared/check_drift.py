#!/usr/bin/env python3
"""
check_drift.py — Verify consumer repos have latest shared modules
======================================================================
Fails if any consumer repo's vendored copies diverge from the canonicals.
Run this in OCR-docs CI to catch drift before it breaks downstream gates.

Canonical modules checked:
  - security_gate.py   — baseline secret/PII/URL scans + pragma support
  - pragma_audit.py    — inline `security-gate: allow` policy enforcement

Exit codes:
  0  all consumers in sync (or absent)
  1  one or more consumers out of sync — run sync_to_repos.py
"""
import sys
from pathlib import Path

SHARED_DIR = Path(__file__).parent
SIBLING_DIR = SHARED_DIR.parent.parent
CANONICALS = ('security_gate.py', 'pragma_audit.py')

CONSUMER_REPOS = [
    'ourSharedEvents',
    'ourWKRP',
    'packages/flags',
]


def main() -> int:
    drift: list[str] = []
    checked = 0
    for canonical in CANONICALS:
        src = SHARED_DIR / canonical
        if not src.exists():
            print(f'[FAIL]  canonical not found at {src}')
            return 1
        src_bytes = src.read_bytes()
        for repo in CONSUMER_REPOS:
            rel = f'{repo}/tests/_shared/{canonical}'
            dest = SIBLING_DIR / repo / 'tests' / '_shared' / canonical
            if not dest.parent.parent.exists():
                print(f'  SKIP   {rel}  (consumer repo not present)')
                continue
            checked += 1
            if not dest.exists():
                print(f'  FAIL   {rel}  MISSING vendored copy')
                drift.append(rel)
                continue
            if dest.read_bytes() != src_bytes:
                print(f'  FAIL   {rel}  OUT OF SYNC with canonical')
                drift.append(rel)
                continue
            print(f'  OK     {rel}')
    print()
    if drift:
        print(f'DRIFT DETECTED in {len(drift)} vendored copy(s).')
        print(f'Fix: cd OCR-docs && py shared/sync_to_repos.py')
        print(f'Then commit the updated tests/_shared/*.py in each affected repo.')
        return 1
    print(f'All {checked} vendored copy(s) in sync with canonical.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
