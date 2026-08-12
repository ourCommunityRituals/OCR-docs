#!/usr/bin/env python3
"""
test_check_brain_contract.py — Regression lock for check_brain_contract.py's
invariant test-file resolution.

Why this exists
===============
On 2026-08-10 a CCR pass (run wf_ec339828-8ce) caught the brain
conformance gate false-failing on live invariants #22 and #25. Their
`test_file` values in architectural-invariants.yaml carry a trailing
human annotation in parentheses, e.g.:

    scripts/check-cross-repo-imports.sh (OSE repo)
    tests/e2e/0-architecture/sponsor-share-covenant.invariant.spec.ts (OSE repo — planned, OSE-663 / OSE-662)

`check_invariant_test_files` passed that raw string straight into
`repo.glob(f'**/{tf}')`. Because the ` (OSE repo…)` suffix is not part of
the path, the glob could NEVER match the real file (which exists in the
sibling OSE repo) — so both live invariants reported `missing_live` and
the gate FAILed even though zero test files were actually missing.

The fix added `_resolve_test_file(tf)`, which strips a trailing
' (' + annotation before globbing. This test locks that behavior so the
false-fail cannot silently return.

Exit codes:
  0 — all contracts hold
  1 — at least one contract failed
"""
import sys
import tempfile
from pathlib import Path

# Keep output legible on consoles whose default encoding (e.g. Windows
# cp1252) cannot represent the non-ASCII chars this file prints.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# Import the module under test. This file lives in BRAIN/tests/,
# the checker lives in BRAIN/scripts/.
BRAIN_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(BRAIN_ROOT / 'scripts'))

import check_brain_contract as cbc  # noqa: E402

results = []


def check(name: str, fn) -> None:
    try:
        detail = fn()
        results.append((name, 'PASS', detail or ''))
    except AssertionError as e:
        results.append((name, 'FAIL', str(e)))
    except Exception as e:
        results.append((name, 'FAIL', f'{type(e).__name__}: {e}'))


# ─── _resolve_test_file unit contracts ───────────────────────────────────────

def test_strips_trailing_ose_repo_annotation():
    """#22's shape: 'path (OSE repo)' → 'path'."""
    got = cbc._resolve_test_file('scripts/check-cross-repo-imports.sh (OSE repo)')
    assert got == 'scripts/check-cross-repo-imports.sh', got
    return got


def test_strips_multiword_annotation():
    """#25's shape: 'path (OSE repo — planned, OSE-663 / OSE-662)' → 'path'."""
    raw = ('tests/e2e/0-architecture/sponsor-share-covenant.invariant.spec.ts '
           '(OSE repo — planned, OSE-663 / OSE-662)')
    got = cbc._resolve_test_file(raw)
    assert got == 'tests/e2e/0-architecture/sponsor-share-covenant.invariant.spec.ts', got
    return got


def test_leaves_plain_path_untouched():
    """A path with no annotation must pass through unchanged."""
    raw = 'tests/e2e/foo.invariant.spec.ts'
    got = cbc._resolve_test_file(raw)
    assert got == raw, got
    return got


# ─── End-to-end contract against check_invariant_test_files ──────────────────

def test_annotated_live_invariant_matches_when_file_exists():
    """The bug reproducer: a live invariant whose test_file carries an
    '(OSE repo)' suffix must PASS when the underlying file exists in the repo.

    Before the fix this FAILed (missing_live) because the annotated string
    was globbed verbatim and never matched."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        # Create the real file the invariant points at.
        target = repo / 'scripts' / 'check-cross-repo-imports.sh'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('#!/usr/bin/env bash\n', encoding='utf-8')

        brain = {
            'invariants': {
                'invariants': [
                    {
                        'id': 22,
                        'applies_to': ['ose'],
                        'status': 'live',
                        'test_file': 'scripts/check-cross-repo-imports.sh (OSE repo)',
                    },
                ]
            }
        }
        name, status, detail = cbc.check_invariant_test_files(repo, brain, 'ose')
        assert status == cbc.PASS, (
            f'expected PASS, got {status}: {detail}'
        )
    return 'annotated live invariant resolves to existing file -> PASS'


def test_annotated_live_invariant_still_fails_when_file_absent():
    """Guard against over-stripping: if the resolved file genuinely does
    NOT exist, a live invariant must still FAIL (missing_live)."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)  # empty repo — target file absent
        brain = {
            'invariants': {
                'invariants': [
                    {
                        'id': 22,
                        'applies_to': ['ose'],
                        'status': 'live',
                        'test_file': 'scripts/check-cross-repo-imports.sh (OSE repo)',
                    },
                ]
            }
        }
        name, status, detail = cbc.check_invariant_test_files(repo, brain, 'ose')
        assert status == cbc.FAIL, (
            f'expected FAIL for genuinely missing live file, got {status}: {detail}'
        )
    return 'genuinely missing live file still FAILs (no false pass)'


# ─── Run all contracts ───────────────────────────────────────────────────────

CONTRACTS = [
    ('resolve.strips_ose_repo_annotation', test_strips_trailing_ose_repo_annotation),
    ('resolve.strips_multiword_annotation', test_strips_multiword_annotation),
    ('resolve.leaves_plain_path_untouched', test_leaves_plain_path_untouched),
    ('invariant.annotated_live_matches_existing_file',
     test_annotated_live_invariant_matches_when_file_exists),
    ('invariant.annotated_live_missing_still_fails',
     test_annotated_live_invariant_still_fails_when_file_absent),
]

for name, fn in CONTRACTS:
    check(name, fn)

# ─── Report ──────────────────────────────────────────────────────────────────

passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')

bar = '=' * 76
print(bar)
print('  CHECK_BRAIN_CONTRACT — TEST_FILE RESOLUTION')
print(bar)
for name, status, detail in results:
    marker = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {marker}  {name:50} {detail}')
print('-' * 76)
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print('-' * 76)
print()
print('Source of test: CCR run wf_ec339828-8ce (2026-08-10) caught')
print('live invariants #22/#25 false-failing on annotated test_file values.')

sys.exit(0 if failed == 0 else 1)
