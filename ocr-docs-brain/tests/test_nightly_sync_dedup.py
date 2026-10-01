#!/usr/bin/env python3
"""
test_nightly_sync_dedup.py — Structural lock for nightly-sync-check.yml
issue dedup (sibling to OCR-129's propagate-standards dedup).

Why this exists
================
`nightly-sync-check.yml` used to unconditionally close any open
`nightly-sync` issue and open a brand-new one every night, even when the
findings were identical to the prior run (e.g. the same spoke standards PR
still awaiting human review, night after night). That produced issue spam —
dozens of near-duplicate "Nightly Sync" issues (#18-#33 and onward) carrying
the same unresolved drift — the opposite of the "never duplicate — fold into
the owner" reconciliation rule (CLAUDE.md knowledge-homes section).

The fix: when an open `nightly-sync` issue already flags the same set of
repos at the same severity (`### :icon: repo` section headers match), fold
today's run into that issue (refresh title/body + comment) instead of
closing it and creating a duplicate. Only close + recreate when the flagged
repos or their severity actually changed.

This is a STRUCTURAL lock, not an execution test: a GitHub Actions workflow
that shells out to real `gh`/`git` against live issues cannot be run
hermetically. So — in the same spirit as `test_propagate_standards_dedup.py`
— it parses the workflow YAML and asserts the invariants that make the
fold-in-instead-of-duplicate behavior hold, so a regression back to
unconditional close+recreate fails here, in `brain-validate`, before the
workflow ships.

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

import yaml

# ocr-docs-brain/tests/ -> repo root is two parents up.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOW = REPO_ROOT / '.github' / 'workflows' / 'nightly-sync-check.yml'

results = []


def check(name: str, fn) -> None:
    try:
        detail = fn()
        results.append((name, 'PASS', detail or ''))
    except AssertionError as e:
        results.append((name, 'FAIL', str(e)))
    except Exception as e:
        results.append((name, 'FAIL', f'{type(e).__name__}: {e}'))


def load_workflow() -> dict:
    assert WORKFLOW.exists(), f'workflow missing: {WORKFLOW}'
    return yaml.safe_load(WORKFLOW.read_text(encoding='utf-8'))


def sync_check_run_text(wf: dict) -> str:
    """Concatenate every `run:` script in the `sync-check` job."""
    job = wf['jobs']['sync-check']
    return '\n'.join(step.get('run', '') for step in job['steps'])


# ─── 1. Existing-issue lookup, scoped to the open nightly-sync label ─────────

def test_checks_for_existing_open_issue():
    wf = load_workflow()
    text = sync_check_run_text(wf)
    assert 'gh issue list' in text, 'must query existing issues (gh issue list)'
    assert '--label "nightly-sync"' in text, 'the query must scope --label "nightly-sync"'
    assert '--state open' in text, 'the query must filter --state open'
    assert 'EXISTING' in text, 'must capture the existing-issue result (EXISTING)'
    return 'queries open issues (gh issue list --label nightly-sync --state open) into EXISTING'


# ─── 2. Findings comparison — repo section headers, not incidental fields ────

def test_compares_report_sections_not_whole_body():
    wf = load_workflow()
    text = sync_check_run_text(wf)
    assert text.count("grep '^### '") >= 2, (
        "must extract '### ' repo-section headers from both the existing "
        'issue body and the new report to compare findings')
    assert 'NEW_SECTIONS' in text and 'EXISTING_SECTIONS' in text, (
        'must name the compared findings (NEW_SECTIONS / EXISTING_SECTIONS)')
    return 'compares ### repo-section headers (findings), not the raw body'


# ─── 3. Fold-in path: edit + comment, not close+recreate ─────────────────────

def test_unchanged_findings_fold_into_existing_issue():
    wf = load_workflow()
    text = sync_check_run_text(wf)
    assert 'gh issue edit "$EXISTING"' in text, (
        'when findings are unchanged, the existing issue must be updated '
        'in place (gh issue edit), not closed')
    assert 'gh issue comment "$EXISTING"' in text, (
        'the fold-in path must leave a comment noting the run was folded in')
    return 'unchanged findings: gh issue edit + gh issue comment (no duplicate)'


def test_changed_findings_close_and_recreate():
    wf = load_workflow()
    text = sync_check_run_text(wf)
    assert 'gh issue close "$EXISTING"' in text, (
        'when findings genuinely changed, the stale issue must still be closed')
    n = text.count('gh issue create')
    assert n == 2, (
        f'expected exactly two `gh issue create` calls (changed-findings path '
        f'+ no-existing-issue path), found {n}')
    return 'changed findings (or no existing issue): gh issue close + gh issue create'


def test_no_unconditional_close():
    """The regression this guards against: closing EXISTING unconditionally
    before deciding whether findings actually changed."""
    wf = load_workflow()
    text = sync_check_run_text(wf)
    assert 'Superseded by new nightly run.' not in text, (
        'the old unconditional "Superseded by new nightly run." close comment '
        'is back — this closed+recreated on every run regardless of whether '
        'findings changed')
    return 'no unconditional close-then-create of the existing issue'


CONTRACTS = [
    ('lookup.existing_open_issue', test_checks_for_existing_open_issue),
    ('compare.report_sections', test_compares_report_sections_not_whole_body),
    ('fold_in.unchanged_edits_existing', test_unchanged_findings_fold_into_existing_issue),
    ('recreate.changed_closes_and_creates', test_changed_findings_close_and_recreate),
    ('regression.no_unconditional_close', test_no_unconditional_close),
]

for name, fn in CONTRACTS:
    check(name, fn)

passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')

bar = '=' * 76
print(bar)
print('  NIGHTLY-SYNC-CHECK DEDUP — FOLD UNCHANGED FINDINGS, NEVER DUPLICATE')
print(bar)
for name, status, detail in results:
    marker = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {marker}  {name:36} {detail}')
print('-' * 76)
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print('-' * 76)
print()
print('Source of test: nightly-sync issue spam (#18-#33+, same findings night')
print('after night). Locks that unchanged findings fold into the existing open')
print('issue instead of closing it and opening a duplicate.')

sys.exit(0 if failed == 0 else 1)
