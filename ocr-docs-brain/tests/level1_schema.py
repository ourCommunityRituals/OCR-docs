#!/usr/bin/env python3
"""
Level 1 — SCHEMA
=================
Required fields per record type. Type validation. Enum constraints.
Ensures every record in the brain has the shape consumers expect.
"""
import sys, yaml
from pathlib import Path

BRAIN = Path(__file__).parent.parent if (Path(__file__).parent.parent / 'product-registry.yaml').exists() \
    else Path(__file__).parent / 'ocr-docs-brain'

results = []

def check(name, condition, detail=''):
    results.append((name, 'PASS' if condition else 'FAIL', detail))

def load(f):
    return yaml.safe_load((BRAIN / f).read_text())

pr = load('product-registry.yaml')
tg = load('tier-gates.yaml')
cd = load('corridor-definitions.yaml')
et = load('event-taxonomy.yaml')
inv = load('architectural-invariants.yaml')

# ---------------------------------------------------------------------------
# 1.1 — Required top-level keys per file
# ---------------------------------------------------------------------------
TOP_KEYS = {
    'product-registry.yaml':     ['schema_version', 'products'],
    'tier-gates.yaml':           ['schema_version', 'tiers', 'phase_gates'],
    'corridor-definitions.yaml': ['schema_version', 'hierarchy', 'founding_corridors'],
    'event-taxonomy.yaml':       ['schema_version', 'total_types_v1', 'categories'],
    'architectural-invariants.yaml': ['schema_version', 'invariants'],
}
for fname, keys in TOP_KEYS.items():
    data = load(fname)
    missing = [k for k in keys if k not in data]
    check(f'top_keys:{fname}', not missing, f'missing {missing}' if missing else f'all {len(keys)} present')

# ---------------------------------------------------------------------------
# 1.2 — Product records: required fields and type validation
# ---------------------------------------------------------------------------
PRODUCT_REQUIRED = ['product_id', 'product_name', 'identity_layer']
PRODUCT_ENUMS = {
    'identity_layer': ['anonymous', 'non-anonymous', 'pre-tech', 'n/a'],
}
PRODUCT_ARRAY_FIELDS = ['regulatory_pools', 'required_tags', 'funnels_to']
PRODUCT_DICT_FIELDS = ['tier_availability', 'bigquery_datasets']

for p in pr.get('products', []):
    pid = p.get('product_id', '?')

    # Required fields
    missing = [f for f in PRODUCT_REQUIRED if f not in p]
    check(f'product_required:{pid}', not missing,
          f'missing {missing}' if missing else 'all required fields present')

    # Enum validation
    for field, allowed in PRODUCT_ENUMS.items():
        val = p.get(field)
        check(f'product_enum:{pid}.{field}', val in allowed,
              f'{val} not in {allowed}' if val not in allowed else f'{val}')

    # Type validation: arrays must be lists or None
    for field in PRODUCT_ARRAY_FIELDS:
        val = p.get(field)
        check(f'product_type:{pid}.{field}',
              val is None or isinstance(val, list),
              f'expected list, got {type(val).__name__}' if val is not None and not isinstance(val, list) else 'ok')

    # Type validation: dicts must be dicts or None
    for field in PRODUCT_DICT_FIELDS:
        val = p.get(field)
        if p.get('identity_layer') in ('n/a', 'pre-tech') and val is None:
            continue  # governance/pre-tech products may lack these
        check(f'product_type:{pid}.{field}',
              val is None or isinstance(val, dict),
              f'expected dict, got {type(val).__name__}' if val is not None and not isinstance(val, dict) else 'ok')

# ---------------------------------------------------------------------------
# 1.3 — Event taxonomy: required fields per event type
# ---------------------------------------------------------------------------
EVENT_REQUIRED = ['type_id', 'type_name', 'uec_code', 'product_origin']
for cat in et.get('categories', []):
    cat_id = cat.get('category_id', '?')
    for t in cat.get('event_types', []):
        tid = t.get('type_id', '?')
        missing = [f for f in EVENT_REQUIRED if f not in t]
        check(f'event_required:{cat_id}/{tid}', not missing,
              f'missing {missing}' if missing else 'complete')

# ---------------------------------------------------------------------------
# 1.4 — Category records: required fields
# ---------------------------------------------------------------------------
CAT_REQUIRED = ['category_id', 'category_name', 'uec_color', 'event_types']
for cat in et.get('categories', []):
    cat_id = cat.get('category_id', '?')
    missing = [f for f in CAT_REQUIRED if f not in cat]
    check(f'category_required:{cat_id}', not missing,
          f'missing {missing}' if missing else 'complete')

# ---------------------------------------------------------------------------
# 1.5 — Invariant records: required fields and enum validation
# ---------------------------------------------------------------------------
INV_REQUIRED = ['id', 'name', 'title', 'status', 'test_file', 'enforces', 'applies_to']
INV_STATUS_ENUM = ['live', 'partial', 'planned']
for i in inv.get('invariants', []):
    iid = i.get('id', '?')
    missing = [f for f in INV_REQUIRED if f not in i]
    check(f'invariant_required:#{iid}', not missing,
          f'missing {missing}' if missing else 'complete')
    status = i.get('status')
    check(f'invariant_status_enum:#{iid}', status in INV_STATUS_ENUM,
          f'{status} not in {INV_STATUS_ENUM}' if status not in INV_STATUS_ENUM else f'{status}')

# ---------------------------------------------------------------------------
# 1.6 — Corridor definitions: required fields per founding corridor
# ---------------------------------------------------------------------------
CORR_REQUIRED = ['corridor_id', 'role']
for c in cd.get('founding_corridors', []):
    cid = c.get('corridor_id', '?')
    missing = [f for f in CORR_REQUIRED if f not in c]
    check(f'corridor_required:{cid}', not missing,
          f'missing {missing}' if missing else 'complete')

# ---------------------------------------------------------------------------
# 1.7 — Tier gates: tiers have required structure
# ---------------------------------------------------------------------------
for tier_id, tier_data in tg.get('tiers', {}).items():
    check(f'tier_has_name:{tier_id}',
          isinstance(tier_data, dict) and ('name' in tier_data or 'display_name' in tier_data),
          f'display_name={tier_data.get("display_name", tier_data.get("name"))}' if isinstance(tier_data, dict) else 'not a dict')

# ---------------------------------------------------------------------------
# 1.8 — No null/empty product_id or type_id values
# ---------------------------------------------------------------------------
for p in pr.get('products', []):
    pid = p.get('product_id')
    check(f'product_id_nonempty:{pid}', pid and isinstance(pid, str) and len(pid.strip()) > 0)

for cat in et.get('categories', []):
    for t in cat.get('event_types', []):
        tid = t.get('type_id')
        check(f'type_id_nonempty:{tid}', tid and isinstance(tid, str) and len(tid.strip()) > 0)

# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')
print(f'{"="*76}')
print(f'  LEVEL 1 — SCHEMA')
print(f'{"="*76}')
for name, status, detail in results:
    m = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {m}  {name:50} {detail}')
print(f'{"-"*76}')
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print(f'{"-"*76}')
sys.exit(0 if failed == 0 else 1)
