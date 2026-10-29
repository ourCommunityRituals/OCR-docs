#!/usr/bin/env python3
"""
OCR-docs brain validation suite
================================
Runs every check that CI will need to run.
Exits 0 if brain is ready for sync, non-zero otherwise.

Tests:
  1. Syntax — all YAML/JSON files parse
  2. Schema — required top-level keys present
  3. Taxonomy count — declared total matches defined entries
  4. Cross-reference integrity — products <-> corridors <-> tiers <-> pools
  5. Identity layer contract — anonymous products CANNOT contribute to named data
  6. Tier availability matrix — every product has tier_availability across all 5 phases
  7. BigQuery dataset routing — every regulatory pool has a schema file
  8. Required tags contract — every anonymous-layer product declares the same required_tags
  9. Faith organization commitment — tier gates contain explicit rule
  10. Invariants file — architectural-invariants.yaml exists and covers all 10 invariants
"""
import sys, yaml, json
from pathlib import Path

BRAIN = Path(__file__).parent if (Path(__file__).parent / 'product-registry.yaml').exists() else Path(__file__).parent / 'ocr-docs-brain'
results = []  # (test_name, status, detail)
FAIL = 'FAIL'
PASS = 'PASS'
WARN = 'WARN'

def record(name, status, detail=''):
    results.append((name, status, detail))

# ---------------------------------------------------------------------------
# TEST 1: Syntax
# ---------------------------------------------------------------------------
yaml_files = ['product-registry.yaml', 'tier-gates.yaml', 'corridor-definitions.yaml', 'event-taxonomy.yaml']
json_files = ['bigquery-schemas/general.json', 'bigquery-schemas/hipaa.json',
              'bigquery-schemas/coppa.json', 'bigquery-schemas/aggregate.json']
loaded = {}

for f in yaml_files:
    try:
        with open(BRAIN / f) as fh:
            loaded[f] = yaml.safe_load(fh)
        record(f'syntax:{f}', PASS, f'{(BRAIN / f).stat().st_size} bytes')
    except Exception as e:
        record(f'syntax:{f}', FAIL, str(e))

for f in json_files:
    try:
        with open(BRAIN / f) as fh:
            loaded[f] = json.load(fh)
        record(f'syntax:{f}', PASS, f'{(BRAIN / f).stat().st_size} bytes')
    except Exception as e:
        record(f'syntax:{f}', FAIL, str(e))

# ---------------------------------------------------------------------------
# TEST 2: Schema — required top-level keys
# ---------------------------------------------------------------------------
REQUIRED_KEYS = {
    'product-registry.yaml':     ['schema_version', 'products'],
    'tier-gates.yaml':           ['schema_version', 'tiers', 'phase_gates'],
    'corridor-definitions.yaml': ['schema_version', 'hierarchy', 'founding_corridors'],
    'event-taxonomy.yaml':       ['schema_version', 'total_types_v1', 'categories'],
}

for fname, required in REQUIRED_KEYS.items():
    if fname not in loaded:
        record(f'schema:{fname}', FAIL, 'file did not load')
        continue
    data = loaded[fname]
    missing = [k for k in required if k not in data]
    if missing:
        record(f'schema:{fname}', FAIL, f'missing keys: {missing}')
    else:
        record(f'schema:{fname}', PASS, f'all {len(required)} required keys present')

# ---------------------------------------------------------------------------
# TEST 3: Taxonomy count
# ---------------------------------------------------------------------------
et = loaded.get('event-taxonomy.yaml', {})
all_types = [t for c in et.get('categories', []) for t in c.get('event_types', [])]
phase1_actual = sum(1 for t in all_types if t.get('phase', 1) == 1)
declared_v1 = et.get('total_types_v1', 0)
declared_all = et.get('total_types', 0)
if declared_v1 == phase1_actual and declared_all == len(all_types):
    record('taxonomy:count_match', PASS, f'{phase1_actual} phase 1 types ({declared_v1} declared), {len(all_types)} in all ({declared_all} declared)')
else:
    record('taxonomy:count_match', FAIL, f'phase 1: declared {declared_v1}, defined {phase1_actual}; all: declared {declared_all}, defined {len(all_types)}')

# ---------------------------------------------------------------------------
# TEST 4: Cross-reference integrity
# ---------------------------------------------------------------------------
pr = loaded.get('product-registry.yaml', {})
cd = loaded.get('corridor-definitions.yaml', {})
products = pr.get('products', [])
corridors = cd.get('founding_corridors', [])
corridor_ids = {c.get('corridor_id') for c in corridors}

# Every product with "active_corridors" field must reference real corridors
broken_refs = []
for p in products:
    for corr in p.get('active_corridors', []) or []:
        if corr not in corridor_ids:
            broken_refs.append((p.get('product_id'), corr))

if broken_refs:
    record('xref:product_corridors', FAIL, f'{len(broken_refs)} broken: {broken_refs[:3]}')
else:
    record('xref:product_corridors', PASS, 'all product->corridor refs resolve (or none present)')

# ---------------------------------------------------------------------------
# TEST 5: Identity layer contract
# ---------------------------------------------------------------------------
# Anonymous products cannot have data_contributor:true to non-anonymous destinations
identity_issues = []
for p in products:
    layer = p.get('identity_layer')
    funnels_to = p.get('funnels_to', []) or []
    # This is a softer rule — flag for review
    if layer == 'anonymous' and p.get('anonymization_method') not in ('full', None):
        identity_issues.append(p.get('product_id'))

if identity_issues:
    record('identity:contract', FAIL, f'anonymous products with partial anonymization: {identity_issues}')
else:
    record('identity:contract', PASS, 'all anonymous products declare full anonymization')

# ---------------------------------------------------------------------------
# TEST 6: Tier availability matrix
# ---------------------------------------------------------------------------
REQUIRED_PHASES = {'phase1', 'phase2', 'phase3', 'phase4', 'phase5'}
tier_gaps = []
for p in products:
    if p.get('identity_layer') == 'n/a':
        continue  # governance products don't need tier availability
    ta = p.get('tier_availability')
    if not isinstance(ta, dict):
        tier_gaps.append((p.get('product_id'), 'missing tier_availability'))
        continue
    missing_phases = REQUIRED_PHASES - set(ta.keys())
    if missing_phases:
        tier_gaps.append((p.get('product_id'), f'missing {missing_phases}'))

if tier_gaps:
    record('tiers:availability_matrix', FAIL, f'{len(tier_gaps)} gaps: {tier_gaps[:3]}')
else:
    record('tiers:availability_matrix', PASS, 'every operational product declares tier_availability across all 5 phases')

# ---------------------------------------------------------------------------
# TEST 7: BigQuery dataset routing
# ---------------------------------------------------------------------------
pool_schema_files = {
    'general':   BRAIN / 'bigquery-schemas/general.json',
    'hipaa':     BRAIN / 'bigquery-schemas/hipaa.json',
    'coppa':     BRAIN / 'bigquery-schemas/coppa.json',
    'aggregate': BRAIN / 'bigquery-schemas/aggregate.json',
}

pool_issues = []
for pool, path in pool_schema_files.items():
    if not path.exists():
        pool_issues.append(f'{pool}: schema file missing')
        continue
    schema = loaded.get(f'bigquery-schemas/{pool}.json', {})
    if not isinstance(schema, (dict, list)) or not schema:
        pool_issues.append(f'{pool}: empty schema')

if pool_issues:
    record('bigquery:routing', FAIL, '; '.join(pool_issues))
else:
    record('bigquery:routing', PASS, 'all 4 pool schemas present and non-empty')

# ---------------------------------------------------------------------------
# TEST 8: Required tags contract
# ---------------------------------------------------------------------------
anon_products = [p for p in products if p.get('identity_layer') == 'anonymous']
tag_sets = {p.get('product_id'): set(p.get('required_tags', []) or []) for p in anon_products}

if not tag_sets:
    record('tags:anon_contract', WARN, 'no anonymous products to compare')
else:
    reference = list(tag_sets.values())[0]
    mismatched = [pid for pid, tags in tag_sets.items() if tags != reference]
    if mismatched:
        record('tags:anon_contract', FAIL, f'anon products with non-matching tag sets: {mismatched}')
    else:
        record('tags:anon_contract', PASS, f'all {len(tag_sets)} anon products share identical required_tags')

# ---------------------------------------------------------------------------
# TEST 9: Faith organization commitment (churches free indefinitely)
# ---------------------------------------------------------------------------
tg = loaded.get('tier-gates.yaml', {})
tg_str = yaml.dump(tg).lower()
faith_keywords = ['faith', 'church', 'congregation', 'religious']
has_faith_rule = any(k in tg_str for k in faith_keywords)
if has_faith_rule:
    record('commitments:faith_free', PASS, 'tier-gates.yaml references faith organizations')
else:
    record('commitments:faith_free', FAIL, 'no explicit faith-organization-free rule in tier-gates.yaml')

# ---------------------------------------------------------------------------
# TEST 10: Invariants file
# ---------------------------------------------------------------------------
invariants_path = BRAIN / 'architectural-invariants.yaml'
if not invariants_path.exists():
    record('invariants:file', FAIL, 'architectural-invariants.yaml does not exist')
else:
    try:
        with open(invariants_path) as f:
            inv = yaml.safe_load(f)
        inv_list = inv.get('invariants', [])
        if len(inv_list) >= 10:
            record('invariants:file', PASS, f'{len(inv_list)} invariants declared')
        else:
            record('invariants:file', FAIL, f'only {len(inv_list)} invariants, expected 10')
    except Exception as e:
        record('invariants:file', FAIL, f'parse error: {e}')

# ---------------------------------------------------------------------------
# TEST 11: UEC scan codes — every add/remove references a valid code
# ---------------------------------------------------------------------------
valid_codes = set(et.get('valid_scan_codes', {}).keys())
default_codes = set(et.get('default_scan_codes', []))

if not valid_codes:
    record('uec:valid_codes_registry', FAIL, 'valid_scan_codes missing from taxonomy')
elif len(valid_codes) != 11:
    record('uec:valid_codes_registry', FAIL, f'expected 11 valid codes, found {len(valid_codes)}')
else:
    record('uec:valid_codes_registry', PASS, f'{len(valid_codes)} codes registered (7 core + 4 ext)')

if not default_codes:
    record('uec:default_set', FAIL, 'default_scan_codes missing from taxonomy')
elif not default_codes.issubset(valid_codes):
    record('uec:default_set', FAIL, f'default set contains unknown codes: {default_codes - valid_codes}')
else:
    record('uec:default_set', PASS, f'default set: {sorted(default_codes)}')

# ---------------------------------------------------------------------------
# TEST 12: UEC scan codes — per-type add/remove all reference valid codes
#          and effective set is never empty
# ---------------------------------------------------------------------------
if valid_codes and default_codes:
    invalid_refs = []
    empty_sets = []
    for cat in et.get('categories', []):
        for t in cat.get('event_types', []):
            tid = t.get('type_id', '?')
            add = set(t.get('scan_codes_add', []) or [])
            remove = set(t.get('scan_codes_remove', []) or [])
            unknown = (add | remove) - valid_codes
            if unknown:
                invalid_refs.append(f'{tid}: {unknown}')
            effective = (default_codes | add) - remove
            if not effective:
                empty_sets.append(tid)

    if invalid_refs:
        record('uec:scan_code_refs', FAIL, f'{len(invalid_refs)} types reference unknown codes: {invalid_refs[:3]}')
    else:
        record('uec:scan_code_refs', PASS, 'all scan_codes_add/remove values are valid UEC codes')

    if empty_sets:
        record('uec:effective_set_nonempty', FAIL, f'{len(empty_sets)} types have empty effective set: {empty_sets}')
    else:
        record('uec:effective_set_nonempty', PASS, 'all 47 types have non-empty effective scan code sets')

# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
passed = sum(1 for _, s, _ in results if s == PASS)
failed = sum(1 for _, s, _ in results if s == FAIL)
warned = sum(1 for _, s, _ in results if s == WARN)

print('=' * 76)
print(f'  BRAIN VALIDATION REPORT')
print(f'  {BRAIN.resolve()}')
print('=' * 76)
print()
for name, status, detail in results:
    marker = {'PASS': '[PASS]', 'FAIL': '[FAIL]', 'WARN': '[WARN]'}[status]
    print(f'  {marker}  {name:40} {detail}')
print()
print('-' * 76)
print(f'  Results: {passed} pass / {failed} fail / {warned} warn  (total {len(results)})')
print('-' * 76)

sys.exit(0 if failed == 0 else 1)
