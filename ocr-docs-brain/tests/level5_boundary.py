#!/usr/bin/env python3
"""
Level 4 — BOUNDARY
===================
Edge cases and negative tests. What happens when data is missing,
malformed, or contradictory? These tests verify that the brain's
structure prevents impossible states.
"""
import re, sys, yaml
from pathlib import Path

BRAIN = Path(__file__).parent.parent if (Path(__file__).parent.parent / 'product-registry.yaml').exists() \
    else Path(__file__).parent / 'ocr-docs-brain'

results = []

def check(name, condition, detail=''):
    results.append((name, 'PASS' if condition else 'FAIL', detail))

def load(f):
    return yaml.safe_load((BRAIN / f).read_text(encoding='utf-8'))

pr = load('product-registry.yaml')
tg = load('tier-gates.yaml')
et = load('event-taxonomy.yaml')
inv = load('architectural-invariants.yaml')
cd = load('corridor-definitions.yaml')

products = {p['product_id']: p for p in pr.get('products', [])}
invariants = inv.get('invariants', [])

# ---------------------------------------------------------------------------
# 4.1 — No product has empty regulatory_pools AND a BigQuery dataset
# (if you have datasets, you must declare which pools route to them)
# ---------------------------------------------------------------------------
for pid, p in products.items():
    pools = p.get('regulatory_pools') or []
    datasets = p.get('bigquery_datasets') or {}
    if datasets and not pools:
        check(f'pools_if_datasets:{pid}', False,
              'has bigquery_datasets but no regulatory_pools — orphaned routing')
    else:
        check(f'pools_if_datasets:{pid}', True, 'consistent')

# ---------------------------------------------------------------------------
# 4.2 — Every regulatory pool in a product has a matching BigQuery dataset
# ---------------------------------------------------------------------------
for pid, p in products.items():
    pools = p.get('regulatory_pools') or []
    datasets = p.get('bigquery_datasets') or {}
    if not pools:
        continue
    missing = [pool for pool in pools if pool not in datasets]
    check(f'pool_dataset_match:{pid}', not missing,
          f'pools without datasets: {missing}' if missing else f'all {len(pools)} pools have datasets')

# ---------------------------------------------------------------------------
# 4.3 — No event type has an empty product_origin
# ---------------------------------------------------------------------------
empty_origins = []
for cat in et.get('categories', []):
    for t in cat.get('event_types', []):
        origins = t.get('product_origin') or []
        if not origins:
            empty_origins.append(t.get('type_id'))
check('no_empty_product_origins', not empty_origins,
      f'{empty_origins[:5]}' if empty_origins else 'all types have origins')

# ---------------------------------------------------------------------------
# 4.4 — product_origin references valid product IDs
# ---------------------------------------------------------------------------
bad_refs = []
for cat in et.get('categories', []):
    for t in cat.get('event_types', []):
        for origin in (t.get('product_origin') or []):
            if origin not in products:
                bad_refs.append(f'{t.get("type_id")}→{origin}')
check('product_origin_refs_valid', not bad_refs,
      f'invalid refs: {bad_refs[:5]}' if bad_refs else 'all origins resolve')

# ---------------------------------------------------------------------------
# 4.5 — regulatory_override values are valid pool names
# ---------------------------------------------------------------------------
VALID_POOLS = {'general', 'hipaa', 'coppa'}
bad_overrides = []
for cat in et.get('categories', []):
    for t in cat.get('event_types', []):
        override = t.get('regulatory_override')
        if override and override not in VALID_POOLS:
            bad_overrides.append(f'{t.get("type_id")}={override}')
check('regulatory_override_valid', not bad_overrides,
      f'invalid: {bad_overrides[:5]}' if bad_overrides else 'all overrides valid')

# ---------------------------------------------------------------------------
# 4.6 — Anonymous products must NOT have anonymization_method: none
# ---------------------------------------------------------------------------
anon_with_none = []
for pid, p in products.items():
    if p.get('identity_layer') == 'anonymous' and p.get('anonymization_method') == 'none':
        anon_with_none.append(pid)
check('anon_not_method_none', not anon_with_none,
      f'contradiction: {anon_with_none}' if anon_with_none else 'no contradictions')

# ---------------------------------------------------------------------------
# 4.7 — Non-anonymous products must NOT claim anonymization_method: full
# ---------------------------------------------------------------------------
named_with_full = []
for pid, p in products.items():
    if p.get('identity_layer') == 'non-anonymous' and p.get('anonymization_method') == 'full':
        named_with_full.append(pid)
check('named_not_method_full', not named_with_full,
      f'contradiction: {named_with_full}' if named_with_full else 'no contradictions')

# Valid targets include products AND top-level entities like oureventring
valid_entities = set(products.keys())
if pr.get('oureventring'):
    valid_entities.add('oureventring')

# ---------------------------------------------------------------------------
# 4.8 — funnels_to must reference real product IDs or known entities
# ---------------------------------------------------------------------------
bad_funnels = []
for pid, p in products.items():
    for target in (p.get('funnels_to') or []):
        if target not in valid_entities:
            bad_funnels.append(f'{pid}→{target}')
check('funnels_to_valid', not bad_funnels,
      f'invalid: {bad_funnels[:5]}' if bad_funnels else 'all funnel targets resolve')

# ---------------------------------------------------------------------------
# 4.9 — applies_to in invariants must reference real product IDs or known entities
# ---------------------------------------------------------------------------
bad_applies = []
for i in invariants:
    for pid in (i.get('applies_to') or []):
        if pid not in valid_entities:
            bad_applies.append(f'invariant#{i.get("id")}→{pid}')
check('invariant_applies_to_valid', not bad_applies,
      f'invalid: {bad_applies[:5]}' if bad_applies else 'all applies_to resolve')

# ---------------------------------------------------------------------------
# 4.10 — No circular funnels_to (A→B→A)
# ---------------------------------------------------------------------------
def detect_cycle(products_dict):
    visited = set()
    for pid in products_dict:
        path = []
        current = pid
        while current and current not in visited:
            if current in path:
                return f'cycle: {" → ".join(path + [current])}'
            path.append(current)
            targets = products_dict.get(current, {}).get('funnels_to') or []
            current = targets[0] if targets else None
        visited.update(path)
    return None

cycle = detect_cycle(products)
check('no_funnel_cycles', cycle is None,
      cycle if cycle else 'no cycles detected')

# ---------------------------------------------------------------------------
# 4.11 — Tier availability values must be valid tier names from tier-gates
# ---------------------------------------------------------------------------
valid_tiers = set(tg.get('tiers', {}).keys())
bad_tier_refs = []
for pid, p in products.items():
    ta = p.get('tier_availability') or {}
    for phase, tiers in ta.items():
        for t in (tiers or []):
            if t not in valid_tiers:
                bad_tier_refs.append(f'{pid}.{phase}={t}')
check('tier_availability_valid_tiers', not bad_tier_refs,
      f'invalid: {bad_tier_refs[:5]}' if bad_tier_refs else 'all tier refs valid')

# ---------------------------------------------------------------------------
# 4.12 — Founding corridors must not be empty
# ---------------------------------------------------------------------------
corridors = cd.get('founding_corridors', [])
check('founding_corridors_nonempty', len(corridors) > 0,
      f'{len(corridors)} corridors' if corridors else 'EMPTY — no founding corridors')

# ---------------------------------------------------------------------------
# 4.13 — Corridor IDs must be unique
# ---------------------------------------------------------------------------
corr_ids = [c.get('corridor_id') for c in corridors]
dupe_corr = [c for c in set(corr_ids) if corr_ids.count(c) > 1]
check('corridor_ids_unique', not dupe_corr,
      f'duplicates: {dupe_corr}' if dupe_corr else f'{len(corr_ids)} corridors, all unique')

# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')
print(f'{"="*76}')
print(f'  LEVEL 5 — BOUNDARY')
print(f'{"="*76}')
for name, status, detail in results:
    m = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {m}  {name:50} {detail}')
print(f'{"-"*76}')
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print(f'{"-"*76}')
sys.exit(0 if failed == 0 else 1)
