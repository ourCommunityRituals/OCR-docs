#!/usr/bin/env python3
"""
Level 0 — SECURITY (Brain pyramid)
====================================
Runs FIRST. Gate: blocks every other level on failure.
Imports baseline checks from OCR-docs/shared/security_gate.py and adds
brain-specific checks on top.
"""
import sys
from pathlib import Path

THIS_DIR = Path(__file__).parent
BRAIN = THIS_DIR.parent if (THIS_DIR.parent / 'product-registry.yaml').exists() else THIS_DIR.parent / 'ocr-docs-brain'
SHARED = (THIS_DIR.parent.parent / 'shared').resolve()

sys.path.insert(0, str(SHARED))
try:
    import security_gate
except ImportError as e:
    print('[FAIL]  shared security_gate.py not importable from OCR-docs/shared/')
    print(f'        looked at: {SHARED}')
    print(f'        error: {e}')
    print('        SECURITY GATE FAILS CLOSED — fix the shared module before continuing.')
    sys.exit(1)

results: list[tuple[str, str, str]] = []
passed = 0


def check(name: str, ok: bool, detail: str = '') -> None:
    global passed
    if ok:
        results.append((name, 'PASS', detail))
        passed += 1
    else:
        results.append((name, 'FAIL', detail))


fails = security_gate.run_baseline(BRAIN, allowlist_names=('security_gate.py', 'level0_security.py'))
results.extend(fails)
baseline_check_names = ('secret_scan', 'pii_scan', 'forbidden_url_scan')
for n in baseline_check_names:
    if not any(r[0] == n and r[1] == 'FAIL' for r in fails):
        check(n, True, 'clean')

REQUIRED_GOVERNANCE_FILES = [
    'product-registry.yaml',
    'tier-gates.yaml',
    'corridor-definitions.yaml',
    'event-taxonomy.yaml',
    'architectural-invariants.yaml',
]
for f in REQUIRED_GOVERNANCE_FILES:
    p = BRAIN / f
    if not p.exists():
        continue
    text = p.read_text(encoding='utf-8', errors='ignore')
    has_world_open = 'public_read: true' in text and 'auth_required: false' in text
    check(f'no_world_open_grant:{f}', not has_world_open,
          'world-open data grant detected' if has_world_open else 'clean')

security_gate.report_and_exit(results, passed, header='LEVEL 0 — SECURITY (Brain)')
