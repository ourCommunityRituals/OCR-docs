#!/usr/bin/env python3
"""
identity_contract_check.py
==========================
Enforces "The Choice" contracts declared in OCR-docs/docs/CHOICE-INVARIANTS.md.

Every spoke declares `identity_mode:` in its CLAUDE.md. This checker reads
that declaration (or an explicit --identity-mode) and runs the matching
contract:

  anonymous -> Anonymous Contract  (A-1..A-8)
  named     -> Identity Contract   (I-1..I-8)
  both      -> Anonymous + Identity + Bridge Contract (B-1..B-7)
  internal  -> no identity contract (universal checks only)

Most rules in CHOICE-INVARIANTS.md are behavioral and cannot be fully
proven by a static hub-side scan. This checker is deliberately conservative:

  FAIL  unambiguous violation - CI blocks
  WARN  needs human review - printed, does NOT block
  INFO  rule acknowledged, not statically checkable from the hub

FAIL is reserved for the genuinely unambiguous cross-coupling cases so the
gate never flakes. Everything softer is WARN/INFO, mirroring the honest
"manual review" style of check_brain_contract.py.

Escape hatch: a FAIL-capable scan (A-7 named-identity coupling, I-4
insecure cookie) is suppressed for a given occurrence when that line, or
the line directly above it, carries a `ccr: allow <rule>` pragma -- e.g.
`ccr: allow A-7`. This mirrors security_gate.py's `security-gate: allow`
mechanism: a legitimate occurrence (a test fixture, a comment) stays
green without forcing obfuscated source. Pragmas are auditable in code
review and should carry a why-comment.

Exit: 0 = no FAIL, 1 = at least one FAIL, 2 = execution error.
"""
import argparse
import re
import sys
from pathlib import Path

PASS, WARN, FAIL, INFO = 'PASS', 'WARN', 'FAIL', 'INFO'

EXCLUDE_DIRS = {'node_modules', '.git', 'dist', 'build', '.next', '.venv',
                'venv', '__pycache__', 'coverage', '.ocr-standards', '.github'}
CODE_SUFFIXES = {'.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.py'}
CONFIG_SUFFIXES = {'.toml', '.json', '.jsonc'}
SCHEMA_GLOBS = ('**/migrations/*.sql', '**/schema.ts', '**/schema.sql',
                '**/d1-schema.sql')

# Importing a named-auth SDK or referencing a named-identity column is an
# unambiguous violation for a pure-anonymous product (see brain check
# check_identity_layer_contract, which uses the same forbidden set).
NAMED_AUTH_TOKENS = ['firebase/auth', 'firebase-admin/auth', 'next-auth',
                     '@auth0/', 'firebase_auth_user_id', 'spotify_user_id',
                     'named_contributor']
PII_COLUMN_TOKENS = ['email', 'phone', 'first_name', 'last_name',
                     'full_name', 'date_of_birth', 'ssn']
ATTRIBUTION_TOKENS = ['contributor', 'created_by', 'attributed_to',
                      'submitted_by', 'curator', 'display_name']
TTL_TOKENS = ['expires_at', 'expires', 'ttl', 'retention', 'purge_after']
INSECURE_COOKIE_TOKENS = ['httponly: false', 'httponly:false',
                          'httponly = false']

# A FAIL-capable occurrence is suppressed when its line, or the line
# directly above, carries `ccr: allow <rule>` (e.g. `ccr: allow A-7`).
PRAGMA_RE = re.compile(r'ccr:\s*allow\s+([a-z0-9-]+)')


def iter_files(root: Path, suffixes):
    for f in root.rglob('*'):
        if not f.is_file():
            continue
        if any(p in EXCLUDE_DIRS for p in f.parts):
            continue
        if suffixes and f.suffix.lower() not in suffixes:
            continue
        yield f


def grep(root: Path, needles, suffixes=CODE_SUFFIXES) -> dict[str, list[str]]:
    """Case-insensitive substring search. Returns {needle: [relpaths]}."""
    found: dict[str, list[str]] = {}
    lowered = [(n, n.lower()) for n in needles]
    for f in iter_files(root, suffixes):
        try:
            text = f.read_text(encoding='utf-8', errors='ignore').lower()
        except Exception:
            continue
        for orig, low in lowered:
            if low in text:
                found.setdefault(orig, []).append(str(f.relative_to(root)))
    return found


def _pragma_allows(low_lines: list[str], idx: int, rule: str) -> bool:
    """True if line `idx`, or the line directly above it, carries a
    `ccr: allow <rule>` pragma for this rule id."""
    for j in (idx, idx - 1):
        if j < 0:
            continue
        m = PRAGMA_RE.search(low_lines[j])
        if m and m.group(1) == rule:
            return True
    return False


def scan_tokens(root: Path, needles, rule: str,
                suffixes=CODE_SUFFIXES) -> tuple[dict[str, list[str]], int]:
    """Substring search with CCR pragma suppression, for FAIL-capable rules.

    An occurrence is suppressed when its line, or the line directly above,
    carries `ccr: allow <rule>`. Returns ({needle: [relpaths]}, n_suppressed).
    """
    found: dict[str, list[str]] = {}
    suppressed = 0
    rule = rule.lower()
    lowered = [(n, n.lower()) for n in needles]
    for f in iter_files(root, suffixes):
        try:
            low_lines = f.read_text(encoding='utf-8',
                                    errors='ignore').lower().splitlines()
        except Exception:
            continue
        for i, line in enumerate(low_lines):
            for orig, low in lowered:
                if low in line:
                    if _pragma_allows(low_lines, i, rule):
                        suppressed += 1
                    else:
                        found.setdefault(orig, []).append(
                            str(f.relative_to(root)))
    for k in found:
        found[k] = sorted(set(found[k]))
    return found, suppressed


def schema_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for g in SCHEMA_GLOBS:
        out += [p for p in root.glob(g)
                if p.is_file() and not any(d in p.parts for d in EXCLUDE_DIRS)]
    return out


def schema_pii_hits(root: Path) -> list[str]:
    hits: list[str] = []
    for sf in schema_files(root):
        try:
            txt = sf.read_text(encoding='utf-8', errors='ignore').lower()
        except Exception:
            continue
        for tok in PII_COLUMN_TOKENS:
            if re.search(r'\b' + re.escape(tok) + r'\b', txt):
                hits.append(f'{tok} @ {sf.name}')
    return hits


def detect_mode(repo: Path) -> str | None:
    claude = repo / 'CLAUDE.md'
    if not claude.exists():
        return None
    m = re.search(r'identity_mode:\s*(anonymous|named|both|internal|none)',
                  claude.read_text(encoding='utf-8', errors='ignore'), re.I)
    return m.group(1).lower() if m else None


# ---------------------------------------------------------------------------
# Contracts - each check returns (rule, status, detail)
# ---------------------------------------------------------------------------

def anonymous_checks(repo: Path, strict_no_named: bool):
    """Anonymous Contract A-1..A-8.

    strict_no_named is True for a pure-anonymous product (named-identity
    coupling is a hard FAIL) and False for a `both` product (named identity
    is allowed; the Bridge Contract governs separation instead).
    """
    results = []
    pii = schema_pii_hits(repo)

    # A-1 - no PII in the main event database.
    if pii:
        results.append(('A-1', WARN,
                         'PII-shaped columns in schema - confirm they live in '
                         f'FORMS_DB, not the main event DB: {pii[:5]}'))
    else:
        results.append(('A-1', PASS, 'no PII-shaped columns in schema files'))

    # A-2 - PII lives in a separate database.
    forms = grep(repo, ['FORMS_DB', 'forms_db'], CODE_SUFFIXES | CONFIG_SUFFIXES)
    if forms:
        results.append(('A-2', PASS, 'separate forms/PII database binding present'))
    else:
        results.append(('A-2', INFO,
                         'no FORMS_DB binding found - not required unless the '
                         'product stores opt-in PII'))

    # A-3 / A-7 - no named-identity coupling (FAIL-capable; pragma-aware).
    named, suppressed = scan_tokens(repo, NAMED_AUTH_TOKENS, 'A-7')
    sup = f' ({suppressed} suppressed by ccr:allow)' if suppressed else ''
    if named:
        detail = '; '.join(f'{k}: {v[:2]}' for k, v in named.items())
        if strict_no_named:
            results.append(('A-7', FAIL,
                             f'anonymous product couples to named identity: '
                             f'{detail}{sup}'))
        else:
            results.append(('A-7', WARN,
                             'named-identity references present - allowed under '
                             f'the Bridge Contract; verify layer separation: '
                             f'{detail}{sup}'))
    else:
        results.append(('A-7', PASS, f'no named-identity coupling found{sup}'))

    # A-4 - every PII column has an expiration.
    if pii:
        ttl = grep(repo, TTL_TOKENS, CODE_SUFFIXES | {'.sql'})
        if ttl:
            results.append(('A-4', PASS, 'retention/TTL columns present alongside PII'))
        else:
            results.append(('A-4', WARN,
                             'PII columns present but no expires_at/ttl/retention '
                             'column found - opt-in PII must have a TTL'))
    else:
        results.append(('A-4', PASS, 'no PII columns - TTL not applicable'))

    # A-6 - a cleanup job runs on a schedule.
    cron = grep(repo, ['scheduled', 'cron', 'lifecycle'],
                CODE_SUFFIXES | CONFIG_SUFFIXES)
    if cron:
        results.append(('A-6', INFO,
                         'scheduled handler present - confirm it scrubs expired PII'))
    else:
        results.append(('A-6', INFO,
                         'no scheduled handler found - required only once opt-in '
                         'PII exists'))

    # A-5 / A-8 - not statically checkable from the hub.
    results.append(('A-5', INFO,
                     'PII encryption-at-rest - verify in code review / infra config'))
    results.append(('A-8', INFO,
                     'scans must be counted by the hour (scan_bucket YYYY-MM-DDTHH) '
                     '- verify in the scan handler'))
    return results


def identity_checks(repo: Path):
    """Identity Contract I-1..I-8."""
    results = []

    # I-1 - every contribution is attributed.
    attr = grep(repo, ATTRIBUTION_TOKENS, CODE_SUFFIXES | {'.sql'})
    if attr:
        results.append(('I-1', PASS,
                         f'attribution fields present: {sorted(attr)[:4]}'))
    else:
        results.append(('I-1', WARN,
                         'no attribution field (contributor/created_by/...) found '
                         '- contributions must carry a name'))

    # I-2 - provenance is tracked.
    prov = grep(repo, ['provenance', 'source_type', 'imported_from',
                       'import_source'])
    results.append(('I-2', PASS if prov else INFO,
                    'provenance fields present' if prov else
                    'verify provenance (source + timestamp) is tracked on imports'))

    # I-4 - sessions are secure (HttpOnly cookies) (FAIL-capable; pragma-aware).
    insecure, suppressed = scan_tokens(repo, INSECURE_COOKIE_TOKENS, 'I-4')
    sup = f' ({suppressed} suppressed by ccr:allow)' if suppressed else ''
    if insecure:
        detail = '; '.join(f'{k}: {v[:2]}' for k, v in insecure.items())
        results.append(('I-4', FAIL,
                         f'session cookie is not HttpOnly: {detail}{sup}'))
    else:
        results.append(('I-4', PASS, f'no httpOnly:false cookie found{sup}'))

    # I-3 / I-5..I-8 - behavioral, not statically checkable.
    results.append(('I-3', INFO,
                     'roles must be earned by action, not self-declared - verify '
                     'role-grant logic'))
    results.append(('I-5', INFO,
                     'identity-write actions must require a name; reads may stay '
                     'anonymous'))
    results.append(('I-6', INFO,
                     'catalog must deduplicate while preserving every contributor '
                     '- verify dedup keeps attribution'))
    results.append(('I-7', INFO,
                     'no platform lock-in - verify Spotify / Apple / CSV are all '
                     'supported'))
    results.append(('I-8', INFO,
                     'document platform limitations honestly (e.g. Spotify user '
                     'caps)'))
    return results


def bridge_checks(repo: Path):
    """Bridge Contract B-1..B-7 - behavioral; reported for human review."""
    return [
        ('B-1', INFO, 'check-in must always offer Named / Anonymous / Skip'),
        ('B-2', INFO, 'named data -> identity layer, anonymous data -> anonymous '
                      'layer; the two never cross'),
        ('B-3', WARN, 'no query may join an anonymous scan to a named person - '
                      'verify no such join exists'),
        ('B-4', INFO, 'SharedReport shows the total only, never the '
                      'named/anonymous split'),
        ('B-5', INFO, 'the choice is per-event, not per-account'),
        ('B-6', INFO, 'the default is anonymous when no choice is made'),
        ('B-7', INFO, 'past Named check-ins are immutable; the future choice '
                      'stays free'),
    ]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default='.', help='spoke repo root')
    ap.add_argument('--identity-mode', default='auto',
                    help='anonymous|named|both|internal|auto '
                         '(auto reads identity_mode from CLAUDE.md)')
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f'ERROR: repo path {repo} is not a directory', file=sys.stderr)
        sys.exit(2)

    mode = args.identity_mode.lower().strip()
    if mode == 'auto':
        detected = detect_mode(repo)
        if not detected:
            print('ERROR: could not detect identity_mode - no `identity_mode:` '
                  'line in CLAUDE.md. Pass --identity-mode explicitly.',
                  file=sys.stderr)
            sys.exit(2)
        mode = detected
        print(f'Auto-detected identity_mode from CLAUDE.md: {mode}')
    if mode == 'none':
        mode = 'internal'
    if mode not in ('anonymous', 'named', 'both', 'internal'):
        print(f'ERROR: unknown identity_mode "{mode}"', file=sys.stderr)
        sys.exit(2)

    results: list[tuple[str, str, str]] = []
    if mode == 'internal':
        results.append(('-', PASS,
                         'internal product - universal checks only, no identity '
                         'contract applies'))
    if mode in ('anonymous', 'both'):
        results += anonymous_checks(repo, strict_no_named=(mode == 'anonymous'))
    if mode in ('named', 'both'):
        results += identity_checks(repo)
    if mode == 'both':
        results += bridge_checks(repo)

    fails = [r for r in results if r[1] == FAIL]
    warns = [r for r in results if r[1] == WARN]
    print('=' * 76)
    print(f'  IDENTITY CONTRACT - {mode}')
    print('=' * 76)
    for rule, status, detail in results:
        print(f'  [{status:4}] {rule:5} {detail}')
        if status == FAIL:
            print(f'::error::{rule}: {detail}')
        elif status == WARN:
            print(f'::warning::{rule}: {detail}')
    print('-' * 76)
    print(f'  {len(fails)} fail / {len(warns)} warn / {len(results)} total')
    print('-' * 76)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
