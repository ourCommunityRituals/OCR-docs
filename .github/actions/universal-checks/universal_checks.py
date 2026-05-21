#!/usr/bin/env python3
"""
universal_checks.py
===================
Helper for the OCR `universal-checks` composite action. Runs the two
universal checks that need Python:

  U-5  .ocr-standards/ is present and synced with OCR-docs
  U-6  no leaked secrets (delegates to OCR-docs/shared/security_gate.py)

The remaining universal checks are shell steps in action.yml (U-2
typecheck + lint, U-3/U-7 CLAUDE.md identity_mode). U-1 security headers
and U-4 layered tests are verified by the spoke's own test suite — a hub
action cannot see them — so they are intentionally out of scope here.

security_gate.py is a library (no __main__) and is imported by every app
repo's level0_security.py. This wrapper exists so the action can reuse it
without modifying the canonical shared file.

Usage:
  universal_checks.py --shared <ocr-docs/shared> --ocr-docs <ocr-docs root> --spoke <spoke root>

Exit: 0 = no FAIL, 1 = at least one FAIL, 2 = execution error.
"""
import argparse
import hashlib
import sys
from pathlib import Path

PASS, WARN, FAIL = 'PASS', 'WARN', 'FAIL'


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_standards(spoke: Path, ocr_docs: Path) -> list[tuple[str, str, str]]:
    """U-5 — .ocr-standards/ present and synced with OCR-docs."""
    std = spoke / '.ocr-standards'
    if not std.is_dir() or not any(std.rglob('*')):
        return [('U-5', FAIL,
                 '.ocr-standards/ missing or empty — run the OCR-docs '
                 'propagate-standards workflow to seed it')]

    results = [('U-5', PASS, '.ocr-standards/ present')]
    spoke_vision = std / 'docs' / 'OCR_VISION.md'
    hub_vision = ocr_docs / 'docs' / 'OCR_VISION.md'
    if spoke_vision.exists() and hub_vision.exists():
        if sha256(spoke_vision) == sha256(hub_vision):
            results.append(('U-5', PASS, 'OCR_VISION.md matches OCR-docs'))
        else:
            results.append(('U-5', WARN,
                             'OCR_VISION.md has drifted from OCR-docs — a '
                             'propagate-standards PR is pending; merge it to '
                             'resync (nightly-sync-check tracks this)'))
    elif not spoke_vision.exists():
        results.append(('U-5', WARN,
                         '.ocr-standards/docs/OCR_VISION.md absent — standards '
                         'dir is stale; re-run propagate-standards'))
    return results


def check_secrets(spoke: Path, shared: Path) -> list[tuple[str, str, str]]:
    """U-6 — token-shaped secret scan via the canonical security gate."""
    sys.path.insert(0, str(shared))
    try:
        from security_gate import scan_secrets
    except Exception as e:  # noqa: BLE001 — surface any import failure as a check failure
        return [('U-6', FAIL, f'cannot load security_gate from {shared}: {e}')]

    fails = scan_secrets(spoke)
    if fails:
        return [('U-6', FAIL, detail) for _, _, detail in fails]
    return [('U-6', PASS, 'no token-shaped secrets found')]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--shared', required=True, help='OCR-docs/shared directory')
    ap.add_argument('--ocr-docs', required=True, help='OCR-docs repo root')
    ap.add_argument('--spoke', default='.', help='spoke repo root to check')
    args = ap.parse_args()

    spoke = Path(args.spoke).resolve()
    if not spoke.is_dir():
        print(f'ERROR: spoke path {spoke} is not a directory', file=sys.stderr)
        sys.exit(2)

    results = (check_standards(spoke, Path(args.ocr_docs))
               + check_secrets(spoke, Path(args.shared)))

    fails = [r for r in results if r[1] == FAIL]
    print('=' * 76)
    print('  UNIVERSAL CHECKS — U-5 standards sync / U-6 secret scan')
    print('=' * 76)
    for rule, status, detail in results:
        print(f'  [{status:4}] {rule:4} {detail}')
        if status == FAIL:
            print(f'::error::{rule}: {detail}')
        elif status == WARN:
            print(f'::warning::{rule}: {detail}')
    print('-' * 76)
    print(f'  {len(fails)} fail / {len(results)} checks')
    print('-' * 76)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
