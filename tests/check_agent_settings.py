#!/usr/bin/env python3
"""
check_agent_settings.py
=======================
Agent permissions are checked in, and the dangerous ones are denied (CCR F1,
security sweep 2026-11-26).

Every agent session in this repo reads .claude/settings.json. A local
settings.local.json can add to it but is gitignored (F16), so this file is the
shared floor. The deny list keeps agents from changing GitHub settings, cutting
releases or tags, dispatching workflows (propagate-standards writes to every
spoke), touching secrets, pushing to main and deploying. Merges and other
`gh api` calls ask first.

Usage:
  python3 tests/check_agent_settings.py --self-test
  python3 tests/check_agent_settings.py

Exit: 0 = clean, 1 = a finding (or a self-test that did not catch its fault).
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MUST_DENY = [
    'Bash(gh api * -X *)',
    'Bash(gh api * --method *)',
    'Bash(gh release*)',
    'Bash(gh secret*)',
    'Bash(gh workflow run*)',
    'Bash(doppler secrets*)',
    'Bash(git push --force*)',
    'Bash(git push * main*)',
    'Bash(git push * --tags*)',
    'Bash(git tag*)',
    'Bash(wrangler deploy*)',
    'Bash(npx wrangler deploy*)',
    'Bash(wrangler secret*)',
]
MUST_ASK = ['Bash(gh pr merge*)', 'Bash(gh api*)']
# A rule that lets an agent run anything, or push, outweighs any deny list.
WIDE = re.compile(r'^Bash\((python3? \*|node \*|bash \*|sh \*|npx \*|pnpm \*|git push|gh api|gh \*|\*)')


def findings(settings):
    perms = (settings or {}).get('permissions') or {}
    allow, ask, deny = (perms.get(k) or [] for k in ('allow', 'ask', 'deny'))
    out = [f'deny list is missing {r}' for r in MUST_DENY if r not in deny]
    out += [f'ask list is missing {r}' for r in MUST_ASK if r not in ask]
    out += [f'allow list has a run-anything rule: {r}' for r in allow if WIDE.match(r)]
    out += [f'{r} is both allowed and denied' for r in allow if r in deny]
    return out


def check():
    path = ROOT / '.claude' / 'settings.json'
    if not path.exists():
        print('.claude/settings.json is missing')
        return 1
    out = findings(json.loads(path.read_text()))
    for line in out:
        print(line)
    print(f'.claude/settings.json: {len(out)} finding(s)')
    return 1 if out else 0


def self_test():
    good = json.loads((ROOT / '.claude' / 'settings.json').read_text())
    cases = {
        'empty settings': {},
        'deny rule removed': {**good, 'permissions': {**good['permissions'], 'deny': good['permissions']['deny'][1:]}},
        'python * allowed': {**good, 'permissions': {**good['permissions'], 'allow': good['permissions']['allow'] + ['Bash(python3 *)']}},
        'merge allowed without asking': {**good, 'permissions': {**good['permissions'], 'ask': []}},
    }
    missed = 0
    for label, doc in cases.items():
        if findings(doc):
            print(f'caught: {label}')
        else:
            print(f'MISSED: {label}')
            missed += 1
    print(f'self-test: {missed} missed')
    return 1 if missed else 0


if __name__ == '__main__':
    sys.exit(self_test() if '--self-test' in sys.argv else check())
