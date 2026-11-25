#!/usr/bin/env python3
"""
check_workflow_injection.py
===========================
Caller-controlled text never reaches a shell through ${{ }} (CCR F17,
security sweep Run 3, 2026-11-19).

Why: GitHub expands ${{ }} into the script text before bash runs it, so a
dispatch input, an event field or a reusable workflow's input written there is
code, not data. propagate-standards.yml once put `github.event.inputs.repos`
straight into a step of a job that later holds OCR_PROPAGATE_WRITE, a token
that writes to every spoke. Such values must reach `run:` through `env:`.

Not yet covered: `inputs.*` of a reusable workflow or composite action
written into `run:` (docs-ci.yml and five composite actions do this today).
Their callers are workflows in our own repos, so they are hardened as a
separate follow-up rather than here.

Rules, over .github/workflows/*.yml and .github/actions/*/action.yml:
  1. no `run:` script contains a ${{ }} expression naming `github.event.`
     (dispatch inputs, PR and issue text, commit messages) or
     `github.head_ref`;
  2. propagate-standards.yml's scope step selects a repo only on an exact name
     match against the comma-separated list (a substring is not a match), and
     a blank list selects every repo.

Usage:
  python3 tests/check_workflow_injection.py --self-test   # each rule fails on a planted fault
  python3 tests/check_workflow_injection.py               # check the real files

Exit: 0 = clean, 1 = a finding (or a self-test that did not catch its fault).
"""
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EXPR = re.compile(r'\$\{\{(.*?)\}\}', re.S)
UNTRUSTED = re.compile(r'\b(github\.event\.|github\.head_ref)')


def _steps(doc):
    if not isinstance(doc, dict):
        return
    for job in (doc.get('jobs') or {}).values():
        for step in (job or {}).get('steps') or []:
            yield step
    runs = doc.get('runs') or {}
    for step in runs.get('steps') or []:
        yield step


def injection_findings(name, doc):
    out = []
    for step in _steps(doc):
        script = (step or {}).get('run')
        if not isinstance(script, str):
            continue
        for expr in EXPR.findall(script):
            if UNTRUSTED.search(expr):
                label = step.get('name') or step.get('id') or '?'
                out.append(f'{name}: step "{label}" puts ${{{{{expr.strip()}}}}} in a run script; pass it through env:')
    return out


def scope_step(doc):
    for step in _steps(doc):
        if (step or {}).get('id') == 'scope':
            return step
    return None


# (input list, repo, expected in_scope)
SCOPE_CASES = [
    ('', 'ourSharedEvents', 'true'),
    ('  ', 'ourWKRP', 'true'),
    ('ourSharedEvents', 'ourSharedEvents', 'true'),
    ('ourWKRP, ourSharedEvents', 'ourSharedEvents', 'true'),
    ('oursharedevents', 'ourSharedEvents', 'true'),
    ('ourSharedEvents', 'ourWKRP', 'false'),
    ('ourSharedEventsX', 'ourSharedEvents', 'false'),
    ('ourShared', 'ourSharedEvents', 'false'),
    ('$(touch pwned)', 'ourWKRP', 'false'),
]


def run_scope(script, inputs, repo, tmp):
    out = tmp / 'out'
    out.write_text('')
    env = {'PATH': '/usr/bin:/bin', 'INPUT_REPOS': inputs, 'REPO': repo, 'GITHUB_OUTPUT': str(out)}
    result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', script], env=env, cwd=tmp,
                            capture_output=True, text=True)
    if result.returncode != 0:
        return f'error (exit {result.returncode})'
    for line in out.read_text().splitlines():
        if line.startswith('in_scope='):
            return line.split('=', 1)[1]
    return None


def scope_findings(doc):
    import tempfile
    step = scope_step(doc)
    if step is None:
        return ['propagate-standards.yml: no step with id "scope"']
    env = step.get('env') or {}
    out = []
    if 'INPUT_REPOS' not in env:
        out.append('propagate-standards.yml: scope step does not take the repo list through env:')
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        for inputs, repo, want in SCOPE_CASES:
            got = run_scope(step['run'], inputs, repo, tmp)
            if got != want:
                out.append(f'propagate-standards.yml: repos="{inputs}" repo={repo} gave in_scope={got}, want {want}')
        if (tmp / 'pwned').exists():
            out.append('propagate-standards.yml: the repo list was executed as a command')
    return out


def real_files():
    files = sorted((ROOT / '.github' / 'workflows').glob('*.yml'))
    files += sorted((ROOT / '.github' / 'actions').glob('*/action.yml'))
    return files


def check():
    findings = []
    for f in real_files():
        doc = yaml.safe_load(f.read_text())
        findings += injection_findings(f.name, doc)
        if f.name == 'propagate-standards.yml':
            findings += scope_findings(doc)
    for line in findings:
        print(line)
    print(f'{len(real_files())} files checked, {len(findings)} finding(s)')
    return 1 if findings else 0


OLD_SCOPE = '''INPUT_REPOS="${{ github.event.inputs.repos }}"
REPO="${{ matrix.repo }}"
if [ -z "$INPUT_REPOS" ]; then
  echo "in_scope=true" >> "$GITHUB_OUTPUT"
elif echo "$INPUT_REPOS" | grep -q "$REPO"; then
  echo "in_scope=true" >> "$GITHUB_OUTPUT"
else
  echo "in_scope=false" >> "$GITHUB_OUTPUT"
fi
'''

SUBSTRING_SCOPE = '''if [ -z "$INPUT_REPOS" ]; then
  echo "in_scope=true" >> "$GITHUB_OUTPUT"
elif echo "$INPUT_REPOS" | grep -qi "$REPO"; then
  echo "in_scope=true" >> "$GITHUB_OUTPUT"
else
  echo "in_scope=false" >> "$GITHUB_OUTPUT"
fi
'''


def self_test():
    failures = 0

    def expect(label, findings):
        nonlocal failures
        if findings:
            print(f'caught: {label}')
        else:
            print(f'MISSED: {label}')
            failures += 1

    expect('dispatch input in run', injection_findings('t.yml', {'jobs': {'a': {'steps': [{'run': 'echo "${{ github.event.inputs.repos }}"'}]}}}))
    expect('PR title in composite run', injection_findings('a.yml', {'runs': {'steps': [{'run': 'echo ${{ github.event.pull_request.title }}'}]}}))
    expect('head_ref in run', injection_findings('t.yml', {'jobs': {'a': {'steps': [{'run': 'git checkout ${{ github.head_ref }}'}]}}}))
    clean = injection_findings('t.yml', {'jobs': {'a': {'steps': [{'run': 'echo "$X ${{ matrix.repo }}"', 'env': {'X': '${{ inputs.phase }}'}}]}}})
    if clean:
        print('MISSED: env-passed input was flagged (false positive)')
        failures += 1
    else:
        print('caught: env-passed input is allowed')
    # The scope rule must fail on the old script (inline input) and on a substring match.
    expect('old inline scope step', scope_findings({'jobs': {'a': {'steps': [{'id': 'scope', 'run': OLD_SCOPE}]}}}))
    expect('substring scope match', scope_findings({'jobs': {'a': {'steps': [{'id': 'scope', 'env': {'INPUT_REPOS': 'x'}, 'run': SUBSTRING_SCOPE}]}}}))
    print(f'self-test: {failures} missed')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(self_test() if '--self-test' in sys.argv else check())
