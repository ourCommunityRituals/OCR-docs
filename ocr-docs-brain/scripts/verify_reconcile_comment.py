#!/usr/bin/env python3
"""
verify_reconcile_comment.py
===========================
Executable enforcement for the SHA-citation rule in
`docs/standards/OCR_STANDARD_reconciliationLoop.md` §4 step 2.

Why this exists
===============
The reconciliation loop requires every Done-flip comment to carry a
parseable citation block:

    sha: <7-40 hex> · ancestor_verified: true · pr: #NNN

so that a wrong status flip is *mechanically* detectable. Until this script
existed the rule was prose — an agent could write "merged — confirmed" and
flip a ticket to Done citing nothing real. The 2026-09-03 reconcile run
produced two false "merged" verdicts exactly this way: testimony, not
evidence.

This script turns verify-first from convention into a gate. Given a Done-flip
comment body it:

  1. parses the citation block field-by-field (schema *integrity*, not mere
     presence of some hex string in prose); and
  2. RE-RUNS the ancestry check itself — it never trusts the comment's own
     `ancestor_verified: true`, because the whole failure mode is a flip that
     *claims* a verification it never performed. The self-asserted boolean
     must be present (the schema demands it) AND must agree with what git
     actually reports.

It exits non-zero if the block is missing/incomplete, the SHA is not a real
7-40 hex commit id, or the SHA is not an ancestor of the base branch (default
`origin/main`) in the target repo. Per §4 step 2, board-reconciler MUST run
this before proposing any Done flip; a flip whose comment does not pass this
checker is itself a drift finding.

Design note: the git ancestry call is isolated in `is_ancestor()` so the
parse/verdict logic is unit-testable hermetically (monkeypatch), while a
separate integration test drives the real `git merge-base` against a throwaway
repo. No network, no Linear, no LLM — matches the L0 offline floor.

Exit codes:
  0 — comment carries a complete, ancestor-verified citation block
  1 — verification failed (missing/incomplete block, bad SHA, or not an ancestor)
  2 — usage error (argparse)
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

# The citation schema from OCR_STANDARD_reconciliationLoop §4 step 2:
#   sha: <7-40 hex> · ancestor_verified: true · pr: #NNN
# Each contract-bearing field is parsed on its own so the block tolerates the
# separator actually used (·, comma, newline) and surrounding prose. What is
# enforced is that each *labeled* field is present and well-formed — anchoring
# on the `sha:` label (not a bare hex run) is deliberate: it asserts the
# schema rather than pattern-matching any 7-hex token that happens to appear.
SHA_RE = re.compile(r'\bsha:\s*([0-9a-fA-F]{7,40})\b', re.IGNORECASE)
ANCESTOR_RE = re.compile(r'\bancestor_verified:\s*(true|false)\b', re.IGNORECASE)
PR_RE = re.compile(r'\bpr:\s*#?(\d+)\b', re.IGNORECASE)


def parse_citation(text: str) -> dict:
    """Extract the citation fields from a comment body.

    Returns a dict with keys `sha` (lowercased str | None),
    `ancestor_verified` (bool | None — None means the field was absent), and
    `pr` (int | None). Absent/malformed fields come back None so the caller
    can report exactly which part of the schema is missing.
    """
    text = text or ''
    sha_m = SHA_RE.search(text)
    anc_m = ANCESTOR_RE.search(text)
    pr_m = PR_RE.search(text)
    ancestor_verified = None
    if anc_m:
        ancestor_verified = anc_m.group(1).lower() == 'true'
    return {
        'sha': sha_m.group(1).lower() if sha_m else None,
        'ancestor_verified': ancestor_verified,
        'pr': int(pr_m.group(1)) if pr_m else None,
    }


def is_ancestor(sha: str, base: str = 'origin/main', repo: str = '.') -> bool:
    """True iff `sha` is an ancestor of `base` in the git repo at `repo`.

    Shells out to `git -C <repo> merge-base --is-ancestor <sha> <base>`, which
    exits 0 for ancestor, 1 for not-ancestor, and 128 for an unknown SHA/ref.
    Only exit 0 counts as verified: a fabricated or truncated commit id makes
    git error (128) and MUST fail closed, never error-through to a pass. A
    missing git binary or a timeout is likewise treated as unverified.
    """
    try:
        proc = subprocess.run(
            ['git', '-C', repo, 'merge-base', '--is-ancestor', sha, base],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as e:
        print(f'::error::git ancestry check could not run: {e}', file=sys.stderr)
        return False
    return proc.returncode == 0


def verify(comment: str, repo: str = '.', base: str = 'origin/main') -> tuple[bool, str]:
    """Verify a Done-flip comment. Returns (ok, reason).

    Fails closed on every gap in the schema, and — critically — recomputes the
    ancestry itself rather than trusting the comment's `ancestor_verified`
    claim.
    """
    c = parse_citation(comment)
    if not c['sha']:
        return False, (
            'no SHA citation — a Done flip must cite the merged commit as '
            '`sha: <7-40 hex>` (§4 step 2). An unbacked flip is not verified.'
        )
    if c['pr'] is None:
        return False, (
            f'citation missing `pr: #NNN` (found sha={c["sha"]}). The block '
            'schema is `sha · ancestor_verified · pr`; all three are required.'
        )
    if c['ancestor_verified'] is None:
        return False, (
            'citation missing `ancestor_verified: true` — the flip must attest '
            'the ancestry check was run (this script then re-checks it).'
        )
    if c['ancestor_verified'] is False:
        return False, (
            '`ancestor_verified: false` — the comment itself reports the SHA is '
            'not an ancestor of the base. Not a Done-worthy flip.'
        )
    # Never trust the self-asserted boolean: re-run the ancestry check.
    if not is_ancestor(c['sha'], base, repo):
        return False, (
            f'SHA {c["sha"]} is NOT an ancestor of {base} in {repo!r} — the '
            'comment claims `ancestor_verified: true` but git disagrees. '
            'False or premature flip.'
        )
    return True, (
        f'verified: {c["sha"]} is an ancestor of {base}; pr #{c["pr"]}.'
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description='Verify a reconcile Done-flip comment carries a valid, '
                    'ancestor-verified SHA citation '
                    '(OCR_STANDARD_reconciliationLoop §4 step 2).',
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument('--comment', help='the comment body, as a string')
    src.add_argument('--comment-file',
                     help='path to a file holding the comment body; "-" = stdin')
    ap.add_argument('--repo', default='.',
                    help='target git repo dir the SHA should live in (default: cwd)')
    ap.add_argument('--base', default='origin/main',
                    help='base ref to check ancestry against (default: origin/main)')
    args = ap.parse_args()

    if args.comment is not None:
        body = args.comment
    elif args.comment_file == '-':
        body = sys.stdin.read()
    else:
        try:
            body = Path(args.comment_file).read_text(encoding='utf-8')
        except OSError as e:
            print(f'::error::could not read --comment-file: {e}', file=sys.stderr)
            return 1

    ok, reason = verify(body, repo=args.repo, base=args.base)
    if ok:
        print(f'[verify-reconcile-comment] PASS — {reason}')
        return 0
    print(f'::error title=Unverified Done flip::{reason}', file=sys.stderr)
    print(f'[verify-reconcile-comment] FAIL — {reason}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
