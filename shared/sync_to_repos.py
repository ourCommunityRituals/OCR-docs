#!/usr/bin/env python3
"""
sync_to_repos.py — Push canonical security_gate.py to consumer repos
======================================================================
Copies OCR-docs/shared/security_gate.py to every consumer repo's
tests/_shared/ directory. Run this after editing the canonical.

Consumers are listed in CONSUMERS below — add new app repos here when
they get their first level0_security.py.
"""
import shutil
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
    rc = 0
    for rel in CONSUMERS:
        dest = SIBLING_DIR / rel
        if not dest.parent.exists():
            print(f'  SKIP   {rel}  (consumer repo not present at {dest.parent})')
            continue
        existing = dest.read_bytes() if dest.exists() else None
        if existing == canonical_bytes:
            print(f'  OK     {rel}  (already up to date)')
            continue
        dest.write_bytes(canonical_bytes)
        print(f'  WROTE  {rel}')
    print()
    print(f'Synced {len(CONSUMERS)} consumer(s) from {CANONICAL.name}')
    return rc


if __name__ == '__main__':
    sys.exit(main())
