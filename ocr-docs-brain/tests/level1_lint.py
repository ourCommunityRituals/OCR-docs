#!/usr/bin/env python3
"""
Level 1 — LINT
===============
Syntax, encoding, formatting, structural rules.
Runs after Level 0 (security) passes.
"""
import json, re, sys, yaml
from pathlib import Path

BRAIN = Path(__file__).parent.parent if (Path(__file__).parent.parent / 'product-registry.yaml').exists() \
    else Path(__file__).parent / 'ocr-docs-brain'

results = []

def check(name, condition, detail=''):
    results.append((name, 'PASS' if condition else 'FAIL', detail))

# ---------------------------------------------------------------------------
# 0.1 — Files exist
# ---------------------------------------------------------------------------
REQUIRED_YAML = [
    'product-registry.yaml',
    'tier-gates.yaml',
    'corridor-definitions.yaml',
    'event-taxonomy.yaml',
    'architectural-invariants.yaml',
]
REQUIRED_JSON = [
    'bigquery-schemas/general.json',
    'bigquery-schemas/hipaa.json',
    'bigquery-schemas/coppa.json',
    'bigquery-schemas/aggregate.json',
]

for f in REQUIRED_YAML + REQUIRED_JSON:
    check(f'file_exists:{f}', (BRAIN / f).exists(), f'{f} {"found" if (BRAIN/f).exists() else "MISSING"}')

# ---------------------------------------------------------------------------
# 0.2 — All YAML parses without error
# ---------------------------------------------------------------------------
yaml_data = {}
for f in REQUIRED_YAML:
    path = BRAIN / f
    if not path.exists():
        continue
    try:
        raw = path.read_text(encoding='utf-8')
        yaml_data[f] = yaml.safe_load(raw)
        check(f'yaml_parse:{f}', True, f'{path.stat().st_size} bytes')
    except yaml.YAMLError as e:
        check(f'yaml_parse:{f}', False, str(e)[:120])

# ---------------------------------------------------------------------------
# 0.3 — All JSON parses without error
# ---------------------------------------------------------------------------
json_data = {}
for f in REQUIRED_JSON:
    path = BRAIN / f
    if not path.exists():
        continue
    try:
        raw = path.read_text(encoding='utf-8')
        json_data[f] = json.loads(raw)
        check(f'json_parse:{f}', True, f'{path.stat().st_size} bytes')
    except json.JSONDecodeError as e:
        check(f'json_parse:{f}', False, str(e)[:120])

# ---------------------------------------------------------------------------
# 0.4 — UTF-8 encoding (no binary, no latin-1 artifacts)
# ---------------------------------------------------------------------------
for f in REQUIRED_YAML + REQUIRED_JSON:
    path = BRAIN / f
    if not path.exists():
        continue
    try:
        path.read_text(encoding='utf-8')
        check(f'encoding_utf8:{f}', True)
    except UnicodeDecodeError as e:
        check(f'encoding_utf8:{f}', False, str(e)[:100])

# ---------------------------------------------------------------------------
# 0.5 — No tabs in YAML (spaces only)
# ---------------------------------------------------------------------------
for f in REQUIRED_YAML:
    path = BRAIN / f
    if not path.exists():
        continue
    raw = path.read_text(encoding='utf-8')
    tab_lines = [i+1 for i, line in enumerate(raw.splitlines()) if '\t' in line]
    check(f'no_tabs:{f}', len(tab_lines) == 0,
          f'tabs on lines {tab_lines[:5]}' if tab_lines else 'clean')

# ---------------------------------------------------------------------------
# 0.6 — Schema version present and valid semver
# ---------------------------------------------------------------------------
SEMVER = re.compile(r'^\d+\.\d+\.\d+$')
for f in REQUIRED_YAML:
    if f not in yaml_data:
        continue
    sv = yaml_data[f].get('schema_version')
    check(f'semver:{f}', sv is not None and SEMVER.match(str(sv)),
          f'version={sv}' if sv else 'missing schema_version')

# ---------------------------------------------------------------------------
# 0.7 — No duplicate top-level keys (YAML allows silent overwrite)
# ---------------------------------------------------------------------------
for f in REQUIRED_YAML:
    path = BRAIN / f
    if not path.exists():
        continue
    raw = path.read_text(encoding='utf-8')
    # Simple heuristic: top-level keys are lines starting at column 0 with a colon
    top_keys = re.findall(r'^([a-z_]+):', raw, re.MULTILINE)
    dupes = [k for k in set(top_keys) if top_keys.count(k) > 1]
    check(f'no_dupe_keys:{f}', len(dupes) == 0,
          f'duplicates: {dupes}' if dupes else 'clean')

# ---------------------------------------------------------------------------
# 0.8 — File size bounds (not empty, not unreasonably large)
# ---------------------------------------------------------------------------
for f in REQUIRED_YAML + REQUIRED_JSON:
    path = BRAIN / f
    if not path.exists():
        continue
    size = path.stat().st_size
    check(f'size_bounds:{f}', 10 < size < 500_000,
          f'{size} bytes' + (' (suspiciously small)' if size < 100 else '') +
          (' (suspiciously large)' if size > 200_000 else ''))

# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')
print(f'{"="*76}')
print(f'  LEVEL 1 — LINT')
print(f'{"="*76}')
for name, status, detail in results:
    m = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {m}  {name:42} {detail}')
print(f'{"-"*76}')
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print(f'{"-"*76}')
sys.exit(0 if failed == 0 else 1)
