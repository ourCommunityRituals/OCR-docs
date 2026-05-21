#!/usr/bin/env python3
"""
validate_action_metadata.py
===========================
Structural validation for every composite action in .github/actions/.

Run by the actions-selftest workflow's `metadata` job. Catches the class
of bug that otherwise only surfaces when a spoke runs the action for the
first time: a missing `shell:` on a run step (composite actions inherit
no default shell), a non-composite runner, an empty step list, or a
malformed action.yml.

Exit: 0 = all actions valid, 1 = at least one validation failure.
"""
import sys
from pathlib import Path

import yaml

REQUIRED_TOP_KEYS = ('name', 'description', 'runs')


def validate(action_file: Path, repo_root: Path) -> list[str]:
    rel = action_file.relative_to(repo_root)
    try:
        doc = yaml.safe_load(action_file.read_text(encoding='utf-8'))
    except Exception as e:  # noqa: BLE001 - any parse failure is a validation failure
        return [f'{rel}: YAML parse error: {e}']
    if not isinstance(doc, dict):
        return [f'{rel}: top level is not a mapping']

    errors = []
    for key in REQUIRED_TOP_KEYS:
        if key not in doc:
            errors.append(f'{rel}: missing top-level key "{key}"')

    runs = doc.get('runs')
    if not isinstance(runs, dict):
        return errors + [f'{rel}: "runs" is not a mapping']
    if runs.get('using') != 'composite':
        errors.append(f'{rel}: runs.using must be "composite"')

    steps = runs.get('steps')
    if not isinstance(steps, list) or not steps:
        return errors + [f'{rel}: runs.steps must be a non-empty list']

    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            errors.append(f'{rel}: step #{i} is not a mapping')
            continue
        label = step.get('name', f'#{i}')
        if 'uses' not in step and 'run' not in step:
            errors.append(f'{rel}: step "{label}" has neither uses nor run')
        if 'run' in step and 'shell' not in step:
            errors.append(f'{rel}: step "{label}" has run but no shell')
    return errors


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    actions_dir = repo_root / '.github' / 'actions'
    action_files = sorted(actions_dir.glob('*/action.yml'))
    if not action_files:
        print(f'ERROR: no action.yml files under {actions_dir}', file=sys.stderr)
        sys.exit(1)

    all_errors = []
    for af in action_files:
        errs = validate(af, repo_root)
        if errs:
            all_errors += errs
        else:
            print(f'OK   {af.relative_to(repo_root)}')

    if all_errors:
        print('-' * 60)
        for e in all_errors:
            print(f'::error::{e}')
        print(f'{len(all_errors)} validation failure(s) across composite actions')
        sys.exit(1)
    print(f'All {len(action_files)} composite actions structurally valid.')


if __name__ == '__main__':
    main()
