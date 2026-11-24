#!/usr/bin/env python3
"""
script_mutation.py: mutation testing for the brain's gate scripts.

Every spoke checks out ocr-docs-brain/scripts and runs them as gates
(check_brain_contract.py, check_cross_repo_imports.py). Their self-tests in
ocr-docs-brain/tests/ say the gates work. This checks that those tests would
notice if a gate stopped working: each mutant in script-mutants.json writes one
fault into a rule a gate enforces, the mutant's kill tests run, and at least
one of them must fail.

FAIL CLOSED. A mutant is killed only when a kill test exits non-zero AND its
own summary line ("N pass / M fail") reports a failed case. A test that
crashed with no summary is an error, not a kill (a mutant that broke the
import would otherwise count as a test with teeth). Before any mutant, the
same tests run on the unchanged source and must pass, or every mutant would
read as killed. The source is restored after each mutant, whatever happens.

Usage:
  python3 tests/mutation/script_mutation.py              run every mutant
  python3 tests/mutation/script_mutation.py --only <id>,<id>
  python3 tests/mutation/script_mutation.py --check      validate the catalog only
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = Path(__file__).resolve().parent / 'script-mutants.json'
ID_RE = re.compile(r'^[a-z0-9-]+$')
SUMMARY_RE = re.compile(r'(\d+)\s+pass\s*/\s*(\d+)\s+fail')


def check_catalog(catalog, read):
    """Problems with a catalog, as strings; empty when it is sound.
    `read(path)` returns a file's text, or None when it does not exist."""
    if not isinstance(catalog, dict):
        return ['the catalog is not an object']
    mutants = catalog.get('mutants')
    if not isinstance(mutants, list) or not mutants:
        return ['the catalog lists no mutants']
    problems, seen = [], set()
    for m in mutants:
        mid = m.get('id') if isinstance(m, dict) else None
        where = f'mutant {mid!r}'
        if not isinstance(m, dict):
            problems.append(f'{where}: not an object')
            continue
        if not isinstance(mid, str) or not ID_RE.match(mid):
            problems.append(f'{where}: id must be lowercase words joined by hyphens')
        if mid in seen:
            problems.append(f'{where}: the id is used twice')
        seen.add(mid)
        for key in ('rule', 'file', 'find'):
            if not isinstance(m.get(key), str) or not m.get(key):
                problems.append(f'{where}: no {key}')
        if not isinstance(m.get('replace'), str):
            problems.append(f'{where}: no replace')
        if m.get('find') == m.get('replace'):
            problems.append(f'{where}: replace is the same as find, so nothing is mutated')
        kill = m.get('kill')
        if not isinstance(kill, list) or not kill:
            problems.append(f'{where}: no test in kill')
            kill = []
        for spec in kill:
            if read(spec) is None:
                problems.append(f'{where}: kill test {spec} does not exist')
        if isinstance(m.get('file'), str) and m.get('file'):
            text = read(m['file'])
            if text is None:
                problems.append(f"{where}: {m['file']} does not exist")
            elif isinstance(m.get('find'), str) and m.get('find'):
                n = text.count(m['find'])
                if n != 1:
                    problems.append(f"{where}: find occurs {n} times in {m['file']}, not once "
                                    '(the source moved; update the mutant)')
    return problems


def apply_mutant(text, mutant):
    """The source with the fault written in. Raises unless `find` occurs once."""
    n = text.count(mutant['find'])
    if n != 1:
        raise ValueError(f"mutant {mutant['id']}: find occurs {n} times in {mutant['file']}, not once")
    return text.replace(mutant['find'], mutant['replace'], 1)


def verdict(returncode, stdout):
    """What one test file's run says.
      killed   exited non-zero and its summary reports a failed case
      passed   exited zero and its summary reports passing cases, none failed
      error    anything else: no summary, nothing ran, or a crash
    """
    found = SUMMARY_RE.findall(stdout or '')
    if not found:
        return 'error', 'no "N pass / M fail" summary (the test crashed or did not run)'
    passed, failed = (int(x) for x in found[-1])
    if returncode != 0 and failed > 0:
        return 'killed', f'{failed} case(s) failed'
    if returncode == 0 and failed == 0 and passed > 0:
        return 'passed', f'{passed} case(s) passed'
    return 'error', f'exit {returncode} with {passed} pass / {failed} fail'


def combine(verdicts):
    """One mutant's verdict from its kill tests: killed if any test killed it,
    else error if any test errored, else passed (survived)."""
    kinds = [v for v, _ in verdicts]
    if 'killed' in kinds:
        return verdicts[kinds.index('killed')]
    if 'error' in kinds:
        return verdicts[kinds.index('error')]
    return verdicts[0] if verdicts else ('error', 'no kill test ran')


def gate_failures(results):
    """Failures over every mutant's result, as strings; empty when all were killed."""
    out = []
    for r in results:
        if r['verdict'] == 'passed':
            out.append(f"{r['id']} SURVIVED: {r['rule']} The tests {', '.join(r['kill'])} "
                       f"passed with this fault in {r['file']}.")
        elif r['verdict'] != 'killed':
            out.append(f"{r['id']} ERROR: {r['reason']}. An error is not a kill.")
    return out


def _read(path):
    p = ROOT / path
    return p.read_text(encoding='utf-8') if p.is_file() else None


def _run_tests(specs):
    results = []
    for spec in specs:
        proc = subprocess.run([sys.executable, str(ROOT / spec)], cwd=ROOT,
                              capture_output=True, text=True, timeout=300)
        results.append(verdict(proc.returncode, proc.stdout))
    return results


def main(argv):
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    problems = check_catalog(catalog, _read)
    if problems:
        for p in problems:
            print(f'::error title=Script mutant catalog::{p}')
        return 1
    if '--check' in argv:
        print(f"{CATALOG.name}: {len(catalog['mutants'])} mutants, all sound.")
        return 0
    mutants = catalog['mutants']
    if '--only' in argv:
        i = argv.index('--only')
        only = argv[i + 1].split(',') if i + 1 < len(argv) else []
        mutants = [m for m in mutants if m['id'] in only]
        if not mutants:
            print('::error::--only matched no mutant')
            return 1

    specs = sorted({s for m in mutants for s in m['kill']})
    print(f'== Baseline: {", ".join(specs)} on the unchanged source')
    base = _run_tests(specs)
    bad = [(s, v) for s, v in zip(specs, base) if v[0] != 'passed']
    if bad:
        for s, (v, why) in bad:
            print(f'::error title=Script mutation baseline::{s} must pass on the unchanged source ({v}: {why})')
        return 1

    results = []
    for m in mutants:
        path = ROOT / m['file']
        original = path.read_text(encoding='utf-8')
        print(f"== Mutant {m['id']}: {m['file']}")
        try:
            path.write_text(apply_mutant(original, m), encoding='utf-8')
            v, why = combine(_run_tests(m['kill']))
        finally:
            path.write_text(original, encoding='utf-8')
        print(f'   {v}: {why}')
        results.append({**m, 'verdict': v, 'reason': why})

    rows = [f"| {r['id']} | {'killed' if r['verdict'] == 'killed' else '**' + ('survived' if r['verdict'] == 'passed' else 'error') + '**'} | {r['rule']} |"
            for r in results]
    table = '\n'.join(['### Gate-script mutation', '', '| Mutant | Result | Rule |', '| --- | --- | --- |', *rows, ''])
    print(table)
    summary = os.environ.get('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary, 'a', encoding='utf-8') as fh:
            fh.write(table + '\n')

    failures = gate_failures(results)
    for f in failures:
        print(f'::error title=Gate-script mutation::{f}')
    print(f'{len(results) - len(failures)} of {len(results)} gate-script mutants killed.')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
