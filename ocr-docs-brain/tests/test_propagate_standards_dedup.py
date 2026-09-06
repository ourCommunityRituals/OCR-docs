#!/usr/bin/env python3
"""
test_propagate_standards_dedup.py — Structural lock for propagate-standards.yml
dedup (OCR-129).

Why this exists
===============
`propagate-standards.yml` used to open a branch named
`ocr-standards/propagate-$(date +%Y%m%d-%H%M%S)` on every triggering push. Two
brain commits in quick succession therefore left TWO open propagation PRs per
spoke, and the human rule "merge newest, close older" could silently DROP a
delta that lived only on the closed PR's branch (the delta-drop OCR-129 fixes;
kin to the #109 early-squash stranded-commit incident).

The fix makes a second open PR impossible by construction: a single STABLE
branch per spoke (`ocr-standards/propagate`) — GitHub allows one open PR per
head — with every run either APPENDING to the open PR's branch or opening the
one PR when none is open.

This is a STRUCTURAL lock, not an execution test: a GitHub Actions workflow
that shells out to real `git`/`gh` against live remotes cannot be run
hermetically. So — in the same spirit as `tests/validate_action_metadata.py`
— it parses the workflow YAML and asserts the invariants that make dedup hold,
so a regression back to a per-run branch (or a second `gh pr create`) fails
here, in `brain-validate`, before the workflow ships.

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
WORKFLOW = REPO_ROOT / '.github' / 'workflows' / 'propagate-standards.yml'

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


def propagate_run_text(wf: dict) -> str:
    """Concatenate every `run:` script in the `propagate` job."""
    job = wf['jobs']['propagate']
    return '\n'.join(step.get('run', '') for step in job['steps'])


# ─── 1. Stable branch, centralized, no per-run timestamp ─────────────────────

def test_stable_branch_env_var():
    wf = load_workflow()
    env = wf.get('env', {}) or {}
    branch = env.get('PROPAGATE_BRANCH')
    assert branch, 'workflow env must define PROPAGATE_BRANCH (the stable branch)'
    assert '$(' not in branch and 'date' not in branch, (
        f'PROPAGATE_BRANCH must be a constant, not run-computed: {branch!r}')
    assert branch == 'ocr-standards/propagate', f'unexpected branch: {branch!r}'
    return f'PROPAGATE_BRANCH = {branch!r} (stable, centralized)'


def test_no_timestamped_branch_anywhere():
    """The root-cause lock: no `$(date ...)` may build a branch. This is the
    exact construct that produced two-PRs-per-spoke."""
    wf = load_workflow()
    text = propagate_run_text(wf)
    assert 'propagate-$(date' not in text, 'per-run timestamped branch reintroduced'
    assert '$(date' not in text, (
        'a $(date ...) substitution is back in the propagate job — the '
        'delta-drop regression')
    return 'no $(date ...) branch construction in the propagate job'


def test_branch_is_used_via_env():
    wf = load_workflow()
    text = propagate_run_text(wf)
    assert '$PROPAGATE_BRANCH' in text or '${PROPAGATE_BRANCH}' in text, (
        'PROPAGATE_BRANCH is defined but never used in the propagate job')
    return 'propagate job uses $PROPAGATE_BRANCH'


# ─── 2. Open-PR dedup + single create + append path ──────────────────────────

def test_checks_for_open_pr_before_creating():
    wf = load_workflow()
    text = propagate_run_text(wf)
    assert 'gh pr list' in text, 'must query existing PRs (gh pr list)'
    assert '--state open' in text, 'the PR query must filter --state open'
    assert '--head' in text, 'the PR query must scope --head to the propagate branch'
    assert 'OPEN_PR' in text, 'must capture the open-PR result (OPEN_PR)'
    return 'queries open PRs (gh pr list --state open --head) into OPEN_PR'


def test_exactly_one_pr_create():
    """Two `gh pr create` calls would let a second PR slip through. There must
    be exactly one, and it must be guarded by the no-open-PR branch."""
    wf = load_workflow()
    text = propagate_run_text(wf)
    n = text.count('gh pr create')
    assert n == 1, f'expected exactly one `gh pr create`, found {n}'
    assert '-n "$OPEN_PR"' in text, (
        'the create must be gated on `[ -n "$OPEN_PR" ]` (append) / else (create)')
    return 'exactly one gh pr create, guarded by the OPEN_PR check'


def test_append_path_comments_not_creates():
    """When a PR is open the workflow APPENDS (pushes to its branch + comments),
    it does not open a second PR."""
    wf = load_workflow()
    text = propagate_run_text(wf)
    assert 'gh pr comment' in text, (
        'the append path must annotate the existing PR (gh pr comment)')
    assert 'HEAD:$PROPAGATE_BRANCH' in text or 'HEAD:${PROPAGATE_BRANCH}' in text, (
        'must push onto the stable branch (fast-forward append)')
    return 'append path pushes to stable branch + comments (no 2nd PR)'


CONTRACTS = [
    ('branch.stable_env_var', test_stable_branch_env_var),
    ('branch.no_timestamped_branch', test_no_timestamped_branch_anywhere),
    ('branch.used_via_env', test_branch_is_used_via_env),
    ('dedup.checks_open_pr', test_checks_for_open_pr_before_creating),
    ('dedup.exactly_one_create', test_exactly_one_pr_create),
    ('dedup.append_comments_not_creates', test_append_path_comments_not_creates),
]

for name, fn in CONTRACTS:
    check(name, fn)

passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')

bar = '=' * 76
print(bar)
print('  PROPAGATE-STANDARDS DEDUP — ONE STABLE BRANCH / ONE OPEN PR PER SPOKE')
print(bar)
for name, status, detail in results:
    marker = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {marker}  {name:36} {detail}')
print('-' * 76)
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print('-' * 76)
print()
print('Source of test: OCR-129 (harden propagate-standards.yml dedup). Locks')
print('that a second open propagation PR — and thus a dropped delta — is')
print('impossible by construction (one stable branch, one guarded gh pr create).')

sys.exit(0 if failed == 0 else 1)
