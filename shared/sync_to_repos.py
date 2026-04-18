#!/usr/bin/env python3
"""
sync_to_repos.py — Push canonical shared gate modules to consumer repos
======================================================================
Copies OCR-docs/shared/*.py to every consumer repo's tests/_shared/
directory. Run this after editing any canonical shared module.

Canonical modules synced:
  - security_gate.py   — baseline secret/PII/URL scans + pragma support
  - pragma_audit.py    — inline `security-gate: allow` policy enforcement

Consumers are listed in CONSUMER_REPOS below — add new app repos here
when they onboard their first level0_security.py.
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
    rc = 0
    total_writes = 0
    total_ok = 0
    for canonical in CANONICALS:
        src = SHARED_DIR / canonical
        if not src.exists():
            print(f'[FAIL]  canonical not found at {src}')
            rc = 1
            continue
        src_bytes = src.read_bytes()
        for repo in CONSUMER_REPOS:
            dest = SIBLING_DIR / repo / 'tests' / '_shared' / canonical
            if not dest.parent.parent.exists():
                print(f'  SKIP   {repo}/tests/_shared/{canonical}  (repo not present)')
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            existing = dest.read_bytes() if dest.exists() else None
            if existing == src_bytes:
                print(f'  OK     {repo}/tests/_shared/{canonical}')
                total_ok += 1
                continue
            dest.write_bytes(src_bytes)
            print(f'  WROTE  {repo}/tests/_shared/{canonical}')
            total_writes += 1
    print()
    print(f'Synced {len(CANONICALS)} canonical(s) × {len(CONSUMER_REPOS)} repo(s): '
          f'{total_writes} wrote, {total_ok} already up to date')
    return rc


if __name__ == '__main__':
    sys.exit(main())
