#!/usr/bin/env python3
"""
test_verify_reconcile_comment.py — Logic lock for verify_reconcile_comment.py.

Why this exists
===============
OCR-128 turned the reconciliation loop's SHA-citation rule (§4 step 2) from
prose into an executable gate. The gate's whole value is that it does NOT
trust a Done-flip comment's self-asserted `ancestor_verified: true` — it
recomputes ancestry against git. This file locks that behavior so it cannot
silently rot back into "presence-checking a hex string":

  1. **Schema integrity, not presence.** Each labeled field (sha / pr /
     ancestor_verified) is required; a bare hex run in prose is NOT a citation.
  2. **The self-asserted boolean is never trusted.** A comment claiming
     `ancestor_verified: true` for a SHA that git says is NOT an ancestor must
     FAIL — this is the exact 2026-09-03 false-"merged" failure mode.
  3. **Fail closed.** Fabricated/short SHAs, missing fields, and a git that
     can't run all resolve to "unverified", never to a pass.

Two test layers, mirroring the brain's other self-tests:
  * hermetic unit checks over `parse_citation` / `verify` (git isolated via a
    monkeypatched `is_ancestor`); and
  * one integration check that builds a throwaway git repo and drives the REAL
    `git merge-base --is-ancestor`, proving the subprocess wiring, plus a CLI
    check via subprocess proving exit codes 0/1/2.

Exit codes:
  0 — all contracts hold
  1 — at least one contract failed
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

BRAIN_ROOT = Path(__file__).parent.parent
SCRIPTS = BRAIN_ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import verify_reconcile_comment as vrc  # noqa: E402

SCRIPT = SCRIPTS / 'verify_reconcile_comment.py'

results = []


def check(name: str, fn) -> None:
    try:
        detail = fn()
        results.append((name, 'PASS', detail or ''))
    except AssertionError as e:
        results.append((name, 'FAIL', str(e)))
    except Exception as e:
        results.append((name, 'FAIL', f'{type(e).__name__}: {e}'))


# A canonical, schema-shaped citation block as the standard writes it.
GOOD_BLOCK = 'Merged to main. sha: a1b2c3d · ancestor_verified: true · pr: #451'


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    """Run git in `repo` with a fixed identity so commits work in CI's
    identity-less environment. Returns the CompletedProcess."""
    return subprocess.run(
        ['git', '-C', str(repo),
         '-c', 'user.name=t', '-c', 'user.email=t@t',
         '-c', 'commit.gpgsign=false', *args],
        capture_output=True, text=True, timeout=30,
    )


# ─── 1. parse_citation — schema integrity ────────────────────────────────────

def test_parse_extracts_all_fields():
    c = vrc.parse_citation(GOOD_BLOCK)
    assert c['sha'] == 'a1b2c3d', c
    assert c['ancestor_verified'] is True, c
    assert c['pr'] == 451, c
    return 'parses sha / ancestor_verified / pr from a ·-joined block'


def test_parse_tolerates_newline_separated_block():
    body = 'Done.\nsha: DEADBEEF1234\nancestor_verified: TRUE\npr: 12\n'
    c = vrc.parse_citation(body)
    assert c['sha'] == 'deadbeef1234', c   # lowercased
    assert c['ancestor_verified'] is True, c
    assert c['pr'] == 12, c
    return 'newline-separated, mixed-case block parses; sha lowercased'


def test_parse_ignores_unlabeled_hex_and_short_sha():
    # A bare hex run in prose is NOT a citation (must be labeled `sha:`), and
    # a labeled but too-short (<7) hex does not satisfy the SHA field.
    assert vrc.parse_citation('random abcdef0 token, no label')['sha'] is None
    assert vrc.parse_citation('sha: abc123 (only 6 hex)')['sha'] is None
    return 'unlabeled hex ignored; <7-hex labeled sha rejected'


def test_parse_missing_fields_are_none():
    c = vrc.parse_citation('just prose, no block at all')
    assert c == {'sha': None, 'ancestor_verified': None, 'pr': None}, c
    return 'absent fields all None'


# ─── 2. verify — fails closed on every schema gap ────────────────────────────

def test_verify_missing_sha_fails():
    ok, reason = vrc.verify('merged — confirmed, trust me', repo='.', base='origin/main')
    assert ok is False, reason
    assert 'no SHA citation' in reason, reason
    return 'no SHA → FAIL (the core DoD: unbacked flip is not verified)'


def test_verify_missing_pr_fails():
    ok, reason = vrc.verify('sha: a1b2c3d · ancestor_verified: true')
    assert ok is False and 'pr' in reason.lower(), reason
    return 'missing pr → FAIL'


def test_verify_missing_ancestor_field_fails():
    ok, reason = vrc.verify('sha: a1b2c3d · pr: #7')
    assert ok is False and 'ancestor_verified' in reason, reason
    return 'missing ancestor_verified → FAIL'


def test_verify_ancestor_false_in_comment_fails():
    ok, reason = vrc.verify('sha: a1b2c3d · ancestor_verified: false · pr: #7')
    assert ok is False and 'false' in reason.lower(), reason
    return 'comment says ancestor_verified:false → FAIL'


def test_verify_recomputes_and_rejects_lying_claim():
    """THE lock: a comment claiming ancestor_verified:true for a SHA git says
    is NOT an ancestor must FAIL. The self-asserted boolean is never trusted."""
    orig = vrc.is_ancestor
    vrc.is_ancestor = lambda sha, base='origin/main', repo='.': False
    try:
        ok, reason = vrc.verify(GOOD_BLOCK)
    finally:
        vrc.is_ancestor = orig
    assert ok is False, reason
    assert 'NOT an ancestor' in reason, reason
    return 'claim=true but git says not-ancestor → FAIL (does not trust claim)'


def test_verify_passes_when_git_confirms_ancestry():
    orig = vrc.is_ancestor
    vrc.is_ancestor = lambda sha, base='origin/main', repo='.': True
    try:
        ok, reason = vrc.verify(GOOD_BLOCK)
    finally:
        vrc.is_ancestor = orig
    assert ok is True, reason
    assert 'verified' in reason, reason
    return 'complete block + git confirms ancestry → PASS'


# ─── 3. is_ancestor — real git, real merge-base (integration) ────────────────

def test_is_ancestor_real_git():
    """Drive the actual `git merge-base --is-ancestor` against a throwaway repo:
    an ancestor commit is True, an unmerged branch commit is False, and a
    fabricated SHA (git exit 128) fails closed to False."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        assert _git(repo, 'init', '-q').returncode == 0
        (repo / 'a.txt').write_text('a', encoding='utf-8')
        _git(repo, 'add', '-A')
        _git(repo, 'commit', '-q', '-m', 'A')
        _git(repo, 'branch', '-M', 'main')
        sha_a = _git(repo, 'rev-parse', 'HEAD').stdout.strip()

        # Second commit on main — sha_a is now an ancestor of main.
        (repo / 'b.txt').write_text('b', encoding='utf-8')
        _git(repo, 'add', '-A')
        _git(repo, 'commit', '-q', '-m', 'B')

        # A commit on an unmerged branch is NOT an ancestor of main.
        _git(repo, 'checkout', '-q', '-b', 'feature')
        (repo / 'c.txt').write_text('c', encoding='utf-8')
        _git(repo, 'add', '-A')
        _git(repo, 'commit', '-q', '-m', 'C')
        sha_c = _git(repo, 'rev-parse', 'HEAD').stdout.strip()

        assert vrc.is_ancestor(sha_a, 'main', str(repo)) is True, 'A must be ancestor of main'
        assert vrc.is_ancestor(sha_c, 'main', str(repo)) is False, 'unmerged C must not be'
        assert vrc.is_ancestor('deadbeefdeadbeef', 'main', str(repo)) is False, \
            'fabricated SHA must fail closed (git exit 128)'
    return 'real merge-base: ancestor=True, unmerged=False, fake=False (fail-closed)'


# ─── 4. CLI surface (subprocess) — exit codes 0 / 1 / 2 ──────────────────────

def _run_cli(args, cwd=None):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, timeout=60, cwd=cwd,
    )


def test_cli_no_source_is_usage_error():
    r = _run_cli([])
    assert r.returncode == 2, (r.returncode, r.stderr[:300])
    return 'no --comment/--comment-file → exit 2 (argparse required group)'


def test_cli_bad_comment_exits_1():
    r = _run_cli(['--comment', 'merged, confirmed'])
    assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)
    assert 'FAIL' in r.stdout, r.stdout
    return 'unbacked comment → exit 1'


def test_cli_valid_ancestor_exits_0():
    """End-to-end through the CLI against a real repo built on disk."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _git(repo, 'init', '-q')
        (repo / 'a.txt').write_text('a', encoding='utf-8')
        _git(repo, 'add', '-A')
        _git(repo, 'commit', '-q', '-m', 'A')
        _git(repo, 'branch', '-M', 'main')
        sha = _git(repo, 'rev-parse', 'HEAD').stdout.strip()
        comment = f'Merged. sha: {sha} · ancestor_verified: true · pr: #99'
        r = _run_cli(['--comment', comment, '--repo', str(repo), '--base', 'main'])
    assert r.returncode == 0, (r.returncode, r.stdout, r.stderr)
    assert 'PASS' in r.stdout, r.stdout
    return 'real SHA + --base main → exit 0'


CONTRACTS = [
    ('parse.extracts_all_fields', test_parse_extracts_all_fields),
    ('parse.tolerates_newlines', test_parse_tolerates_newline_separated_block),
    ('parse.ignores_unlabeled_and_short', test_parse_ignores_unlabeled_hex_and_short_sha),
    ('parse.missing_fields_none', test_parse_missing_fields_are_none),
    ('verify.missing_sha_fails', test_verify_missing_sha_fails),
    ('verify.missing_pr_fails', test_verify_missing_pr_fails),
    ('verify.missing_ancestor_field_fails', test_verify_missing_ancestor_field_fails),
    ('verify.ancestor_false_fails', test_verify_ancestor_false_in_comment_fails),
    ('verify.recomputes_rejects_lying_claim', test_verify_recomputes_and_rejects_lying_claim),
    ('verify.passes_when_git_confirms', test_verify_passes_when_git_confirms_ancestry),
    ('is_ancestor.real_git', test_is_ancestor_real_git),
    ('cli.no_source_exit_2', test_cli_no_source_is_usage_error),
    ('cli.bad_comment_exit_1', test_cli_bad_comment_exits_1),
    ('cli.valid_ancestor_exit_0', test_cli_valid_ancestor_exits_0),
]

for name, fn in CONTRACTS:
    check(name, fn)

passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')

bar = '=' * 76
print(bar)
print('  VERIFY_RECONCILE_COMMENT — SCHEMA INTEGRITY / DOES-NOT-TRUST-CLAIM')
print(bar)
for name, status, detail in results:
    marker = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {marker}  {name:44} {detail}')
print('-' * 76)
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print('-' * 76)
print()
print('Source of test: OCR-128 (executable verify-reconcile-comment gate) —')
print('locks that the gate asserts schema integrity and recomputes ancestry')
print('rather than trusting a comment\'s self-asserted ancestor_verified.')

sys.exit(0 if failed == 0 else 1)
