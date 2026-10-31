#!/usr/bin/env python3
"""
test_adr_index.py — Born-red logic lock for adr_index.py (the ADR index
builder that check_adr_edges.py reads).

Why this exists
===============
The edge check is only as honest as the index under it. Each case below
pins one contract from the plan's "ADR side" and "Index shape" sections:
the two declaration forms, that prose (and OSE's "Invariants touched"
bullet) never becomes an edge, status
normalisation, non-ADR files skipped, duplicate numbers fail closed, BOM
and CRLF tolerated, `--check` stale versus fresh, byte-stable output, and
the qualified-ID helpers the check imports. Every case fails if its
behaviour breaks (a parser that greps every `#N`, a section that never
ends, a status kept verbatim, a CRLF compared raw ...).

Hermetic: fixture ADR directories in a tempdir; the real script runs as a
subprocess, and the importable helpers are imported from scripts/.
`run_script_tests.py` auto-discovers this file.

Exit codes:
  0 — all contracts hold
  1 — at least one contract failed
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

SCRIPTS = Path(__file__).resolve().parent.parent / 'scripts'
SCRIPT = SCRIPTS / 'adr_index.py'
sys.path.insert(0, str(SCRIPTS))
import adr_index  # noqa: E402

TMP = None  # set in main()
_counter = [0]


def head(status='Accepted', extra=''):
    return (f'# ADR-NNN: Title\n\n**Status:** {status}\n**Date:** 2026-10-31\n'
            f'**Scope:** Fleet-wide\n{extra}\n## Context\n\nBody text.\n')


def make_dir(files: dict, binary: bool = False) -> Path:
    _counter[0] += 1
    d = TMP / f'adr{_counter[0]}'
    d.mkdir(parents=True)
    for name, content in files.items():
        p = d / name
        if isinstance(content, bytes):
            p.write_bytes(content)
        elif content is None:
            p.mkdir()
        else:
            p.write_bytes(content.encode('utf-8'))
    return d


def run(*args):
    proc = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                          capture_output=True, timeout=60)
    return (proc.returncode, proc.stdout,
            proc.stderr.decode('utf-8', errors='replace'))


def index_of(files: dict, scope='fleet'):
    code, out, err = run('--scope', scope, '--adr-dir', make_dir(files))
    if code != 0:
        raise AssertionError(f'exit {code}: {err.strip()}')
    return json.loads(out.decode('utf-8'))


def entry(files: dict, name: str, scope='fleet'):
    for a in index_of(files, scope)['adrs']:
        if a['file'] == name:
            return a
    raise AssertionError(f'{name} not in index')


def expect(actual, want, what=''):
    if actual != want:
        raise AssertionError(f'{what} expected {want!r}, got {actual!r}')


def decl(a):
    return a['declared'], a['enforced_by'], a['none_reason']


F = 'ADR-001-x.md'

# ─── Declaration forms ───────────────────────────────────────────────────────


def t_form1_header_line():
    a = entry({F: head(extra='**Enforced-by:** invariant #4, #2\n')}, F)
    expect(decl(a), (True, [2, 4], None))


def t_form1_bullet_and_case_insensitive():
    a = entry({F: head(extra='- **ENFORCED-BY:** Invariants #5 and #12\n')}, F)
    expect(decl(a), (True, [5, 12], None))


def t_form1_none_with_reason():
    a = entry({F: head(extra='**Enforced-by:** none - documentation scaffold only\n')}, F)
    expect(decl(a), (True, [], 'documentation scaffold only'))


def t_form1_none_em_dash():
    a = entry({F: head(extra='**Enforced-by:** None — process decision\n')}, F)
    expect(decl(a), (True, [], 'process decision'))


def t_form1_only_first_30_lines():
    body = head() + ('filler\n' * 40) + '**Enforced-by:** invariant #3\n'
    expect(decl(entry({F: body}, F)), (False, [], None))


def t_form1_inside_fence_ignored():
    body = head(extra='```\n**Enforced-by:** invariant #3\n```\n')
    expect(decl(entry({F: body}, F)), (False, [], None))


SECTION_2 = '\n## Enforced by invariants\n\n- **Invariant #2**\n'


def t_fence_other_char_does_not_close():
    # A ~~~ line inside a ``` block is content, not a closer; the real section
    # after the block must still count (a toggle-on-any-fence parser misses it).
    for inner in ('~~~ x', '~~~', '~~~~~~'):
        body = head() + f'\n```text\nexample:\n{inner}\n```\n' + SECTION_2
        expect(decl(entry({F: body}, F)), (True, [2], None), f'inner {inner!r}:')


def t_fence_shorter_or_suffixed_run_does_not_close():
    # Inside a 4-backtick fence, an odd number of ``` lines and a ```js line
    # are content; only the ```` line closes it.
    body = head() + ('\n````markdown\n```\n**Enforced-by:** invariant #7\n'
                     '```js\n````\n') + SECTION_2
    expect(decl(entry({F: body}, F)), (True, [2], None))


def t_fence_declarations_inside_ignored():
    # Still working: declarations inside a fence never count, for either fence
    # char, an indented fence, or an unclosed fence (which runs to EOF).
    cases = {
        'tilde': head(extra='~~~~\n**Enforced-by:** invariant #3\n~~~\n~~~~\n'),
        'indented': head(extra='   ```\n**Enforced-by:** invariant #3\n   ```\n'),
        'section': head() + '\n```\n## Enforced by invariants\n- **Invariant #3**\n```\n',
        'unclosed': head() + '\n```\n' + SECTION_2,
    }
    for name, body in cases.items():
        expect(decl(entry({F: body}, F)), (False, [], None), f'{name}:')


def t_form2_section_stops_at_next_heading():
    body = head() + (
        '\n## Enforced by invariants\n\n'
        '- **Invariant #9 (geo hierarchy)** — enforced in spec 9.\n'
        '- **Invariant #2** - one place.\n'
        '- see also #11 in prose (not a bullet of the form)\n'
        '* **invariant #4** star bullet\n'
        '### Notes\n\n'
        '- **Invariant #17** under a lower-level heading: not in the section\n'
        '## Consequences\n\n'
        '- **Invariant #21** later section: never an edge\n')
    expect(decl(entry({F: body}, F)), (True, [2, 4, 9], None))


def t_form2_heading_case_insensitive():
    body = head() + '\n### ENFORCED BY INVARIANTS\n\n- **Invariant #16**\n'
    expect(decl(entry({F: body}, F)), (True, [16], None))


TOUCHED = '- **Invariants touched:** #2 `x` (live), #4 (partial), #5, #16\n'


def t_touched_bullet_alone_is_not_an_edge():
    # "touched" is not "enforced by": an ADR with only this bullet is undeclared.
    a = entry({F: head(extra=TOUCHED)}, F)
    expect(decl(a), (False, [], None))


def t_touched_bullet_case_variants_not_an_edge():
    extra = '**INVARIANTS TOUCHED:** #7, #3\n- **Invariants touched**: #8\n'
    expect(decl(entry({F: head(extra=extra)}, F)), (False, [], None))


def t_touched_bullet_beside_section_adds_nothing():
    body = head(extra='- **Invariants touched:** #1, #21\n') + (
        '\n## Enforced by invariants\n\n- **Invariant #16** (the one that enforces it)\n')
    expect(decl(entry({F: body}, F)), (True, [16], None))


def t_touched_bullet_beside_header_adds_nothing():
    extra = '**Enforced-by:** invariant #2\n' + TOUCHED
    expect(decl(entry({F: head(extra=extra)}, F)), (True, [2], None))


def t_forms_union():
    body = head(extra='**Enforced-by:** invariant #2, #5\n') + (
        '\n## Enforced by invariants\n\n- **Invariant #9**\n- **Invariant #2**\n')
    expect(decl(entry({F: body}, F)), (True, [2, 5, 9], None))


def t_prose_mention_is_not_an_edge():
    body = head() + (
        '\nThis decision relates to invariant #11 and Invariant #12.\n'
        'Enforced-by: invariant #13 (not bold, so not the form)\n'
        '- **Invariant #11** a bullet outside any Enforced-by section\n'
        '<!-- **Enforced-by:** invariant #14 -->\n')
    expect(decl(entry({F: body}, F)), (False, [], None))


# ─── Malformed declarations fail closed ──────────────────────────────────────


def _exit_for(files):
    return run('--scope', 'fleet', '--adr-dir', make_dir(files))[0]


def t_malformed_enforced_by_no_numbers():
    expect(_exit_for({F: head(extra='**Enforced-by:** TBD\n')}), 2, 'exit')


def t_malformed_none_without_reason():
    expect(_exit_for({F: head(extra='**Enforced-by:** none\n')}), 2, 'exit')


def t_malformed_two_enforced_by_lines():
    extra = '**Enforced-by:** invariant #2\n**Enforced-by:** invariant #4\n'
    expect(_exit_for({F: head(extra=extra)}), 2, 'exit')


def t_malformed_none_plus_numbers():
    body = head(extra='**Enforced-by:** none - nothing\n') + (
        '\n## Enforced by invariants\n\n- **Invariant #2**\n')
    expect(_exit_for({F: body}), 2, 'exit')


def t_malformed_empty_section():
    body = head() + '\n## Enforced by invariants\n\nTo be assigned.\n'
    expect(_exit_for({F: body}), 2, 'exit')


# ─── Status ──────────────────────────────────────────────────────────────────

STATUS_CASES = [
    ('- **Status:** Accepted', 'Accepted'),
    ('**Status:** ACCEPTED', 'Accepted'),
    ('**Status:** Accepted - in flight', 'Accepted'),
    ('**Status:** Accepted — implementation pending', 'Accepted'),
    ('**Status:** Accepted (ratified 2026-09-29)', 'Accepted'),
    ('**Status:** Superseded by ADR-014', 'Superseded'),
    ('**status:** proposed', 'Proposed'),
    ('**Status:** **Deprecated**', 'Deprecated'),
]


def t_status_variants():
    files = {f'ADR-{i + 1:03d}-s.md': f'# T\n\n{line}\n\nBody.\n'
             for i, (line, _) in enumerate(STATUS_CASES)}
    got = {a['file']: a['status'] for a in index_of(files)['adrs']}
    for i, (line, want) in enumerate(STATUS_CASES):
        expect(got[f'ADR-{i + 1:03d}-s.md'], want, f'status of {line!r}:')


def t_status_heading_form():
    expect(entry({F: '# T\n\n## Status\n\nProposed (draft)\n\n## Context\n'}, F)['status'],
           'Proposed')


def t_status_missing_is_null():
    expect(entry({F: '# T\n\nNo header here.\n'}, F)['status'], None)


# ─── Directory handling ──────────────────────────────────────────────────────


def t_non_adr_files_skipped():
    files = {
        'README.md': head(extra='**Enforced-by:** invariant #1\n'),
        'template.md': head(extra='**Enforced-by:** invariant #N, #M\n'),
        'ADR-RECONCILIATION-PROCESS.md': head(),
        'ADR-01-short.md': head(),
        'ADR-0004-long.md': head(),
        'ADR-005-notes.txt': head(),
        'ADR-006-dir.md': None,  # a directory, not a file
        'ADR-002-real.md': head(),
        'ADR-010-real.md': head(),
    }
    ids = [a['id'] for a in index_of(files)['adrs']]
    expect(ids, ['fleet:ADR-002', 'fleet:ADR-010'], 'ids:')


def t_duplicate_numbers_exit_2():
    code, _, err = run('--scope', 'fleet', '--adr-dir',
                       make_dir({'ADR-003-a.md': head(), 'ADR-003-b.md': head()}))
    expect(code, 2, 'exit')
    if 'duplicate' not in err:
        raise AssertionError(f'stderr does not name the duplicate: {err!r}')


def t_bom_and_crlf():
    lf = head(status='ACCEPTED', extra='**Enforced-by:** invariant #2, #4\n') + (
        '\n## Enforced by invariants\n\n- **Invariant #9**\n## Next\n- **Invariant #11**\n')
    crlf_bom = b'\xef\xbb\xbf' + lf.replace('\n', '\r\n').encode('utf-8')
    idx = index_of({'ADR-001-lf.md': lf, 'ADR-002-crlf.md': crlf_bom})['adrs']
    a, b = idx[0], idx[1]
    expect((b['status'],) + decl(b), (a['status'],) + decl(a), 'CRLF+BOM vs LF:')
    expect((b['status'],) + decl(b), ('Accepted', True, [2, 4, 9], None), 'CRLF+BOM:')


def t_bom_on_first_line_status():
    raw = b'\xef\xbb\xbf**Status:** Proposed\r\n\r\n# T\r\n'
    expect(entry({F: raw}, F)['status'], 'Proposed')


def t_undecodable_file_exit_2():
    expect(_exit_for({F: b'**Status:** Accepted\n\xff\xfe bad\n'}), 2, 'exit')


def t_missing_dir_exit_2():
    expect(run('--scope', 'fleet', '--adr-dir', TMP / 'does-not-exist')[0], 2, 'exit')
    a_file = make_dir({F: head()}) / F
    expect(run('--scope', 'fleet', '--adr-dir', a_file)[0], 2, 'a file as --adr-dir:')


def _run_patched(patch: str, adr_dir: Path):
    """Run main() in a fresh interpreter with one pathlib method made to raise,
    to provoke OS errors (permission denied) portably."""
    code = ('import sys, pathlib\n'
            f'sys.path.insert(0, {str(SCRIPTS)!r})\n'
            'import adr_index\n'
            'def boom(self, *a, **k):\n'
            '    raise PermissionError(13, "Permission denied", str(self))\n'
            f'pathlib.Path.{patch} = boom\n'
            f'sys.exit(adr_index.main(["--scope", "fleet", "--adr-dir", {str(adr_dir)!r}]))\n')
    proc = subprocess.run([sys.executable, '-c', code], capture_output=True,
                          text=True, encoding='utf-8', errors='replace', timeout=60)
    return proc.returncode, proc.stderr


def t_os_errors_exit_2_not_traceback():
    # An OS error must be a tool error (2), never a traceback (exit 1), which a
    # --check caller would misread as "stale".
    d = make_dir({F: head()})
    for patch in ('iterdir', 'read_bytes', 'is_dir'):
        code, err = _run_patched(patch, d)
        expect(code, 2, f'{patch} raising: exit')
        if 'Traceback' in err or 'FATAL' not in err:
            raise AssertionError(f'{patch} raising: stderr {err.strip()!r}')


def t_undecodable_check_file_exit_2():
    d = make_dir({F: head()})
    bad = TMP / f'bad{_counter[0]}.json'
    bad.write_bytes(b'{\xff\xfe}\n')
    code, _, err = run('--scope', 'fleet', '--adr-dir', d, '--check', bad)
    expect(code, 2, 'exit')
    if 'Traceback' in err:
        raise AssertionError(f'traceback: {err.strip()!r}')


def t_bad_scope_exit_2():
    d = make_dir({F: head()})
    for scope in ('OSE', '1ose', 'ose:x', ''):
        expect(run('--scope', scope, '--adr-dir', d)[0], 2, f'scope {scope!r}:')


def t_bad_args_exit_2():
    expect(run('--adr-dir', make_dir({F: head()}))[0], 2, 'missing --scope:')
    d = make_dir({F: head()})
    expect(run('--scope', 'fleet', '--adr-dir', d, '--out', TMP / 'o.json',
               '--check', TMP / 'o.json')[0], 2, '--out with --check:')


def t_cold_start_empty_dir_beside_populated():
    empty = index_of({'README.md': '# readme\n'})
    expect(empty, {'schema': 1, 'scope': 'fleet', 'adrs': []}, 'empty:')
    populated = index_of({F: head()})
    expect(len(populated['adrs']), 1, 'populated count:')


# ─── Index shape and byte stability ──────────────────────────────────────────


def t_index_shape_exact():
    idx = index_of({'ADR-009-geo.md': head(extra='**Enforced-by:** invariant #9, #2, #4\n')},
                   scope='ose')
    expect(list(idx), ['schema', 'scope', 'adrs'], 'top keys:')
    expect(idx['adrs'], [{
        'id': 'ose:ADR-009', 'number': 9, 'file': 'ADR-009-geo.md',
        'status': 'Accepted', 'declared': True, 'enforced_by': [2, 4, 9],
        'none_reason': None}], 'entries:')
    expect(list(idx['adrs'][0]), ['id', 'number', 'file', 'status', 'declared',
                                  'enforced_by', 'none_reason'], 'entry key order:')
    adr_index.validate_index(idx, expected_scope='ose')


def t_byte_stable_output():
    files = {'ADR-012-z.md': head(extra='**Enforced-by:** invariant #3\n'),
             'ADR-002-a.md': head(status='Proposed'),
             'ADR-007-m.md': head(extra='**Enforced-by:** none - why\n')}
    d = make_dir(files)
    c1, out1, _ = run('--scope', 'fleet', '--adr-dir', d)
    c2, out2, _ = run('--scope', 'fleet', '--adr-dir', d)
    expect((c1, c2), (0, 0), 'exits:')
    expect(out1, out2, 'two runs:')
    if b'\r' in out1:
        raise AssertionError('stdout contains a CR')
    if not out1.endswith(b'}\n') or out1.endswith(b'\n\n'):
        raise AssertionError('stdout must end with exactly one trailing newline')
    numbers = [a['number'] for a in json.loads(out1)['adrs']]
    expect(numbers, [2, 7, 12], 'sorted by number:')
    expect(out1.decode('utf-8'), adr_index.render_index(json.loads(out1)), 'indent=2 form:')
    out_path = TMP / f'out{_counter[0]}' / 'idx.json'
    expect(run('--scope', 'fleet', '--adr-dir', d, '--out', out_path)[0], 0, '--out exit:')
    expect(out_path.read_bytes(), out1, '--out bytes vs stdout:')


def t_check_fresh_stale_crlf_missing():
    d = make_dir({F: head(extra='**Enforced-by:** invariant #2\n')})
    idx = TMP / f'check{_counter[0]}.json'
    expect(run('--scope', 'ose', '--adr-dir', d, '--out', idx)[0], 0, '--out:')
    expect(run('--scope', 'ose', '--adr-dir', d, '--check', idx)[0], 0, 'fresh:')
    # A Windows checkout's CRLF copy of the same file is still fresh.
    idx.write_bytes(idx.read_bytes().replace(b'\n', b'\r\n'))
    expect(run('--scope', 'ose', '--adr-dir', d, '--check', idx)[0], 0, 'CRLF copy:')
    # Change the ADR: the stored index is now stale.
    (d / F).write_text(head(extra='**Enforced-by:** invariant #2, #4\n'), encoding='utf-8')
    expect(run('--scope', 'ose', '--adr-dir', d, '--check', idx)[0], 1, 'stale:')
    # Wrong scope against the same file is stale too.
    expect(run('--scope', 'fleet', '--adr-dir', d, '--check', idx)[0], 1, 'scope differs:')
    expect(run('--scope', 'ose', '--adr-dir', d, '--check', TMP / 'nope.json')[0], 2,
           'missing --check file:')


# ─── Importable API the edge check uses ──────────────────────────────────────


def t_qualified_id_api():
    for good, want in (('ose:ADR-009', ('ose', 9)), ('fleet:ADR-002', ('fleet', 2)),
                       ('my-spoke2:ADR-120', ('my-spoke2', 120))):
        if not adr_index.QUALIFIED_ID_RE.fullmatch(good):
            raise AssertionError(f'{good!r} should match')
        expect(adr_index.parse_qualified_id(good), want, f'parse {good!r}:')
    for bad in ('ADR-009', 'ose:ADR-9', 'ose:ADR-0009', 'OSE:ADR-009', 'ose:adr-009',
                '1ose:ADR-009', 'ose: ADR-009', 'ose:ADR-009 ', 'ourSharedEvents/docs/adr/ADR-009.md',
                None, 9):
        if adr_index.parse_qualified_id(bad) is not None:
            raise AssertionError(f'{bad!r} should not parse')
        if isinstance(bad, str) and adr_index.QUALIFIED_ID_RE.fullmatch(bad):
            raise AssertionError(f'{bad!r} should not fullmatch')
    expect(adr_index.qualify('ose', 9), 'ose:ADR-009', 'qualify:')
    expect(adr_index.qualify('fleet', 120), 'fleet:ADR-120', 'qualify:')
    for scope, number in (('OSE', 1), ('ose', 1000), ('ose', -1), ('ose', '9'), ('', 1)):
        try:
            adr_index.qualify(scope, number)
        except ValueError:
            continue
        raise AssertionError(f'qualify({scope!r}, {number!r}) should raise')


def t_parse_helpers_match_cli():
    text = head(status='ACCEPTED', extra='**Enforced-by:** invariant #4, #2\n')
    expect(adr_index.parse_status(text), 'Accepted', 'parse_status:')
    expect(adr_index.parse_enforced_by(text), (True, [2, 4], None), 'parse_enforced_by:')
    a = entry({F: text}, F)
    expect(adr_index.parse_adr_text(text),
           {k: a[k] for k in ('status', 'declared', 'enforced_by', 'none_reason')},
           'helper vs CLI:')
    d = make_dir({F: text, 'ADR-002-b.md': head()})
    expect(adr_index.build_index(d, 'fleet'), index_of({F: text, 'ADR-002-b.md': head()}),
           'build_index vs CLI:')


def t_validate_index_rejects_bad_shapes():
    good = {'schema': 1, 'scope': 'ose', 'adrs': [
        {'id': 'ose:ADR-009', 'number': 9, 'file': 'f.md', 'status': 'Accepted',
         'declared': True, 'enforced_by': [2], 'none_reason': None}]}
    adr_index.validate_index(good, expected_scope='ose')
    bads = [
        ('scope mismatch', good, 'fleet'),
        ('schema 2', dict(good, schema=2), None),
        ('adrs not list', dict(good, adrs={}), None),
        ('id/number mismatch', dict(good, adrs=[dict(good['adrs'][0], number=8)]), None),
        ('id wrong scope', dict(good, adrs=[dict(good['adrs'][0], id='fleet:ADR-009')]), None),
        ('missing key', dict(good, adrs=[{'id': 'ose:ADR-009', 'number': 9}]), None),
        ('enforced_by strings', dict(good, adrs=[dict(good['adrs'][0], enforced_by=['2'])]), None),
        ('duplicate number', dict(good, adrs=[good['adrs'][0], good['adrs'][0]]), None),
        ('not a dict', [], None),
    ]
    for name, data, scope in bads:
        try:
            adr_index.validate_index(data, expected_scope=scope)
        except adr_index.AdrIndexError:
            continue
        raise AssertionError(f'validate_index accepted: {name}')


# ─── Invariant sweep: every ADR in one directory is read, not only the first ─


def t_sweep_every_entry():
    files = {
        'ADR-001-h.md': head(extra='**Enforced-by:** invariant #1\n'),
        'ADR-002-n.md': head(status='Superseded by ADR-004', extra='**Enforced-by:** none - superseded\n'),
        'ADR-003-s.md': head(status='ACCEPTED') + '\n## Enforced by invariants\n\n- **Invariant #3**\n## End\n- **Invariant #30**\n',
        'ADR-004-t.md': '# T\n\n- **Status:** Proposed\n- **Invariants touched:** #4, #40\n',
        'ADR-005-p.md': head() + '\nMentions invariant #5 in prose only.\n',
        'README.md': 'Lists ADR-001..ADR-005 and invariant #99.\n',
    }
    want = {
        'fleet:ADR-001': ('Accepted', True, [1], None),
        'fleet:ADR-002': ('Superseded', True, [], 'superseded'),
        'fleet:ADR-003': ('Accepted', True, [3], None),
        'fleet:ADR-004': ('Proposed', False, [], None),
        'fleet:ADR-005': ('Accepted', False, [], None),
    }
    got = {a['id']: (a['status'],) + decl(a) for a in index_of(files)['adrs']}
    wrong = [f'{k}: want {v}, got {got.get(k)}' for k, v in want.items() if got.get(k) != v]
    if set(got) != set(want):
        wrong.append(f'ids {sorted(got)} != {sorted(want)}')
    if wrong:
        raise AssertionError('; '.join(wrong))


CASES = [(name[2:], fn) for name, fn in list(globals().items())
         if name.startswith('t_') and callable(fn)]


def main() -> int:
    global TMP
    passed = failed = 0
    with tempfile.TemporaryDirectory() as td:
        TMP = Path(td)
        for name, fn in CASES:
            try:
                fn()
            except Exception as e:  # any failure, including a crash, is a FAIL
                failed += 1
                print(f'  [FAIL] {name}: {type(e).__name__}: {e}')
            else:
                passed += 1
    print('-' * 76)
    print(f'  {passed} pass / {failed} fail  (total {passed + failed} contracts)')
    print('-' * 76)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
