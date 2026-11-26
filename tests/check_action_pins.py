#!/usr/bin/env python3
"""
check_action_pins.py
====================
Every action OCR-docs runs is pinned by commit, and a read token used for a
checkout is never written to disk (OCR-231; CCR security sweep 2026-11-25).

Why: a tag such as `@v4` can be moved to new code by whoever controls the
action's repository. propagate-standards.yml runs with OCR_PROPAGATE_WRITE, a
token that writes to every spoke, and the composite actions in
.github/actions/ (deploy-spoke among them) run inside the spokes' own
pipelines. A full 40-hex commit cannot be moved. Dependabot
(.github/dependabot.yml, github-actions) proposes new commits as reviewed PRs.

Rules, over .github/workflows/*.yml and .github/actions/*/action.yml:
  1. every remote `uses:` ends in a full 40-hex commit (local `./` and
     `docker://` references are exempt);
  2. a checkout given a `token:` sets `persist-credentials: false`, except the
     checkouts listed in PUSHES_WITH_CHECKOUT_TOKEN, which push with it.
And over .github/dependabot.yml (CCR F5, 2026-11-26):
  3. every update entry waits at least COOLDOWN_DAYS after a release before
     proposing it (`cooldown: default-days`), so a hijacked or broken release
     has time to be caught upstream before a PR offers it here.

Usage:
  python3 tests/check_action_pins.py --self-test   # each rule fails on a planted fault
  python3 tests/check_action_pins.py               # check the real files

Exit: 0 = clean, 1 = a finding (or a self-test that did not catch its fault).
"""
import re
import sys
from pathlib import Path

import yaml

SHA = re.compile(r'@[0-9a-f]{40}$')

# Checkouts that push with their token (file name -> number of such checkouts).
# Listed exactly, so a new one cannot join silently.
PUSHES_WITH_CHECKOUT_TOKEN = {'propagate-standards.yml': 1}

# Days Dependabot waits after a release before proposing it (rule 3).
COOLDOWN_DAYS = 7


def _steps(doc):
    if not isinstance(doc, dict):
        return
    jobs = doc.get('jobs')
    if isinstance(jobs, dict):
        for job in jobs.values():
            if isinstance(job, dict):
                if job.get('uses'):
                    yield {'uses': job['uses']}
                for s in job.get('steps') or []:
                    if isinstance(s, dict):
                        yield s
    runs = doc.get('runs')
    if isinstance(runs, dict):
        for s in runs.get('steps') or []:
            if isinstance(s, dict):
                yield s


def findings(text: str, name: str) -> list[str]:
    doc = yaml.safe_load(text)
    out = []
    persisted = 0
    for s in _steps(doc):
        uses = str(s.get('uses') or '')
        if uses and not uses.startswith(('./', 'docker://')) and not SHA.search(uses):
            out.append(f'{name}: not pinned by commit: {uses}')
        w = s.get('with') or {}
        if uses.startswith('actions/checkout@') and 'token' in w and w.get('persist-credentials') is not False:
            persisted += 1
    allowed = PUSHES_WITH_CHECKOUT_TOKEN.get(name, 0)
    if persisted > allowed:
        out.append(f'{name}: {persisted - allowed} checkout(s) keep their token on disk')
    return out


def cooldown_findings(text: str) -> list[str]:
    doc = yaml.safe_load(text) or {}
    updates = doc.get('updates') if isinstance(doc, dict) else None
    if not isinstance(updates, list) or not updates:
        return ['dependabot.yml: no update entries']
    out = []
    for u in updates:
        eco = u.get('package-ecosystem', '?') if isinstance(u, dict) else '?'
        cd = u.get('cooldown') if isinstance(u, dict) else None
        days = cd.get('default-days') if isinstance(cd, dict) else None
        if not isinstance(days, int) or isinstance(days, bool) or days < COOLDOWN_DAYS:
            out.append(f'dependabot.yml: {eco} has no cooldown of at least {COOLDOWN_DAYS} days')
    return out


def self_test() -> int:
    good = 'jobs:\n  a:\n    steps:\n      - uses: actions/checkout@' + 'a' * 40 + ' # v4\n      - uses: ./.github/actions/x\n'
    cases = [
        ('pinned and local pass', good, 'x.yml', 0),
        ('a tag is caught', 'jobs:\n  a:\n    steps:\n      - uses: actions/checkout@v4\n', 'x.yml', 1),
        ('a branch is caught', 'jobs:\n  a:\n    steps:\n      - uses: actions/setup-python@main\n', 'x.yml', 1),
        ('a short SHA is caught', 'jobs:\n  a:\n    steps:\n      - uses: actions/cache@0057852\n', 'x.yml', 1),
        ('a reusable workflow on a tag is caught', 'jobs:\n  a:\n    uses: o/r/.github/workflows/w.yml@v1\n', 'x.yml', 1),
        ('a composite action step on a tag is caught',
         "name: n\ndescription: d\nruns:\n  using: composite\n  steps:\n    - uses: actions/setup-node@v4\n", 'action.yml', 1),
        ('a token checkout that persists is caught',
         'jobs:\n  a:\n    steps:\n      - uses: actions/checkout@' + 'a' * 40 + '\n        with:\n          token: x\n', 'x.yml', 1),
        ('a token checkout with persist-credentials: false passes',
         'jobs:\n  a:\n    steps:\n      - uses: actions/checkout@' + 'a' * 40
         + '\n        with:\n          token: x\n          persist-credentials: false\n', 'x.yml', 0),
        ('the listed pusher may keep one, not two',
         'jobs:\n  a:\n    steps:\n' + ('      - uses: actions/checkout@' + 'a' * 40 + '\n        with:\n          token: x\n') * 2,
         'propagate-standards.yml', 1),
    ]
    eco = "  - package-ecosystem: github-actions\n    directory: /\n    schedule:\n      interval: weekly\n"
    cooldown_cases = [
        ('a 7-day cooldown passes', 'version: 2\nupdates:\n' + eco + '    cooldown:\n      default-days: 7\n', 0),
        ('a missing cooldown is caught', 'version: 2\nupdates:\n' + eco, 1),
        ('a 3-day cooldown is caught', 'version: 2\nupdates:\n' + eco + '    cooldown:\n      default-days: 3\n', 1),
        ('a quoted day count is caught', 'version: 2\nupdates:\n' + eco + "    cooldown:\n      default-days: '7'\n", 1),
        ('one entry of two without it is caught',
         'version: 2\nupdates:\n' + eco + '    cooldown:\n      default-days: 7\n' + eco, 1),
        ('a file with no updates is caught', 'version: 2\n', 1),
    ]
    bad = 0
    for label, text, name, want in cases:
        got = len(findings(text, name))
        ok = got == want
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {label} (findings {got}, want {want})")
    for label, text, want in cooldown_cases:
        got = len(cooldown_findings(text))
        ok = got == want
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {label} (findings {got}, want {want})")
    return 1 if bad else 0


def main() -> int:
    if '--self-test' in sys.argv:
        return self_test()
    root = Path(__file__).resolve().parent.parent
    files = sorted(root.glob('.github/workflows/*.yml')) + sorted(root.glob('.github/actions/*/action.yml'))
    if len(files) < 10:
        print(f'only {len(files)} files found; the glob is wrong')
        return 1
    out = []
    for f in files:
        out += findings(f.read_text(encoding='utf-8'), f.name if f.parent.name == 'workflows' else str(f.relative_to(root)))
    dep = root / '.github' / 'dependabot.yml'
    out += cooldown_findings(dep.read_text(encoding='utf-8')) if dep.exists() else ['.github/dependabot.yml is missing']
    for line in out:
        print(line)
    print(f'{len(files)} files checked, {len(out)} finding(s)')
    return 1 if out else 0


if __name__ == '__main__':
    sys.exit(main())
