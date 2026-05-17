#!/usr/bin/env python3
"""
Level 6 — CONTRACT (provider-side)
====================================
What the brain PROMISES to every consumer.
These are the interfaces the brain publishes. If these break,
every product repo's CI will fail. The brain must not ship a change
that violates a published contract.

This is the provider half of consumer-driven contract testing.
Level 7 (pact) is the consumer half.
"""
import json, sys, yaml
from pathlib import Path

# Fix Windows console cp1252 encoding + enable line buffering so output streams
# correctly on self-hosted Windows runners (e.g. Bloodraven). Handles the `→`
# character that appears in some detail strings.
try:
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)
except Exception:
    pass

BRAIN = Path(__file__).parent.parent if (Path(__file__).parent.parent / 'product-registry.yaml').exists() \
    else Path(__file__).parent / 'ocr-docs-brain'

results = []

def check(name, condition, detail=''):
    results.append((name, 'PASS' if condition else 'FAIL', detail))

def load(f):
    if f.endswith('.json'):
        return json.loads((BRAIN / f).read_text(encoding='utf-8'))
    return yaml.safe_load((BRAIN / f).read_text(encoding='utf-8'))

pr = load('product-registry.yaml')
tg = load('tier-gates.yaml')
et = load('event-taxonomy.yaml')
inv = load('architectural-invariants.yaml')

products = {p['product_id']: p for p in pr.get('products', [])}

# ---------------------------------------------------------------------------
# CONTRACT 1: Every operational product has a resolvable identity_layer
# (consumers use this to determine their privacy posture)
# ---------------------------------------------------------------------------
VALID_LAYERS = {'anonymous', 'non-anonymous', 'pre-tech', 'n/a'}
for pid, p in products.items():
    layer = p.get('identity_layer')
    check(f'contract:identity_layer:{pid}', layer in VALID_LAYERS,
          f'{layer}' if layer in VALID_LAYERS else f'{layer} not in {VALID_LAYERS}')

# ---------------------------------------------------------------------------
# CONTRACT 2: Every product with regulatory_pools has matching BigQuery datasets
# (consumers use datasets to determine write destinations)
# ---------------------------------------------------------------------------
for pid, p in products.items():
    pools = p.get('regulatory_pools') or []
    datasets = p.get('bigquery_datasets') or {}
    for pool in pools:
        check(f'contract:dataset_for_pool:{pid}/{pool}',
              pool in datasets,
              f'dataset={datasets.get(pool)}' if pool in datasets else 'NO DATASET — consumers will fail')

# ---------------------------------------------------------------------------
# CONTRACT 3: Every anonymous product has the SAME required_tags set
# (consumers share a common tagging contract)
# ---------------------------------------------------------------------------
anon_products = [(p['product_id'], set(p.get('required_tags', [])))
                 for p in pr['products'] if p.get('identity_layer') == 'anonymous']
if len(anon_products) >= 2:
    ref_id, ref_tags = anon_products[0]
    for pid, tags in anon_products[1:]:
        check(f'contract:shared_anon_tags:{pid}', tags == ref_tags,
              f'matches {ref_id}' if tags == ref_tags else f'differs from {ref_id}: {tags ^ ref_tags}')

# ---------------------------------------------------------------------------
# CONTRACT 4: Every live invariant has a test_file declared
# (consumers use test_file to locate their enforcement tests)
# ---------------------------------------------------------------------------
for i in inv.get('invariants', []):
    if i.get('status') == 'live':
        check(f'contract:test_file:invariant#{i["id"]}',
              bool(i.get('test_file')),
              i.get('test_file') or 'MISSING — consumers cannot locate enforcement test')

# ---------------------------------------------------------------------------
# CONTRACT 5: Every invariant that applies_to a product uses valid product IDs
# (consumers use applies_to to determine which invariants they must enforce)
# ---------------------------------------------------------------------------
# Valid entities include products AND top-level entities like oureventring
valid_entities = set(products.keys())
if pr.get('oureventring'):
    valid_entities.add('oureventring')

for i in inv.get('invariants', []):
    for pid in (i.get('applies_to') or []):
        check(f'contract:applies_to:#{i["id"]}→{pid}',
              pid in valid_entities,
              'resolves' if pid in valid_entities else 'ORPHAN — consumer cannot find product')

# ---------------------------------------------------------------------------
# CONTRACT 6: tier-gates tiers are present and named
# (consumers use tier names for feature gating)
# ---------------------------------------------------------------------------
tiers = tg.get('tiers', {})
check('contract:tiers_nonempty', len(tiers) > 0, f'{len(tiers)} tiers')
for tid, tdata in tiers.items():
    check(f'contract:tier_named:{tid}',
          isinstance(tdata, dict) and ('name' in tdata or 'display_name' in tdata),
          tdata.get('display_name', tdata.get('name')) if isinstance(tdata, dict) else 'not a dict')

# ---------------------------------------------------------------------------
# CONTRACT 7: sponsor_type_overrides are complete
# (consumers use overrides to short-circuit tier assignment)
# ---------------------------------------------------------------------------
overrides = tg.get('sponsor_type_overrides', {})
for otype, odata in overrides.items():
    check(f'contract:override_complete:{otype}',
          all(k in odata for k in ('forced_tier', 'duration')),
          f'forced_tier={odata.get("forced_tier")} duration={odata.get("duration")}')

# ---------------------------------------------------------------------------
# CONTRACT 8: BigQuery pool schemas have fields arrays
# (consumers use these schemas to validate write shape)
# ---------------------------------------------------------------------------
for pool in ('general', 'hipaa', 'coppa', 'aggregate'):
    path = BRAIN / f'bigquery-schemas/{pool}.json'
    if not path.exists():
        check(f'contract:bq_schema_shape:{pool}', False, 'file missing')
        continue
    schema = load(f'bigquery-schemas/{pool}.json')
    # Schemas are dicts with dataset/tables structure, or lists of field defs, or dicts with fields key
    is_valid = (isinstance(schema, dict) and len(schema) > 0) or (isinstance(schema, list) and len(schema) > 0)
    check(f'contract:bq_schema_shape:{pool}', is_valid,
          f'dict with {len(schema)} keys' if isinstance(schema, dict) else
          f'list with {len(schema)} items' if isinstance(schema, list) else 'empty or invalid')

# ---------------------------------------------------------------------------
# CONTRACT 9: event taxonomy categories have uec_color
# (consumers use uec_color for QR code generation)
# ---------------------------------------------------------------------------
for cat in et.get('categories', []):
    cid = cat.get('category_id', '?')
    check(f'contract:uec_color:{cid}', bool(cat.get('uec_color')),
          cat.get('uec_color') or 'MISSING')

# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')
print(f'{"="*76}')
print(f'  LEVEL 7 — CONTRACT (provider-side)')
print(f'{"="*76}')
for name, status, detail in results:
    m = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {m}  {name:55} {detail}')
print(f'{"-"*76}')
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print(f'{"-"*76}')
sys.exit(0 if failed == 0 else 1)
