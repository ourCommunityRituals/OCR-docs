#!/usr/bin/env python3
"""
check_adr_edges.py — Two-sided ADR <-> invariant edge check (brain-internal).

Why this exists
===============
An ADR records a decision; an invariant is the rule that enforces it. Until
this check, the link between the two lived in prose on one side or the other,
named no repo, and nothing verified that both sides agreed. This script makes
the link a two-sided edge and verifies it deterministically in the brain's own
CI (`brain-validate.yml`).

It is NOT part of check_brain_contract.py on purpose: that script is a
per-product conformance check each spoke runs with `--repo`, so a brain-only
rule there would run once per spoke with nothing to inspect.

Qualified IDs
=============
Every ADR has one unambiguous ID, `<scope>:ADR-<NNN>` (`fleet:ADR-002`,
`ose:ADR-009`). Scopes come from `adr_scopes` in product-registry.yaml:

  - `fleet` is built IN MEMORY from its `adr_dir` (resolved against
    --repo-root) with adr_index.build_index — generated is not stored.
  - every other scope needs an `index` file (path relative to --repo-root),
    a committed snapshot produced by adr_index.py. The file's JSON `scope`
    must equal its map key. Spokes publish IDs, status and enforced-by only
    (rule R3: no code crosses).

The invariant side is `references.adr`, a YAML list of qualified IDs. The ADR
side is whatever adr_index.py parses (one parser, imported, never
re-implemented here).

Rules
=====
  E1 unresolved   a qualified ID names a scope not in adr_scopes, or a number
                  absent from that scope's index
  E2 bare         a value in references.adr is not a qualified ID (legacy path
                  strings included; reported, never crashed on), or adr is not
                  a list
  E3 one-sided    invariant X lists ADR Y, Y is declared, X not in Y's
                  enforced_by (retired invariants skipped)
  E4 one-sided    ADR Y declares X, and X does not exist or does not list Y
                  (a retired X may be named; it cannot be required to list)
  E5 undeclared   a fleet ADR is undeclared and not on the ratchet's
                  adrs_undeclared, or is on it but declared (spoke scopes
                  exempt until they publish their own index, slice 3)
  E6 ratchet      a non-retired invariant has no ADR and is not on
                  invariants_without_adr, or is on it but has ADRs, or the list
                  holds an id above frozen_max_id (the list can only shrink)
  E7 status       GAP, report only: an invariant lists an ADR whose status is
                  not Accepted
  INDEX map       an index file in <brain>/adr-indexes/ that adr_scopes does
                  not name for its scope

E3 and E4 skip `declared: false` ADRs and print how many were skipped.

Usage
=====
    python3 check_adr_edges.py --brain ocr-docs-brain --repo-root . \
        --ratchet ocr-docs-brain/adr-edge-ratchet.json \
        [--report-path adr-edge-report.json]

The report JSON (product_id "brain", summary, failures with check /
invariant_or_adr / detail) is shaped so open_drift_ticket.py can route it.

Exit codes:
  0 — clean (GAP findings do not fail)
  1 — one or more findings
  2 — tool error: bad arguments, missing or malformed registry, scope map,
      index or ratchet (fails closed; no report is written)
"""
import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

try:
    import yaml
except ImportError:
    print('FATAL: pyyaml not available (pip install pyyaml)', file=sys.stderr)
    sys.exit(2)

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from adr_index import (  # noqa: E402
        SCOPE_RE, AdrIndexError, build_index, parse_qualified_id)
    from adr_index import validate_index as _validate_index_shape  # noqa: E402
except ImportError as e:
    print(f'FATAL: cannot import adr_index.py beside this script: {e}',
          file=sys.stderr)
    sys.exit(2)

PASS, FAIL, GAP = 'PASS', 'FAIL', 'GAP'
FLEET = 'fleet'

RULES = [
    ('E1_unresolved', 'qualified ID resolves to a scope and an ADR in its index'),
    ('E2_bare', 'every references.adr value is a qualified ID in a list'),
    ('E3_one_sided_inv_to_adr', 'an ADR an invariant lists names it back'),
    ('E4_one_sided_adr_to_inv', 'an invariant an ADR declares lists it back'),
    ('E5_undeclared_fleet', 'undeclared fleet ADRs match adrs_undeclared'),
    ('E6_ratchet', 'invariants without an ADR match invariants_without_adr'),
    ('E7_status', 'every listed ADR is Accepted (report only)'),
    ('INDEX_map', 'every file in adr-indexes/ is the one adr_scopes names'),
]
GAP_RULES = {'E7_status'}


class ToolError(Exception):
    """Configuration or input error: exit 2, fail closed."""


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
def _load_yaml(path: Path):
    if not path.is_file():
        raise ToolError(f'{path} not found')
    try:
        return yaml.safe_load(path.read_text(encoding='utf-8-sig'))
    except yaml.YAMLError as e:
        raise ToolError(f'{path} is not valid YAML: {e}')


def _load_json(path: Path, what: str):
    if not path.is_file():
        raise ToolError(f'{what} {path} not found')
    try:
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except (ValueError, UnicodeDecodeError) as e:
        raise ToolError(f'{what} {path} is not valid JSON: {e}')


def load_invariants(brain: Path) -> dict:
    """Return {id: entry} from architectural-invariants.yaml (safe_load only)."""
    data = _load_yaml(brain / 'architectural-invariants.yaml')
    invs = data.get('invariants') if isinstance(data, dict) else None
    if not isinstance(invs, list):
        raise ToolError('architectural-invariants.yaml has no `invariants` list')
    out = {}
    for inv in invs:
        if not isinstance(inv, dict):
            raise ToolError(f'invariant entry is not a mapping: {inv!r}')
        iid = inv.get('id')
        if not isinstance(iid, int) or isinstance(iid, bool):
            raise ToolError(f'invariant id is not an integer: {iid!r}')
        if iid in out:
            raise ToolError(f'duplicate invariant id #{iid}')
        refs = inv.get('references')
        if refs is not None and not isinstance(refs, dict):
            raise ToolError(f'invariant #{iid} references is not a mapping')
        out[iid] = inv
    return out


def is_retired(inv: dict) -> bool:
    return str(inv.get('status', '')).strip().lower() == 'retired'


def load_scope_map(brain: Path) -> dict:
    data = _load_yaml(brain / 'product-registry.yaml')
    scopes = data.get('adr_scopes') if isinstance(data, dict) else None
    if not isinstance(scopes, dict) or not scopes:
        raise ToolError('product-registry.yaml has no `adr_scopes` map')
    for key, cfg in scopes.items():
        if not isinstance(key, str) or not SCOPE_RE.fullmatch(key):
            raise ToolError(f'adr_scopes key {key!r} is not a valid scope '
                            '([a-z][a-z0-9-]*)')
        if not isinstance(cfg, dict):
            raise ToolError(f'adr_scopes.{key} is not a mapping')
    if FLEET not in scopes:
        raise ToolError('adr_scopes has no `fleet` scope')
    return scopes


def load_ratchet(path: Path) -> dict:
    data = _load_json(path, 'ratchet')
    if not isinstance(data, dict):
        raise ToolError(f'ratchet {path} is not a JSON object')
    fmax = data.get('frozen_max_id')
    if not isinstance(fmax, int) or isinstance(fmax, bool):
        raise ToolError('ratchet frozen_max_id is missing or not an integer')
    inv = data.get('invariants_without_adr')
    if not isinstance(inv, list) or not all(
            isinstance(i, int) and not isinstance(i, bool) for i in inv):
        raise ToolError('ratchet invariants_without_adr must be a list of integers')
    und = data.get('adrs_undeclared')
    if not isinstance(und, list) or not all(isinstance(a, str) for a in und):
        raise ToolError('ratchet adrs_undeclared must be a list of strings')
    return {'frozen_max_id': fmax, 'invariants_without_adr': inv,
            'adrs_undeclared': und}


def validate_index(idx, scope: str, origin: str) -> dict:
    """Check an index (built or loaded) against the adr_index.py contract,
    using adr_index's own validator (one contract, one implementation).

    Returns {number: adr}. Raises ToolError on any malformed field, and when
    the index's `scope` is not the adr_scopes key it was loaded for.
    """
    if isinstance(idx, dict) and idx.get('scope') != scope:
        raise ToolError(f'{origin}: index scope is {idx.get("scope")!r} but '
                        f'adr_scopes names it as {scope!r}')
    try:
        _validate_index_shape(idx, expected_scope=scope)
    except AdrIndexError as e:
        raise ToolError(f'{origin}: {e}')
    return {a['number']: a for a in idx['adrs']}


def load_scopes(scope_map: dict, repo_root: Path) -> dict:
    """Return {scope: {number: adr}} for every scope in the map."""
    out = {}
    for scope, cfg in scope_map.items():
        if scope == FLEET:
            if cfg.get('index'):
                raise ToolError('adr_scopes.fleet names an index file; the '
                                'fleet index is built in memory and never stored')
            rel = cfg.get('adr_dir')
            if not isinstance(rel, str) or not rel:
                raise ToolError('adr_scopes.fleet has no adr_dir')
            adr_dir = repo_root / rel
            if not adr_dir.is_dir():
                raise ToolError(f'fleet adr_dir {adr_dir} is not a directory')
            try:
                idx = build_index(adr_dir, FLEET)
            except SystemExit as e:
                raise ToolError(f'building the fleet index failed (exit {e.code})')
            except Exception as e:
                raise ToolError(f'building the fleet index failed: '
                                f'{type(e).__name__}: {e}')
            out[scope] = validate_index(idx, scope, f'fleet ({rel})')
        else:
            rel = cfg.get('index')
            if not isinstance(rel, str) or not rel:
                raise ToolError(f'adr_scopes.{scope} has no index file; every '
                                'scope except fleet needs one')
            path = repo_root / rel
            idx = _load_json(path, f'index for scope {scope!r}')
            out[scope] = validate_index(idx, scope, rel)
    return out


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
def invariant_edges(invs: dict):
    """Return (edges, raw_counts, e2_findings).

    edges:      {inv_id: [(scope, number, qualified_id), ...]}  (qualified only)
    raw_counts: {inv_id: number of values in references.adr, valid or not}
    """
    edges, raw_counts, e2 = {}, {}, []
    for iid in sorted(invs):
        refs = invs[iid].get('references') or {}
        raw = refs.get('adr')
        if raw is None:
            values = []
        elif isinstance(raw, list):
            values = raw
        else:
            values = [raw]
            e2.append((f'#{iid}', f'references.adr must be a list of qualified '
                                  f'IDs, got a {type(raw).__name__}: {raw!r}'))
        raw_counts[iid] = len(values)
        seen, ok = set(), []
        for v in values:
            q = parse_qualified_id(v)
            if q is None:
                e2.append((f'#{iid}', f'references.adr value {v!r} is not a '
                                      'qualified ID (<scope>:ADR-NNN)'))
                continue
            if v in seen:
                e2.append((f'#{iid}', f'references.adr lists {v} twice'))
                continue
            seen.add(v)
            ok.append((q[0], q[1], v))
        edges[iid] = ok
    return edges, raw_counts, e2


def index_map_findings(brain: Path, repo_root: Path, scope_map: dict):
    """Every *.json in <brain>/adr-indexes/ must be the file adr_scopes names
    for the scope the file declares."""
    out = []
    d = brain / 'adr-indexes'
    if not d.is_dir():
        return out
    named = {}
    for scope, cfg in scope_map.items():
        rel = cfg.get('index')
        if isinstance(rel, str) and rel:
            named[(repo_root / rel).resolve()] = scope
    for f in sorted(d.glob('*.json')):
        label = f'adr-indexes/{f.name}'
        data = _load_json(f, 'index')
        scope = data.get('scope') if isinstance(data, dict) else None
        if scope not in scope_map:
            out.append((label, f'declares scope {scope!r}, which is not in '
                               'adr_scopes; add the scope or remove the file'))
        elif named.get(f.resolve()) != scope:
            out.append((label, f'declares scope {scope!r}, but adr_scopes does '
                               f'not name this file as its index'))
    return out


def run(brain: Path, repo_root: Path, ratchet_path: Path, report_path: Path) -> int:
    invs = load_invariants(brain)
    scope_map = load_scope_map(brain)
    ratchet = load_ratchet(ratchet_path)
    scopes = load_scopes(scope_map, repo_root)
    edges, raw_counts, e2 = invariant_edges(invs)

    findings = {name: [] for name, _ in RULES}
    findings['E2_bare'] = e2
    skipped = {'E3': 0, 'E4': 0}

    # E1 (all invariants) / E3 + E7 (non-retired)
    resolved = {}  # inv_id -> {qualified_id: adr}
    for iid in sorted(edges):
        resolved[iid] = {}
        for scope, num, qid in edges[iid]:
            if scope not in scopes:
                findings['E1_unresolved'].append(
                    (f'#{iid}', f'{qid}: scope {scope!r} is not in adr_scopes'))
                continue
            adr = scopes[scope].get(num)
            if adr is None:
                findings['E1_unresolved'].append(
                    (f'#{iid}', f'{qid}: no ADR-{num:03d} in the {scope} index'))
                continue
            resolved[iid][qid] = adr
        if is_retired(invs[iid]):
            continue
        for qid, adr in resolved[iid].items():
            if not adr['declared']:
                skipped['E3'] += 1
            elif iid not in adr['enforced_by']:
                findings['E3_one_sided_inv_to_adr'].append(
                    (f'#{iid}', f'lists {qid}, but {qid} declares enforced-by '
                                f'{_fmt_ids(adr["enforced_by"])} without #{iid}'))
            status = adr.get('status')
            if status != 'Accepted':
                findings['E7_status'].append(
                    (f'#{iid}', f'lists {qid}, whose status is {status or "missing"}'))

    # E4 (every declared ADR in every scope)
    for scope in sorted(scopes):
        for num in sorted(scopes[scope]):
            adr = scopes[scope][num]
            qid = adr['id']
            if not adr['declared']:
                skipped['E4'] += 1
                continue
            for x in sorted(set(adr['enforced_by'])):
                if x not in invs:
                    findings['E4_one_sided_adr_to_inv'].append(
                        (qid, f'declares invariant #{x}, which does not exist '
                              'in the registry'))
                elif is_retired(invs[x]):
                    continue
                elif qid not in {q for _, _, q in edges.get(x, [])}:
                    findings['E4_one_sided_adr_to_inv'].append(
                        (qid, f'declares invariant #{x}, but #{x} '
                              f'references.adr does not list {qid}'))

    # E5 (fleet scope only)
    und = ratchet['adrs_undeclared']
    fleet = scopes[FLEET]
    fleet_ids = {a['id']: a for a in fleet.values()}
    for qid in _dupes(und):
        findings['E5_undeclared_fleet'].append(
            (qid, 'listed more than once in adrs_undeclared'))
    for num in sorted(fleet):
        a = fleet[num]
        if not a['declared'] and a['id'] not in und:
            findings['E5_undeclared_fleet'].append(
                (a['id'], 'declares no Enforced-by and is not on adrs_undeclared; '
                          'add an **Enforced-by:** line (invariant #N, or '
                          'none - <reason>)'))
        elif a['declared'] and a['id'] in und:
            findings['E5_undeclared_fleet'].append(
                (a['id'], 'is declared now; remove it from adrs_undeclared'))
    for qid in sorted(set(und)):
        if qid not in fleet_ids:
            findings['E5_undeclared_fleet'].append(
                (qid, 'is on adrs_undeclared but is not a fleet ADR in the '
                      'fleet index; remove it'))

    # E6 (non-retired invariants; the list can only shrink)
    fmax = ratchet['frozen_max_id']
    wo = ratchet['invariants_without_adr']
    for x in _dupes(wo):
        findings['E6_ratchet'].append(
            (f'#{x}', 'listed more than once in invariants_without_adr'))
    for x in sorted(set(wo)):
        if x > fmax:
            findings['E6_ratchet'].append(
                (f'#{x}', f'is above frozen_max_id {fmax}; a new invariant must '
                          'carry an ADR and cannot join the ratchet'))
        if x not in invs:
            findings['E6_ratchet'].append(
                (f'#{x}', 'is on invariants_without_adr but does not exist in '
                          'the registry; remove it'))
        elif is_retired(invs[x]):
            findings['E6_ratchet'].append(
                (f'#{x}', 'is retired; remove it from invariants_without_adr'))
    for iid in sorted(invs):
        if is_retired(invs[iid]):
            continue
        has = raw_counts.get(iid, 0) > 0
        on = iid in wo
        if not has and not on:
            hint = (f'(ids above frozen_max_id {fmax} must carry an ADR)'
                    if iid > fmax else '(or add it to invariants_without_adr)')
            findings['E6_ratchet'].append(
                (f'#{iid}', f'has no references.adr; give it a qualified ADR ID '
                            f'{hint}'))
        elif has and on:
            findings['E6_ratchet'].append(
                (f'#{iid}', 'has an ADR now; remove it from invariants_without_adr'))

    # INDEX map
    findings['INDEX_map'] = index_map_findings(brain, repo_root, scope_map)

    return report(brain, repo_root, report_path, findings, skipped)


def _dupes(seq):
    seen, d = set(), []
    for x in seq:
        if x in seen and x not in d:
            d.append(x)
        seen.add(x)
    return d


def _fmt_ids(ids):
    return '[' + ', '.join(f'#{i}' for i in ids) + ']' if ids else '[]'


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def report(brain, repo_root, report_path, findings, skipped) -> int:
    checks = []
    for name, desc in RULES:
        items = findings[name]
        if not items:
            status, detail = PASS, desc
        else:
            status = GAP if name in GAP_RULES else FAIL
            detail = f'{len(items)} finding(s)'
        if name == 'E3_one_sided_inv_to_adr':
            detail += f' (skipped {skipped["E3"]} edge(s) to undeclared ADRs)'
        if name == 'E4_one_sided_adr_to_inv':
            detail += f' (skipped {skipped["E4"]} undeclared ADR(s))'
        checks.append((name, status, detail))

    print('=' * 76)
    print('  ADR <-> INVARIANT EDGE CHECK — brain')
    print('=' * 76)
    for name, status, detail in checks:
        marker = {PASS: '[PASS]', FAIL: '[FAIL]', GAP: '[GAP]'}[status]
        print(f'  {marker:7} {name:26} {detail}')
        for who, what in findings[name]:
            print(f'           - {who}: {what}')

    failures = [{'check': n, 'invariant_or_adr': w, 'detail': d}
                for n, _ in RULES if n not in GAP_RULES
                for w, d in findings[n]]
    gaps = [{'check': n, 'invariant_or_adr': w, 'detail': d}
            for n in GAP_RULES for w, d in findings[n]]
    passed = [c for c in checks if c[1] == PASS]
    rules_failed = [c for c in checks if c[1] == FAIL]
    rules_gap = [c for c in checks if c[1] == GAP]

    print('-' * 76)
    print(f'  {len(passed)} pass / {len(rules_failed)} fail / {len(rules_gap)} gap'
          f'  (total {len(checks)} rules; {len(failures)} finding(s), '
          f'{len(gaps)} gap finding(s))')
    print('-' * 76)

    out = {
        'product_id': 'brain',
        'check': 'adr_edges',
        'brain_path': str(brain),
        'repo_root': str(repo_root),
        'summary': {
            'passed': len(passed),
            'failed': len(failures),
            'gaps': len(gaps),
            'total': len(checks),
            'rules_failed': len(rules_failed),
            'skipped_undeclared': dict(skipped),
        },
        'passes': [{'check': n, 'detail': d} for n, s, d in checks if s == PASS],
        'failures': failures,
        'gaps': gaps,
    }
    Path(report_path).write_text(json.dumps(out, indent=2) + '\n',
                                 encoding='utf-8', newline='\n')
    print(f'Report: {report_path}')
    return 1 if failures else 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description='Two-sided ADR <-> invariant edge check (brain-internal)')
    ap.add_argument('--brain', required=True, help='path to ocr-docs-brain')
    ap.add_argument('--repo-root', required=True,
                    help='OCR-docs repo root (resolves adr_dir and index paths)')
    ap.add_argument('--ratchet', required=True,
                    help='path to adr-edge-ratchet.json')
    ap.add_argument('--report-path', default='adr-edge-report.json')
    args = ap.parse_args(argv)

    brain, repo_root = Path(args.brain), Path(args.repo_root)
    if not brain.is_dir():
        print(f'FATAL: --brain {brain} is not a directory', file=sys.stderr)
        return 2
    if not repo_root.is_dir():
        print(f'FATAL: --repo-root {repo_root} is not a directory', file=sys.stderr)
        return 2
    try:
        return run(brain, repo_root, Path(args.ratchet), Path(args.report_path))
    except ToolError as e:
        print(f'FATAL: {e}', file=sys.stderr)
        return 2
    except Exception as e:  # anything unexpected fails closed
        print(f'FATAL: {type(e).__name__}: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
