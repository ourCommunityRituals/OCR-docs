#!/usr/bin/env python3
"""
test_check_adr_edges.py — Born-red logic lock for check_adr_edges.py (the
two-sided ADR <-> invariant edge check).

Why this exists
===============
A gate earns trust only if it is first shown FAILING against a deliberately
broken fixture. Every rule E1-E6 gets its own born-red case (expect exit 1 and
exactly that rule in the report), E7 is shown as a GAP that does not fail, and
a born-green baseline shows the permitted shapes pass. Around them sit the
fail-closed contracts (exit 2), the invariant sweep (several bad edges of
different rules in one fixture, every one reported), the cold-start twins, and
the contract-drift case (the same ADR directory checked in memory and through
its generated index file gives the same result: one parser, two entry paths).

`run_script_tests.py` auto-discovers this file (glob `test_*.py`).

Hermetic: every case builds a fixture brain, fixture ADR directories, a
fixture scope map, ratchet and index files in a tempdir and runs the real
check as a subprocess. Nothing reads the real registry.

Exit codes:
  0 — all contracts hold
  1 — at least one contract failed
"""
import copy
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
GUARD = SCRIPTS / 'check_adr_edges.py'
INDEXER = SCRIPTS / 'adr_index.py'


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------
def adr_text(num, status='Accepted', enforced=None, title='Decision',
             body='Context: invariant #11 is mentioned in prose only.\n'):
    """An ADR file in the fleet header style. enforced=None -> undeclared."""
    lines = [f'# ADR-{num:03d}: {title}', '', f'**Status:** {status}',
             '**Date:** 2026-10-01']
    if enforced is not None:
        lines.append(f'**Enforced-by:** {enforced}')
    lines += ['', '## Context', '', body]
    return '\n'.join(lines) + '\n'


def idx_entry(scope, num, status='Accepted', declared=True, enforced_by=(),
              none_reason=None):
    return {'id': f'{scope}:ADR-{num:03d}', 'number': num,
            'file': f'ADR-{num:03d}-fixture.md', 'status': status,
            'declared': declared, 'enforced_by': sorted(enforced_by),
            'none_reason': none_reason}


def baseline():
    """A born-green tree exercising every permitted shape."""
    return {
        'invariants': [
            {'id': 1, 'name': 'one', 'status': 'live',
             'references': {'adr': ['fleet:ADR-001'],
                            'adr_coordination': 'prose key, never an edge'}},
            {'id': 2, 'name': 'two', 'status': 'partial',
             'references': {'adr': ['ose:ADR-009']}},
            # no references key at all; carried on the ratchet
            {'id': 3, 'name': 'three', 'status': 'live'},
            # retired, no ADR, not on the ratchet, but named by ose:ADR-009
            {'id': 4, 'name': 'four', 'status': 'retired'},
        ],
        'fleet': {
            'ADR-001-first.md': adr_text(1, enforced='invariant #1'),
            'ADR-002-second.md': adr_text(2),               # undeclared
            'README.md': '# ADRs\n**Enforced-by:** invariant #99\n',
            'template.md': adr_text(0, enforced='invariant #98'),
        },
        'scope_map': {
            'fleet': {'adr_dir': 'docs/adr'},
            'ose': {'repo': 'ourSharedEvents', 'adr_dir': 'docs/adr',
                    'index': 'brain/adr-indexes/ose.json'},
        },
        'indexes': {
            'ose.json': {'schema': 1, 'scope': 'ose', 'adrs': [
                idx_entry('ose', 9, enforced_by=[2, 4]),
                idx_entry('ose', 10, declared=False),  # spoke: E5-exempt
            ]},
        },
        'ratchet': {'frozen_max_id': 4, 'invariants_without_adr': [3],
                    'adrs_undeclared': ['fleet:ADR-002']},
    }


def inv(tree, iid):
    for i in tree['invariants']:
        if i['id'] == iid:
            return i
    raise KeyError(iid)


def ose_adr(tree, num):
    for a in tree['indexes']['ose.json']['adrs']:
        if a['number'] == num:
            return a
    raise KeyError(num)


def write_tree(root: Path, tree: dict):
    """Materialise a tree dict. Returns (brain, repo_root, ratchet_path)."""
    brain = root / 'brain'
    (brain / 'adr-indexes').mkdir(parents=True)
    # YAML files written as JSON (JSON is valid YAML).
    (brain / 'architectural-invariants.yaml').write_text(
        json.dumps({'schema_version': '1.2.0',
                    'invariants': tree['invariants']}), encoding='utf-8')
    reg = {'org': 'fixture', 'products': []}
    if tree.get('scope_map') is not None:
        reg['adr_scopes'] = tree['scope_map']
    (brain / 'product-registry.yaml').write_text(json.dumps(reg),
                                                 encoding='utf-8')
    adr_dir = root / 'docs' / 'adr'
    adr_dir.mkdir(parents=True)
    for name, text in tree['fleet'].items():
        data = text if isinstance(text, bytes) else text.encode('utf-8')
        (adr_dir / name).write_bytes(data)
    for name, data in tree.get('indexes', {}).items():
        body = data if isinstance(data, str) else json.dumps(data, indent=2)
        (brain / 'adr-indexes' / name).write_text(body, encoding='utf-8')
    ratchet = root / 'ratchet.json'
    r = tree['ratchet']
    ratchet.write_text(r if isinstance(r, str) else json.dumps(r),
                       encoding='utf-8')
    return brain, root, ratchet


def run_check(brain, root, ratchet, report):
    proc = subprocess.run(
        [sys.executable, str(GUARD), '--brain', str(brain),
         '--repo-root', str(root), '--ratchet', str(ratchet),
         '--report-path', str(report)],
        capture_output=True, text=True, encoding='utf-8', timeout=60)
    rep = None
    if report.is_file():
        rep = json.loads(report.read_text(encoding='utf-8'))
    return proc.returncode, proc.stdout + proc.stderr, rep


# ---------------------------------------------------------------------------
# Case mutators (each returns a tree)
# ---------------------------------------------------------------------------
def m(fn):
    def build():
        t = baseline()
        fn(t)
        return t
    return build


def _e1_scope(t):
    inv(t, 1)['references']['adr'].append('ow:ADR-001')


def _e1_number(t):
    inv(t, 1)['references']['adr'].append('fleet:ADR-099')


def _e2_bare(t):
    inv(t, 2)['references']['adr'].append('ADR-002')


def _e2_legacy_string(t):
    # a legacy path string: reported by E2, never a crash; fleet:ADR-001 then
    # names #1 without #1 naming it back, so E4 fires too.
    inv(t, 1)['references']['adr'] = 'docs/adr/ADR-001-first.md'


def _e3(t):
    inv(t, 1)['references']['adr'].append('ose:ADR-009')  # 009 declares [2,4]


def _e4_not_listed(t):
    ose_adr(t, 9)['enforced_by'] = [2, 3, 4]  # #3 does not list ose:ADR-009


def _e4_missing_invariant(t):
    ose_adr(t, 9)['enforced_by'] = [2, 4, 77]  # #77 does not exist


def _e5_not_on_list(t):
    t['ratchet']['adrs_undeclared'] = []


def _e5_declared_but_listed(t):
    t['fleet']['ADR-002-second.md'] = adr_text(
        2, enforced='none - a process decision, no runtime rule')


def _e5_stale_entry(t):
    t['ratchet']['adrs_undeclared'].append('fleet:ADR-050')


def _e6_missing(t):
    t['ratchet']['invariants_without_adr'] = []


def _e6_stale(t):
    t['ratchet']['invariants_without_adr'] = [2, 3]  # #2 has an ADR


def _e6_above_ceiling(t):
    t['invariants'].append({'id': 5, 'name': 'five', 'status': 'live'})
    t['ratchet']['invariants_without_adr'] = [3, 5]  # 5 > frozen_max_id 4


def _e6_new_without_adr(t):
    t['invariants'].append({'id': 5, 'name': 'five', 'status': 'live'})


def _e6_retired_on_list(t):
    t['ratchet']['invariants_without_adr'] = [3, 4]


def _e7(t):
    t['fleet']['ADR-001-first.md'] = adr_text(
        1, status='Superseded by ADR-002', enforced='invariant #1')


def _retired_named(t):
    inv(t, 4)['references'] = {'adr': []}  # named by ose:ADR-009, lists nothing


def _index_unmapped(t):
    t['indexes']['ow.json'] = {'schema': 1, 'scope': 'ow', 'adrs': []}


def _index_fleet_stored(t):
    t['indexes']['fleet.json'] = {'schema': 1, 'scope': 'fleet', 'adrs': []}


def _empty_adr_list_on_ratchet(t):
    inv(t, 3)['references'] = {'adr': []}


def _empty_adr_list_off_ratchet(t):
    inv(t, 3)['references'] = {'adr': []}
    t['ratchet']['invariants_without_adr'] = []


def _empty_ratchet(t):
    # every live invariant carries an ADR and every fleet ADR is declared
    inv(t, 3)['references'] = {'adr': ['fleet:ADR-002']}
    t['fleet']['ADR-002-second.md'] = adr_text(2, enforced='invariant #3')
    t['ratchet'] = {'frozen_max_id': 4, 'invariants_without_adr': [],
                    'adrs_undeclared': []}


def _empty_spoke_index(t):
    inv(t, 2)['references'] = {'adr': ['fleet:ADR-001']}
    t['fleet']['ADR-001-first.md'] = adr_text(1, enforced='invariant #1, #2')
    t['indexes']['ose.json']['adrs'] = []


def _empty_fleet_dir(t):
    t['fleet'] = {'README.md': '# none yet\n'}
    inv(t, 1)['references'] = {'adr': ['ose:ADR-009']}
    ose_adr(t, 9)['enforced_by'] = [1, 2, 4]
    t['ratchet']['adrs_undeclared'] = []


def _crlf_bom_fleet(t):
    text = adr_text(1, status='ACCEPTED', enforced='invariant #1')
    t['fleet']['ADR-001-first.md'] = (
        b'\xef\xbb\xbf' + text.replace('\n', '\r\n').encode('utf-8'))


# --- tool errors (exit 2) --------------------------------------------------
def _no_index_scope(t):
    del t['scope_map']['ose']['index']


def _scope_mismatch(t):
    t['indexes']['ose.json']['scope'] = 'ow'
    for a in t['indexes']['ose.json']['adrs']:
        a['id'] = a['id'].replace('ose:', 'ow:')


def _no_scope_map(t):
    t['scope_map'] = None


def _fleet_index_named(t):
    t['scope_map']['fleet']['index'] = 'brain/adr-indexes/fleet.json'


def _index_missing_file(t):
    del t['indexes']['ose.json']


def _index_malformed(t):
    t['indexes']['ose.json'] = '{"schema": 1, "scope": "ose", "adrs": [ '


def _index_bad_entry(t):
    ose_adr(t, 9)['enforced_by'] = ['#2']


def _ratchet_malformed(t):
    t['ratchet'] = 'not json'


def _ratchet_bad_ceiling(t):
    t['ratchet']['frozen_max_id'] = '29'


def _ratchet_missing_key(t):
    del t['ratchet']['adrs_undeclared']


def _duplicate_fleet_number(t):
    t['fleet']['ADR-001-again.md'] = adr_text(1, enforced='invariant #1')


def _references_not_mapping(t):
    inv(t, 1)['references'] = ['fleet:ADR-001']


# (name, build, expected_exit, expected failing checks, expected gap checks)
CASES = [
    ('green: baseline (prose key, no references, retired, spoke undeclared, '
     'non-ADR files)', baseline, 0, set(), set()),
    ('red E1: scope not in adr_scopes', m(_e1_scope), 1, {'E1_unresolved'}, set()),
    ('red E1: number absent from the scope index', m(_e1_number), 1,
     {'E1_unresolved'}, set()),
    ('red E2: bare ADR-NNN in the list', m(_e2_bare), 1, {'E2_bare'}, set()),
    ('red E2: legacy path string reported, not crashed', m(_e2_legacy_string),
     1, {'E2_bare', 'E4_one_sided_adr_to_inv'}, set()),
    ('red E3: invariant lists an ADR that does not name it', m(_e3), 1,
     {'E3_one_sided_inv_to_adr'}, set()),
    ('red E4: ADR names an invariant that does not list it',
     m(_e4_not_listed), 1, {'E4_one_sided_adr_to_inv'}, set()),
    ('red E4: ADR names an invariant that does not exist',
     m(_e4_missing_invariant), 1, {'E4_one_sided_adr_to_inv'}, set()),
    ('red E5: undeclared fleet ADR not on adrs_undeclared',
     m(_e5_not_on_list), 1, {'E5_undeclared_fleet'}, set()),
    ('red E5: declared fleet ADR still on adrs_undeclared',
     m(_e5_declared_but_listed), 1, {'E5_undeclared_fleet'}, set()),
    ('red E5: adrs_undeclared names no fleet ADR', m(_e5_stale_entry), 1,
     {'E5_undeclared_fleet'}, set()),
    ('red E6: invariant without ADR not on the ratchet', m(_e6_missing), 1,
     {'E6_ratchet'}, set()),
    ('red E6: ratchet entry that now has an ADR', m(_e6_stale), 1,
     {'E6_ratchet'}, set()),
    ('red E6: ratchet id above frozen_max_id', m(_e6_above_ceiling), 1,
     {'E6_ratchet'}, set()),
    ('red E6: new invariant above the ceiling without an ADR',
     m(_e6_new_without_adr), 1, {'E6_ratchet'}, set()),
    ('red E6: retired invariant left on the ratchet', m(_e6_retired_on_list),
     1, {'E6_ratchet'}, set()),
    ('gap E7: superseded ADR listed is a GAP, exit 0', m(_e7), 0, set(),
     {'E7_status'}),
    ('green: retired invariant named by an ADR, listing nothing',
     m(_retired_named), 0, set(), set()),
    ('red INDEX: index file whose scope is not in adr_scopes',
     m(_index_unmapped), 1, {'INDEX_map'}, set()),
    ('red INDEX: a stored fleet index (generated is not stored)',
     m(_index_fleet_stored), 1, {'INDEX_map'}, set()),
    ('twin green: empty adr list on the ratchet (beside populated)',
     m(_empty_adr_list_on_ratchet), 0, set(), set()),
    ('twin red: empty adr list off the ratchet', m(_empty_adr_list_off_ratchet),
     1, {'E6_ratchet'}, set()),
    ('twin green: empty ratchet (beside populated baseline)',
     m(_empty_ratchet), 0, set(), set()),
    ('twin green: empty spoke adrs list', m(_empty_spoke_index), 0, set(),
     set()),
    ('twin green: fleet dir with no ADRs', m(_empty_fleet_dir), 0, set(), set()),
    ('green: CRLF + BOM + ACCEPTED fleet ADR', m(_crlf_bom_fleet), 0, set(),
     set()),
    ('exit 2: non-fleet scope with no index file', m(_no_index_scope), 2,
     None, None),
    ('exit 2: index JSON scope differs from its map key', m(_scope_mismatch),
     2, None, None),
    ('exit 2: product-registry has no adr_scopes', m(_no_scope_map), 2, None,
     None),
    ('exit 2: fleet names a stored index', m(_fleet_index_named), 2, None,
     None),
    ('exit 2: index file missing', m(_index_missing_file), 2, None, None),
    ('exit 2: index file not JSON', m(_index_malformed), 2, None, None),
    ('exit 2: index entry malformed', m(_index_bad_entry), 2, None, None),
    ('exit 2: ratchet not JSON', m(_ratchet_malformed), 2, None, None),
    ('exit 2: ratchet frozen_max_id not an integer', m(_ratchet_bad_ceiling),
     2, None, None),
    ('exit 2: ratchet missing adrs_undeclared', m(_ratchet_missing_key), 2,
     None, None),
    ('exit 2: duplicate fleet ADR number', m(_duplicate_fleet_number), 2, None,
     None),
    ('exit 2: references is not a mapping', m(_references_not_mapping), 2,
     None, None),
]

RULE_NAMES = ['E1_unresolved', 'E2_bare', 'E3_one_sided_inv_to_adr',
              'E4_one_sided_adr_to_inv', 'E5_undeclared_fleet', 'E6_ratchet',
              'E7_status', 'INDEX_map']


# ---------------------------------------------------------------------------
# Composite contracts
# ---------------------------------------------------------------------------
def sweep_case(tmp: Path):
    """Several bad edges of different rules in one fixture: every one must be
    reported, not only the first."""
    t = baseline()
    inv(t, 1)['references']['adr'] += ['ow:ADR-001', 'fleet:ADR-099',
                                       'ose:ADR-009']   # E1, E1, E3
    inv(t, 2)['references']['adr'].append('docs/adr/ADR-009.md')  # E2
    ose_adr(t, 9)['enforced_by'] = [1, 2, 3, 4, 77]  # E4 #3, E4 #77 (#1 ok)
    t['ratchet']['adrs_undeclared'] = []            # E5 fleet:ADR-002
    t['invariants'].append({'id': 6, 'name': 'six', 'status': 'live'})  # E6
    t['ratchet']['invariants_without_adr'] = [3, 30]  # E6 above ceiling
    t['indexes']['ow.json'] = {'schema': 1, 'scope': 'ow', 'adrs': []}
    want = {
        ('E1_unresolved', '#1', 'ow:ADR-001'),
        ('E1_unresolved', '#1', 'fleet:ADR-099'),
        ('E2_bare', '#2', 'docs/adr/ADR-009.md'),
        ('E4_one_sided_adr_to_inv', 'ose:ADR-009', '#3'),
        ('E4_one_sided_adr_to_inv', 'ose:ADR-009', '#77'),
        ('E5_undeclared_fleet', 'fleet:ADR-002', 'not on adrs_undeclared'),
        ('E6_ratchet', '#6', 'no references.adr'),
        ('E6_ratchet', '#30', 'frozen_max_id'),
        ('E6_ratchet', '#30', 'does not exist'),
        ('INDEX_map', 'adr-indexes/ow.json', "'ow'"),
    }
    brain, root, ratchet = write_tree(tmp, t)
    code, out, rep = run_check(brain, root, ratchet, tmp / 'report.json')
    errors = []
    if code != 1:
        errors.append(f'expected exit 1, got {code}')
    if rep is None:
        return errors + ['no report written'], out
    fails = rep.get('failures', [])
    for check, who, frag in sorted(want):
        if not any(f['check'] == check and f['invariant_or_adr'] == who
                   and frag in f['detail'] for f in fails):
            errors.append(f'missing finding {check} {who} ~{frag!r}')
    # #1 IS named back by ose:ADR-009 in this fixture, so no E3 for it.
    if any(f['check'] == 'E3_one_sided_inv_to_adr' for f in fails):
        errors.append('unexpected E3 finding')
    if len(fails) != len(want):
        errors.append(f'expected {len(want)} findings, got {len(fails)}: '
                      f'{[(f["check"], f["invariant_or_adr"]) for f in fails]}')
    # report shape, so open_drift_ticket.py can route it later
    if rep.get('product_id') != 'brain':
        errors.append(f'product_id is {rep.get("product_id")!r}')
    summ = rep.get('summary', {})
    if summ.get('failed') != len(fails):
        errors.append(f'summary.failed {summ.get("failed")} != {len(fails)}')
    for f in fails:
        if set(f) != {'check', 'invariant_or_adr', 'detail'}:
            errors.append(f'failure entry keys {sorted(f)}')
            break
    return errors, out


def stdout_case(tmp: Path):
    """One [PASS]/[FAIL]/[GAP] line per rule, the skipped counts printed."""
    t = baseline()
    _e7(t)
    _e3(t)
    brain, root, ratchet = write_tree(tmp, t)
    code, out, _ = run_check(brain, root, ratchet, tmp / 'report.json')
    errors = []
    lines = out.splitlines()
    for name in RULE_NAMES:
        hits = [ln for ln in lines if name in ln
                and any(mk in ln for mk in ('[PASS]', '[FAIL]', '[GAP]'))]
        if len(hits) != 1:
            errors.append(f'{name}: {len(hits)} status lines')
    for want in ('[FAIL]  E3_one_sided_inv_to_adr', '[GAP]   E7_status',
                 'skipped 2 undeclared ADR', 'pass /'):
        if want not in out:
            errors.append(f'stdout lacks {want!r}')
    if code != 1:
        errors.append(f'expected exit 1, got {code}')
    return errors, out


def drift_case(tmp: Path):
    """Contract drift: the same ADR directory checked in memory (as the fleet
    scope) and through its generated index file (as a spoke scope, written
    by the real adr_index.py CLI) must give the same findings."""
    adrs = {
        'ADR-001-a.md': adr_text(1, enforced='invariant #1, #2'),
        # OSE-style section form, CRLF + BOM
        'ADR-002-b.md': ('﻿# ADR-002: B\r\n\r\n- **Status:** ACCEPTED\r\n'
                         '\r\n## Enforced by invariants\r\n\r\n'
                         '- **Invariant #3** - the rule\r\n'
                         '- **Invariant #9** - not in the registry\r\n'
                         '\r\n## Notes\r\n\r\n- **Invariant #2** outside\r\n'),
        'ADR-003-c.md': adr_text(3, status='Proposed',
                                 enforced='invariant #2'),
        'ADR-004-d.md': ('# ADR-004: D\n\n**Status:** Accepted - in flight\n'
                         '**Enforced-by:** invariant #1, #3\n'),
        'README.md': '# not an ADR\n',
    }

    def tree_for(scope):
        q = f'{scope}:ADR-'
        t = {
            'invariants': [
                # #1: two-sided with 001 and 004; #2 lists 002 (E3: 002 is #3,#9)
                {'id': 1, 'status': 'live',
                 'references': {'adr': [q + '001', q + '004']}},
                {'id': 2, 'status': 'live',
                 'references': {'adr': [q + '001', q + '002', q + '003']}},
                {'id': 3, 'status': 'live', 'references': {'adr': [q + '002']}},
                # 004 names #3, #3 does not list 004 -> E4; 002 names #9 -> E4
            ],
            'ratchet': {'frozen_max_id': 3, 'invariants_without_adr': [],
                        'adrs_undeclared': []},
            'indexes': {},
        }
        if scope == 'fleet':
            t['fleet'] = adrs
            t['scope_map'] = {'fleet': {'adr_dir': 'docs/adr'}}
        else:
            t['fleet'] = {}
            t['scope_map'] = {'fleet': {'adr_dir': 'docs/adr'},
                              scope: {'index': 'brain/adr-indexes/ose.json'}}
        return t

    results = {}
    errors = []
    for scope in ('fleet', 'ose'):
        root = tmp / scope
        t = tree_for(scope)
        brain, root, ratchet = write_tree(root, t)
        if scope == 'ose':
            src = root / 'spoke-adr'
            src.mkdir()
            for name, text in adrs.items():
                (src / name).write_bytes(text.encode('utf-8'))
            gen = subprocess.run(
                [sys.executable, str(INDEXER), '--scope', 'ose', '--adr-dir',
                 str(src), '--out', str(brain / 'adr-indexes' / 'ose.json')],
                capture_output=True, text=True, timeout=60)
            if gen.returncode != 0:
                return [f'adr_index.py --out failed: {gen.stderr.strip()}'], ''
        code, out, rep = run_check(brain, root, ratchet, root / 'report.json')
        if rep is None:
            return [f'{scope}: no report (exit {code})'], out
        norm = lambda items: sorted(  # noqa: E731
            (f['check'], f['invariant_or_adr'].replace(f'{scope}:', 'S:'),
             f['detail'].replace(f'{scope}:', 'S:')) for f in items)
        results[scope] = (code, norm(rep['failures']), norm(rep['gaps']), out)
    a, b = results['fleet'], results['ose']
    if a[:3] != b[:3]:
        errors.append(f'in-memory vs index differ:\n      fleet={a[:3]}\n'
                      f'      ose  ={b[:3]}')
    # And the shared result is the one the fixture was built to produce.
    want_checks = {('E3_one_sided_inv_to_adr', '#2'),
                   ('E4_one_sided_adr_to_inv', 'S:ADR-002'),
                   ('E4_one_sided_adr_to_inv', 'S:ADR-004')}
    got = {(c, w) for c, w, _ in a[1]}
    if got != want_checks:
        errors.append(f'fleet findings {sorted(got)} != {sorted(want_checks)}')
    if {(c, w) for c, w, _ in a[2]} != {('E7_status', '#2')}:
        errors.append(f'fleet gaps {a[2]}')
    if a[0] != 1:
        errors.append(f'expected exit 1, got {a[0]}')
    return errors, a[3] + b[3]


def bad_args_case(tmp: Path):
    proc = subprocess.run([sys.executable, str(GUARD), '--brain', str(tmp)],
                          capture_output=True, text=True, timeout=60)
    return ([] if proc.returncode == 2
            else [f'expected exit 2, got {proc.returncode}']), proc.stderr


def main() -> int:
    passed = failed = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for idx, (name, build, want_exit, want_fail, want_gap) in enumerate(CASES):
            case_dir = tmp / f'case{idx:02d}'
            brain, root, ratchet = write_tree(case_dir, copy.deepcopy(build()))
            code, out, rep = run_check(brain, root, ratchet,
                                       case_dir / 'report.json')
            problems = []
            if code != want_exit:
                problems.append(f'expected exit {want_exit}, got {code}')
            if want_fail is not None:
                if rep is None:
                    problems.append('no report written')
                else:
                    got_f = {f['check'] for f in rep['failures']}
                    got_g = {g['check'] for g in rep['gaps']}
                    if got_f != want_fail:
                        problems.append(f'failing checks {sorted(got_f)} != '
                                        f'{sorted(want_fail)}')
                    if got_g != want_gap:
                        problems.append(f'gap checks {sorted(got_g)} != '
                                        f'{sorted(want_gap)}')
            elif 'FATAL' not in out:
                problems.append('exit-2 case printed no FATAL line')
            if problems:
                failed += 1
                print(f'  [FAIL] {name}: ' + '; '.join(problems))
                print('    ' + out.strip().replace('\n', '\n    '))
            else:
                passed += 1

        for name, fn in (('sweep: every bad edge reported', sweep_case),
                         ('stdout: one status line per rule', stdout_case),
                         ('contract drift: dir vs generated index', drift_case),
                         ('bad args: missing --repo-root', bad_args_case)):
            d = tmp / name.split(':')[0].replace(' ', '_')
            d.mkdir()
            problems, out = fn(d)
            if problems:
                failed += 1
                print(f'  [FAIL] {name}:')
                for p in problems:
                    print(f'    - {p}')
                print('    ' + out.strip().replace('\n', '\n    '))
            else:
                passed += 1

    print('-' * 76)
    print(f'  {passed} pass / {failed} fail  (total {passed + failed} contracts)')
    print('-' * 76)
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
