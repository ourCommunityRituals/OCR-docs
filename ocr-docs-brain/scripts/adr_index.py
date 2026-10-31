#!/usr/bin/env python3
"""
adr_index.py — Build the ADR index for one ADR directory: each ADR's
qualified ID, status, and the invariants it declares it is enforced by.

Why this exists
===============
An ADR and the invariant that enforces it must point at each other, and a
deterministic check (check_adr_edges.py) verifies both sides agree. That
check never reads a spoke's code or prose (rule R3: only IDs, status and
enforced-by cross a repo boundary). It reads an INDEX, and this script is
the single implementation that builds one, for the fleet directory
(`docs/adr/`, built in memory by the check) and for spoke snapshots
(`ocr-docs-brain/adr-indexes/<scope>.json`, committed).

Qualified ID
============
`<scope>:ADR-<NNN>` — scope is lower-case `[a-z][a-z0-9-]*`, NNN exactly
three digits (`fleet:ADR-002`, `ose:ADR-009`). Only files named
`ADR-NNN-*.md` are ADRs; anything else in the directory (`README.md`,
`template.md`, `ADR-RECONCILIATION-PROCESS.md`) is skipped. Two files with
the same number in one directory is a tool error (exit 2).

How an ADR declares its invariants (exactly these forms, nothing else)
=====================================================================
1. Header line, anywhere in the first 30 lines:
       **Enforced-by:** invariant #2, #4
       **Enforced-by:** none - <one-line reason>
2. OSE's existing section: a `## Enforced by invariants` heading (any
   level), then every following bullet that starts `- **Invariant #N`,
   until the next heading of any level.

No other text counts, so a passing mention of `#11` in prose can never
become an edge. In particular OSE's `- **Invariants touched:** #N` header
bullet is NOT a declaration: it says an ADR touches an invariant, not that
the invariant enforces it. Labels match case-insensitively; a leading `- ` bullet is
allowed on the header forms; lines inside ``` fences never count. An ADR
with none of the forms is `declared: false`. A malformed declaration (an
Enforced-by line with neither `#N` nor `none - <reason>`, two Enforced-by
lines, `none` alongside numbers, an empty Enforced-by section) is a tool
error: the index fails closed rather than guessing.

Status is read from `**Status:**` (optionally as a `- ` bullet) in the
first 30 lines, or failing that from the first non-blank line under a
`## Status` heading, and normalised to its first word in title case
(`ACCEPTED` -> `Accepted`, `Accepted — implementation pending` ->
`Accepted`). No status line gives `null`.

Files are read as UTF-8, tolerating a BOM and CRLF. Output is byte-stable:
JSON, indent 2, ADRs sorted by number, `\\n` newlines, trailing newline.

Usage:
  python3 adr_index.py --scope fleet --adr-dir docs/adr            # stdout
  python3 adr_index.py --scope ose --adr-dir <dir> --out FILE      # write
  python3 adr_index.py --scope ose --adr-dir <dir> --check FILE    # verify

Public API (imported by check_adr_edges.py from the same directory):
  build_index(adr_dir, scope) -> dict, render_index(index) -> str,
  parse_adr_text(text) -> dict, parse_status(text), parse_enforced_by(text),
  QUALIFIED_ID_RE, SCOPE_RE, parse_qualified_id(s), qualify(scope, number),
  validate_index(data, expected_scope=None), AdrIndexError.

Exit codes:
  0 — index printed / written, or --check found the file up to date
  1 — --check found the file stale (differs from what would be generated)
  2 — tool error (bad arguments, missing directory, duplicate ADR number,
      malformed declaration, undecodable file, --check file missing or
      unreadable)
"""
import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = 1
HEADER_LINES = 30

# ─── Identity ────────────────────────────────────────────────────────────────
#: A scope name: lower-case, starts with a letter.
SCOPE_RE = re.compile(r'[a-z][a-z0-9-]*')
#: A qualified ADR id. Use with .fullmatch(): group 1 = scope, group 2 = NNN.
QUALIFIED_ID_RE = re.compile(r'([a-z][a-z0-9-]*):ADR-(\d{3})')
#: An ADR file name: `ADR-NNN-<anything>.md`. Group 1 = NNN.
ADR_FILE_RE = re.compile(r'ADR-(\d{3})-.+\.md')


class AdrIndexError(Exception):
    """A tool error: the index cannot be built or trusted (exit 2)."""


def parse_qualified_id(value):
    """Return (scope, number) for a qualified ID string, else None.

    Fullmatch semantics: `ose:ADR-009` -> ('ose', 9); `ADR-009`,
    `ose:ADR-9`, `OSE:ADR-009`, `ose:ADR-0009`, non-strings -> None.
    """
    if not isinstance(value, str):
        return None
    m = QUALIFIED_ID_RE.fullmatch(value)
    if not m:
        return None
    return m.group(1), int(m.group(2))


def qualify(scope, number):
    """Return the qualified ID for (scope, number): qualify('ose', 9) ->
    'ose:ADR-009'. Raises ValueError for an invalid scope or number."""
    if not isinstance(scope, str) or not SCOPE_RE.fullmatch(scope):
        raise ValueError(f'invalid ADR scope {scope!r}: must match [a-z][a-z0-9-]*')
    if isinstance(number, bool) or not isinstance(number, int) or not 0 <= number <= 999:
        raise ValueError(f'invalid ADR number {number!r}: must be an int 0-999')
    return f'{scope}:ADR-{number:03d}'


# ─── Text parsing ────────────────────────────────────────────────────────────
# CommonMark fences: up to 3 spaces of indent, then 3+ of one char (` or ~).
# A backtick opener's info string may not contain a backtick.
_FENCE_OPEN_RE = re.compile(r' {0,3}(?:(`{3,})[^`]*|(~{3,}).*)$')
_FENCE_CLOSE_RE = re.compile(r' {0,3}(`{3,}|~{3,})[ \t]*$')
_HEADING_RE = re.compile(r'#{1,6}\s')
_STATUS_LINE_RE = re.compile(r'\s*(?:[-*]\s+)?\*\*Status:?\*\*:?\s*(.*)', re.I)
_STATUS_HEADING_RE = re.compile(r'#{1,6}\s+Status\s*:?\s*$', re.I)
_ENFORCED_LINE_RE = re.compile(r'\s*(?:[-*]\s+)?\*\*Enforced[- ]by:?\*\*:?\s*(.*)', re.I)
_ENFORCED_HEADING_RE = re.compile(r'#{1,6}\s+Enforced by invariants\b', re.I)
_INVARIANT_BULLET_RE = re.compile(r'\s*[-*]\s+\*\*Invariant\s+#(\d+)', re.I)
_NONE_RE = re.compile(r'none\b\s*(?:[-–—:]\s*(.*))?', re.I)
_HASH_NUM_RE = re.compile(r'#(\d+)')
_WORD_RE = re.compile(r'[A-Za-z]+')


def normalise_text(text):
    """Strip a leading BOM and turn CRLF / CR into LF."""
    if text.startswith('﻿'):
        text = text[1:]
    return text.replace('\r\n', '\n').replace('\r', '\n')


def _unfenced_lines(text):
    """Yield (index, line) for every line outside a fenced code block.

    CommonMark rules: a fence opens on 3+ backticks or tildes (up to 3
    spaces of indent) and closes only on a line of the SAME character, at
    least as long as the opener, with nothing after it but whitespace. A
    shorter run or the other character stays inside the block; an unclosed
    fence runs to the end of the file.
    """
    fence = None  # (char, length) of the open fence, or None
    for i, line in enumerate(normalise_text(text).split('\n')):
        if fence is None:
            m = _FENCE_OPEN_RE.match(line)
            if m:
                run = m.group(1) or m.group(2)
                fence = (run[0], len(run))
                continue
            yield i, line
        else:
            m = _FENCE_CLOSE_RE.match(line)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1]:
                fence = None


def normalise_status(value):
    """First word of a status value, title case; None if there is no word."""
    m = _WORD_RE.search(value or '')
    return m.group(0).title() if m else None


def parse_status(text):
    """Return the ADR's normalised status (e.g. 'Accepted') or None."""
    lines = list(_unfenced_lines(text))
    for i, line in lines:
        if i >= HEADER_LINES:
            break
        m = _STATUS_LINE_RE.match(line)
        if m:
            return normalise_status(m.group(1))
    after_heading = False
    for _, line in lines:
        if after_heading:
            if not line.strip():
                continue
            if _HEADING_RE.match(line):
                return None
            return normalise_status(line)
        if _STATUS_HEADING_RE.match(line):
            after_heading = True
    return None


def _parse_header_line(lines):
    """Form 1. Returns None (absent) or (numbers:set, none_reason|None)."""
    found = []
    for i, line in lines:
        if i >= HEADER_LINES:
            break
        m = _ENFORCED_LINE_RE.match(line)
        if m:
            found.append(m.group(1).strip())
    if not found:
        return None
    if len(found) > 1:
        raise AdrIndexError(f'{len(found)} **Enforced-by:** lines; exactly one is allowed')
    value = found[0]
    none_m = _NONE_RE.match(value)
    if none_m:
        reason = (none_m.group(1) or '').strip()
        if not reason:
            raise AdrIndexError(
                f'**Enforced-by:** {value!r}: "none" needs a reason, '
                f'as "none - <one-line reason>"')
        return set(), reason
    nums = {int(n) for n in _HASH_NUM_RE.findall(value)}
    if not nums:
        raise AdrIndexError(
            f'**Enforced-by:** {value!r}: write "invariant #N, #M" '
            f'or "none - <one-line reason>"')
    return nums, None


def _parse_section(lines):
    """Form 2. Returns None (no heading) or the set of bullet numbers."""
    in_section = False
    seen_heading = False
    nums = set()
    for _, line in lines:
        if _HEADING_RE.match(line):
            if _ENFORCED_HEADING_RE.match(line):
                in_section = seen_heading = True
            else:
                in_section = False
            continue
        if in_section:
            m = _INVARIANT_BULLET_RE.match(line)
            if m:
                nums.add(int(m.group(1)))
    if not seen_heading:
        return None
    if not nums:
        raise AdrIndexError(
            '"Enforced by invariants" section has no "- **Invariant #N" bullet')
    return nums


def parse_enforced_by(text):
    """Return (declared: bool, enforced_by: sorted list[int], none_reason).

    Union of the two declaration forms (header line, Enforced-by section).
    Raises AdrIndexError on a malformed or contradictory declaration.
    """
    lines = list(_unfenced_lines(text))
    header = _parse_header_line(lines)
    section = _parse_section(lines)
    if header is None and section is None:
        return False, [], None
    nums = set()
    none_reason = None
    if header is not None:
        nums |= header[0]
        none_reason = header[1]
    if section is not None:
        nums |= section
    if none_reason is not None and nums:
        raise AdrIndexError(
            f'**Enforced-by:** none, but invariants {sorted(nums)} are declared '
            f'elsewhere in the file')
    return True, sorted(nums), none_reason


def parse_adr_text(text):
    """Parse one ADR's text into {status, declared, enforced_by, none_reason}."""
    declared, enforced_by, none_reason = parse_enforced_by(text)
    return {
        'status': parse_status(text),
        'declared': declared,
        'enforced_by': enforced_by,
        'none_reason': none_reason,
    }


def read_text(path):
    """Read a file as UTF-8 (BOM tolerated), CRLF normalised to LF."""
    try:
        raw = Path(path).read_bytes()
    except OSError as e:
        raise AdrIndexError(f'cannot read {path}: {e}') from e
    try:
        return normalise_text(raw.decode('utf-8-sig'))
    except UnicodeDecodeError as e:
        raise AdrIndexError(f'{path} is not valid UTF-8: {e}') from e


# ─── Index ───────────────────────────────────────────────────────────────────
def build_index(adr_dir, scope):
    """Build the index dict for every `ADR-NNN-*.md` in adr_dir.

    Raises AdrIndexError (missing or unlistable dir, unreadable or
    undecodable file, duplicate number, malformed declaration) and
    ValueError (invalid scope).
    """
    adr_dir = Path(adr_dir)
    qualify(scope, 0)  # validates the scope
    if not adr_dir.is_dir():
        raise AdrIndexError(f'ADR directory {adr_dir} does not exist or is not a directory')
    try:
        entries = sorted(adr_dir.iterdir(), key=lambda p: p.name)
    except OSError as e:
        raise AdrIndexError(f'cannot list ADR directory {adr_dir}: {e}') from e
    by_number = {}
    for f in entries:
        if not f.is_file():
            continue
        m = ADR_FILE_RE.fullmatch(f.name)
        if not m:
            continue
        number = int(m.group(1))
        if number in by_number:
            raise AdrIndexError(
                f'duplicate ADR number {number:03d} in {adr_dir}: '
                f'{by_number[number]} and {f.name}')
        by_number[number] = f.name
    adrs = []
    for number in sorted(by_number):
        name = by_number[number]
        try:
            parsed = parse_adr_text(read_text(adr_dir / name))
        except AdrIndexError as e:
            raise AdrIndexError(f'{name}: {e}') from e
        adrs.append({
            'id': qualify(scope, number),
            'number': number,
            'file': name,
            'status': parsed['status'],
            'declared': parsed['declared'],
            'enforced_by': parsed['enforced_by'],
            'none_reason': parsed['none_reason'],
        })
    return {'schema': SCHEMA_VERSION, 'scope': scope, 'adrs': adrs}


def render_index(index):
    """The byte-stable text form: JSON, indent 2, LF, trailing newline."""
    return json.dumps(index, indent=2, ensure_ascii=False) + '\n'


_ADR_KEYS = ('id', 'number', 'file', 'status', 'declared', 'enforced_by', 'none_reason')


def validate_index(data, expected_scope=None):
    """Check a loaded index has the documented shape; raise AdrIndexError
    if not. With expected_scope, its `scope` must equal it."""
    if not isinstance(data, dict):
        raise AdrIndexError('index is not a JSON object')
    if data.get('schema') != SCHEMA_VERSION:
        raise AdrIndexError(f'index schema is {data.get("schema")!r}, expected {SCHEMA_VERSION}')
    scope = data.get('scope')
    if not isinstance(scope, str) or not SCOPE_RE.fullmatch(scope):
        raise AdrIndexError(f'index scope {scope!r} is not a valid scope')
    if expected_scope is not None and scope != expected_scope:
        raise AdrIndexError(f'index scope {scope!r} does not match expected {expected_scope!r}')
    adrs = data.get('adrs')
    if not isinstance(adrs, list):
        raise AdrIndexError('index "adrs" is not a list')
    seen = set()
    for a in adrs:
        if not isinstance(a, dict) or any(k not in a for k in _ADR_KEYS):
            raise AdrIndexError(f'index entry {a!r} lacks one of {list(_ADR_KEYS)}')
        n = a['number']
        if isinstance(n, bool) or not isinstance(n, int):
            raise AdrIndexError(f'index entry {a["id"]!r}: number is not an int')
        if parse_qualified_id(a['id']) != (scope, n):
            raise AdrIndexError(f'index entry id {a["id"]!r} does not match scope/number')
        if n in seen:
            raise AdrIndexError(f'index has duplicate number {n:03d}')
        seen.add(n)
        if not isinstance(a['declared'], bool):
            raise AdrIndexError(f'index entry {a["id"]}: declared is not a bool')
        eb = a['enforced_by']
        if not isinstance(eb, list) or any(
                isinstance(x, bool) or not isinstance(x, int) for x in eb):
            raise AdrIndexError(f'index entry {a["id"]}: enforced_by is not a list of ints')
        if a['status'] is not None and not isinstance(a['status'], str):
            raise AdrIndexError(f'index entry {a["id"]}: status is not a string or null')
        if a['none_reason'] is not None and not isinstance(a['none_reason'], str):
            raise AdrIndexError(f'index entry {a["id"]}: none_reason is not a string or null')
    return data


# ─── CLI ─────────────────────────────────────────────────────────────────────
def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    ap = argparse.ArgumentParser(description='Build the ADR index for one ADR directory')
    ap.add_argument('--scope', required=True, help='scope name (fleet, ose, ...)')
    ap.add_argument('--adr-dir', required=True, help='directory holding ADR-NNN-*.md files')
    group = ap.add_mutually_exclusive_group()
    group.add_argument('--out', metavar='PATH', help='write the index to PATH')
    group.add_argument('--check', metavar='PATH',
                       help='exit 1 if PATH differs from the index that would be generated')
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code == 0 else 2

    try:
        text = render_index(build_index(Path(args.adr_dir), args.scope))
    except (AdrIndexError, ValueError, OSError) as e:
        # OSError / UnicodeDecodeError (a ValueError) must never escape as a
        # traceback with exit 1, which a --check caller would read as "stale".
        print(f'FATAL: {type(e).__name__}: {e}', file=sys.stderr)
        return 2

    if args.check:
        target = Path(args.check)
        try:
            current = read_text(target)
        except AdrIndexError as e:
            print(f'FATAL: --check {e}', file=sys.stderr)
            return 2
        if current == text:
            print(f'PASS — {target} is up to date ({args.scope}).')
            return 0
        print(f'FAIL — {target} is stale: regenerate it with '
              f'adr_index.py --scope {args.scope} --adr-dir {args.adr_dir} --out {target}')
        return 1

    if args.out:
        out = Path(args.out)
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(text)
        except OSError as e:
            print(f'FATAL: cannot write {out}: {e}', file=sys.stderr)
            return 2
        return 0

    # Write bytes so a Windows console / redirect never turns \n into \r\n.
    sys.stdout.flush()
    buffer = getattr(sys.stdout, 'buffer', None)
    if buffer is not None:
        buffer.write(text.encode('utf-8'))
        buffer.flush()
    else:
        sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
