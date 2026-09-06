#!/usr/bin/env python3
"""
test_check_secrets_baseline.py — Logic lock for check_secrets_baseline.py (OCR-130).

Why this exists
===============
The secret gate's enforcing decision is: fail iff the current scan contains a
(file, hashed_secret) pair NOT already accepted in the committed baseline —
keyed on hashed_secret, not line number, so line churn on a known secret does
not flap. This file locks that decision hermetically:

  * `pairs()` normalizes Windows/Linux paths (a baseline written on Windows must
    match a scan run on Linux CI) and flattens every detection.
  * a NEW (file, hash) pair => the set difference is non-empty => the gate fails.
  * a known secret that only MOVES lines => same hash => difference empty => pass.

These are pure-Python assertions over fake baseline dicts, so they need neither
`detect-secrets` installed nor a git tree — they run under `run_script_tests.py`
in `brain-validate`. The end-to-end "the real scanner actually bites" proof is a
born-red step inside `secret-scan.yml` (plants a fake key, asserts exit 1),
because a live detect-secrets scan cannot run hermetically here.

Exit codes:
  0 — all contracts hold
  1 — at least one contract failed
"""
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BRAIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BRAIN_ROOT / 'scripts'))

import check_secrets_baseline as gate  # noqa: E402

results = []


def check(name: str, fn) -> None:
    try:
        detail = fn()
        results.append((name, 'PASS', detail or ''))
    except AssertionError as e:
        results.append((name, 'FAIL', str(e)))
    except Exception as e:
        results.append((name, 'FAIL', f'{type(e).__name__}: {e}'))


def _doc(results_map):
    """Build a minimal detect-secrets-baseline-shaped doc from
    {path: [(hashed_secret, line_number), ...]}."""
    return {
        'results': {
            path: [{'hashed_secret': h, 'line_number': ln} for h, ln in entries]
            for path, entries in results_map.items()
        }
    }


# ─── pairs(): flatten + path normalization ───────────────────────────────────

def test_pairs_flattens_all_detections():
    doc = _doc({'a.md': [('h1', 3), ('h2', 9)], 'b.json': [('h3', 1)]})
    assert gate.pairs(doc) == {('a.md', 'h1'), ('a.md', 'h2'), ('b.json', 'h3')}
    return 'every (file, hashed_secret) pair is flattened'


def test_pairs_normalizes_windows_paths():
    win = gate.pairs(_doc({r'docs\notes.md': [('h1', 1)]}))
    nix = gate.pairs(_doc({'docs/notes.md': [('h1', 1)]}))
    assert win == nix == {('docs/notes.md', 'h1')}, (win, nix)
    return 'backslash paths normalize to forward slashes (Win baseline == Linux scan)'


def test_pairs_empty_doc():
    assert gate.pairs({}) == set()
    assert gate.pairs({'results': {}}) == set()
    return 'no results -> empty set (no crash)'


# ─── the enforcing decision: NEW = current - baseline ────────────────────────

def test_new_secret_is_flagged():
    baseline = _doc({'known.md': [('hA', 1)]})
    current = _doc({'known.md': [('hA', 1)], 'leak.md': [('hB', 2)]})
    new = gate.pairs(current) - gate.pairs(baseline)
    assert new == {('leak.md', 'hB')}, new
    return 'a (file, hash) not in baseline appears in the NEW set -> gate fails'


def test_line_churn_on_known_secret_does_not_flag():
    """Same secret, different line number => same hashed_secret => NOT new.
    This is the anti-flake property (keys on hash, not location)."""
    baseline = _doc({'known.md': [('hA', 1)]})
    current = _doc({'known.md': [('hA', 42)]})   # moved from line 1 to 42
    new = gate.pairs(current) - gate.pairs(baseline)
    assert new == set(), new
    return 'known secret moving lines is NOT new (keys on hash, not line)'


def test_clean_tree_has_no_new():
    baseline = _doc({'known.md': [('hA', 1)], 'k2.json': [('hB', 5)]})
    current = _doc({'known.md': [('hA', 1)], 'k2.json': [('hB', 5)]})
    assert gate.pairs(current) - gate.pairs(baseline) == set()
    return 'current == baseline -> no NEW -> gate passes'


# ─── excludes stay in lockstep with the documented re-baseline command ────────

def test_excludes_cover_baseline_file():
    """The baseline file itself must be excluded (it stores hashed_secret values
    that would otherwise be re-flagged forever)."""
    assert any('secrets' in p and 'baseline' in p for p in gate.EXCLUDES), gate.EXCLUDES
    return '.secrets.baseline is excluded from the scan'


CONTRACTS = [
    ('pairs.flattens', test_pairs_flattens_all_detections),
    ('pairs.normalizes_paths', test_pairs_normalizes_windows_paths),
    ('pairs.empty', test_pairs_empty_doc),
    ('decision.new_secret_flagged', test_new_secret_is_flagged),
    ('decision.line_churn_ignored', test_line_churn_on_known_secret_does_not_flag),
    ('decision.clean_tree_passes', test_clean_tree_has_no_new),
    ('excludes.baseline_excluded', test_excludes_cover_baseline_file),
]

for name, fn in CONTRACTS:
    check(name, fn)

passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')

bar = '=' * 76
print(bar)
print('  CHECK_SECRETS_BASELINE — NEW-SECRET DIFF / HASH-KEYED / PATH-NORMALIZED')
print(bar)
for name, status, detail in results:
    marker = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {marker}  {name:34} {detail}')
print('-' * 76)
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print('-' * 76)
print()
print('Source of test: OCR-130 (brain content secret-scanner, ports OSE-911).')
print('Locks the enforcing decision (new = current - baseline, keyed on hash).')
print('The "scanner actually bites" proof is the born-red step in secret-scan.yml.')

sys.exit(0 if failed == 0 else 1)
