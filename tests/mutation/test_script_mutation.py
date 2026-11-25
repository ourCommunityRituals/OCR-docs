#!/usr/bin/env python3
"""
test_script_mutation.py: self-test for tests/mutation/script_mutation.py and
its catalog. Plain Python with an "N pass / M fail" summary, like the brain's
own script self-tests.

BORN RED: each rule here was watched failing with its fault written into the
runner (`failed > 0` read as `failed >= 0` in verdict, the `n != 1` check
removed from check_catalog, the 'error' branch removed from combine, the
`passed` branch removed from gate_failures).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import script_mutation as sm  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

FILES = {
    'scripts/a.py': 'if bad:\n    return 1\nreturn 0\n',
    'tests/test_a.py': 'print("1 pass / 0 fail")',
}
GOOD = {'mutants': [{'id': 'bad-passes', 'rule': 'r', 'file': 'scripts/a.py',
                     'find': 'if bad:', 'replace': 'if False:', 'kill': ['tests/test_a.py']}]}


def fake_read(p):
    return FILES.get(p)


def with_mutant(**patch):
    return {'mutants': [{**GOOD['mutants'][0], **patch}]}


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def committed_catalog_is_sound():
    cat = json.loads(sm.CATALOG.read_text(encoding='utf-8'))
    assert sm.check_catalog(cat, sm._read) == [], sm.check_catalog(cat, sm._read)


@case
def committed_catalog_kills_only_with_brain_script_tests():
    cat = json.loads(sm.CATALOG.read_text(encoding='utf-8'))
    for m in cat['mutants']:
        assert m['file'].startswith('ocr-docs-brain/scripts/'), m['file']
        for spec in m['kill']:
            assert spec.startswith('ocr-docs-brain/tests/test_'), spec


@case
def sound_catalog_passes():
    assert sm.check_catalog(GOOD, fake_read) == []


@case
def born_red_find_not_once_fails():
    assert 'occurs 0 times' in ' '.join(sm.check_catalog(with_mutant(find='if worse:'), fake_read))
    assert 'occurs 2 times' in ' '.join(sm.check_catalog(with_mutant(find='return'), fake_read))


@case
def born_red_missing_parts_fail():
    assert 'does not exist' in ' '.join(sm.check_catalog(with_mutant(kill=['tests/gone.py']), fake_read))
    assert 'no test in kill' in ' '.join(sm.check_catalog(with_mutant(kill=[]), fake_read))
    assert 'nothing is mutated' in ' '.join(sm.check_catalog(with_mutant(replace='if bad:'), fake_read))
    assert 'used twice' in ' '.join(sm.check_catalog({'mutants': GOOD['mutants'] * 2}, fake_read))
    assert sm.check_catalog({'mutants': []}, fake_read) == ['the catalog lists no mutants']


@case
def apply_writes_the_fault_once():
    assert sm.apply_mutant(FILES['scripts/a.py'], GOOD['mutants'][0]).startswith('if False:\n')
    try:
        sm.apply_mutant('x x', {'id': 'x', 'file': 'f', 'find': 'x', 'replace': 'y'})
    except ValueError as e:
        assert '2 times' in str(e)
    else:
        raise AssertionError('a find that occurs twice was applied')


@case
def verdict_reads_the_summary():
    assert sm.verdict(1, '  3 pass / 1 fail  (total 4)')[0] == 'killed'
    assert sm.verdict(0, '  4 pass / 0 fail  (total 4)')[0] == 'passed'


@case
def born_red_a_crash_or_empty_run_is_an_error_not_a_kill():
    assert sm.verdict(1, 'Traceback (most recent call last):\n  NameError')[0] == 'error'
    assert sm.verdict(1, '  0 pass / 0 fail')[0] == 'error'
    assert sm.verdict(0, '  0 pass / 0 fail')[0] == 'error'
    assert sm.verdict(0, '')[0] == 'error'


@case
def born_red_combine_prefers_kill_then_error():
    assert sm.combine([('passed', 'p'), ('killed', 'k')])[0] == 'killed'
    assert sm.combine([('passed', 'p'), ('error', 'e')])[0] == 'error'
    assert sm.combine([('passed', 'p')])[0] == 'passed'
    assert sm.combine([])[0] == 'error'


@case
def born_red_survivor_and_error_each_fail_the_gate():
    base = {'rule': 'r', 'file': 'f', 'kill': ['k'], 'reason': 'x'}
    assert sm.gate_failures([{'id': 'a', 'verdict': 'killed', **base}]) == []
    f = sm.gate_failures([{'id': 'a', 'verdict': 'passed', **base}, {'id': 'b', 'verdict': 'error', **base}])
    assert len(f) == 2 and f[0].startswith('a SURVIVED') and f[1].startswith('b ERROR'), f


@case
def workflow_runs_the_selftest_and_the_mutants():
    wf = (ROOT / '.github/workflows/mutation-testing.yml').read_text(encoding='utf-8')
    assert 'python3 tests/mutation/test_script_mutation.py' in wf
    assert 'python3 tests/mutation/script_mutation.py' in wf
    assert 'schedule:' in wf and 'workflow_dispatch:' in wf


def main():
    passed = failed = 0
    for fn in CASES:
        try:
            fn()
            passed += 1
            print(f'  [PASS]  {fn.__name__}')
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f'  [FAIL]  {fn.__name__}: {e!r}')
    print(f'  {passed} pass / {failed} fail  (total {passed + failed} cases)')
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
