#!/usr/bin/env python3
"""
Level 7 — PACT (consumer-driven contracts)
============================================
What each CONSUMER expects from the brain.
These are written from the consumer's perspective:
  "I am OSE. I expect the brain to provide X."
  "I am WKRP. I expect the brain to provide Y."

If the brain ships a change that breaks a pact, the consumer's
CI will fail when it runs check_brain_contract.py. These tests
catch the breakage BEFORE it ships, in the brain's own CI.

Each pact block represents one product repo's expectations.
Add a new block when a new product repo starts consuming the brain.
"""
import json, sys, yaml
from pathlib import Path

BRAIN = Path(__file__).parent.parent if (Path(__file__).parent.parent / 'product-registry.yaml').exists() \
    else Path(__file__).parent / 'ocr-docs-brain'

results = []

def pact(consumer, name, condition, detail=''):
    results.append((f'pact:{consumer}/{name}', 'PASS' if condition else 'FAIL', detail))

def load(f):
    if f.endswith('.json'):
        return json.loads((BRAIN / f).read_text())
    return yaml.safe_load((BRAIN / f).read_text())

pr = load('product-registry.yaml')
tg = load('tier-gates.yaml')
et = load('event-taxonomy.yaml')
inv = load('architectural-invariants.yaml')

products = {p['product_id']: p for p in pr.get('products', [])}
invariant_list = inv.get('invariants', [])

# ===================================================================
# PACT: OSE (OurSharedEvents)
# The primary anonymous platform. Strictest expectations.
# ===================================================================
def ose_pacts():
    p = products.get('ose')
    pact('ose', 'exists', p is not None, 'product_id ose must exist')
    if not p:
        return

    pact('ose', 'identity_anonymous',
         p.get('identity_layer') == 'anonymous',
         f'actual={p.get("identity_layer")}')

    pact('ose', 'has_three_pools',
         set(p.get('regulatory_pools', [])) == {'general', 'hipaa', 'coppa'},
         f'actual={p.get("regulatory_pools")}')

    pact('ose', 'has_general_dataset',
         'general' in (p.get('bigquery_datasets') or {}),
         p.get('bigquery_datasets', {}).get('general', 'MISSING'))

    pact('ose', 'has_hipaa_dataset',
         'hipaa' in (p.get('bigquery_datasets') or {}),
         p.get('bigquery_datasets', {}).get('hipaa', 'MISSING'))

    pact('ose', 'has_coppa_dataset',
         'coppa' in (p.get('bigquery_datasets') or {}),
         p.get('bigquery_datasets', {}).get('coppa', 'MISSING'))

    pact('ose', 'free_in_phase1',
         'free' in (p.get('tier_availability', {}).get('phase1', [])),
         f'phase1={p.get("tier_availability", {}).get("phase1")}')

    # OSE expects 6 required tags
    tags = p.get('required_tags', [])
    expected_tags = {'corridor_id', 'venue_id', 'event_type', 'uec_code', 'regulatory_pool', 'product_id'}
    pact('ose', 'required_tags_complete',
         set(tags) == expected_tags,
         f'missing={expected_tags - set(tags)}' if set(tags) != expected_tags else f'{len(tags)} tags')

    # OSE expects invariants 1,2,3,4 to apply to it
    for inv_id in (1, 2, 3, 4):
        inv_entry = next((i for i in invariant_list if i['id'] == inv_id), None)
        pact('ose', f'invariant{inv_id}_applies',
             inv_entry and 'ose' in (inv_entry.get('applies_to') or []),
             f'applies_to={inv_entry.get("applies_to") if inv_entry else "NOT FOUND"}')

ose_pacts()

# ===================================================================
# PACT: WKRP (OurWKRP)
# Non-anonymous music/culture layer.
# ===================================================================
def wkrp_pacts():
    p = products.get('wkrp')
    pact('wkrp', 'exists', p is not None, 'product_id wkrp must exist')
    if not p:
        return

    pact('wkrp', 'identity_non_anonymous',
         p.get('identity_layer') == 'non-anonymous',
         f'actual={p.get("identity_layer")}')

    pact('wkrp', 'not_in_anonymous_pools',
         'hipaa' not in (p.get('regulatory_pools') or []) and
         'coppa' not in (p.get('regulatory_pools') or []),
         'wkrp should not route to hipaa/coppa')

    # WKRP expects invariant 10 (deprecation lock) to apply
    inv10 = next((i for i in invariant_list if i['id'] == 10), None)
    pact('wkrp', 'invariant10_applies',
         inv10 and 'wkrp' in (inv10.get('applies_to') or []),
         f'applies_to={inv10.get("applies_to") if inv10 else "NOT FOUND"}')

wkrp_pacts()

# ===================================================================
# PACT: OAW (OurAirwaves)
# Non-anonymous DJ/artist community sites. Paired with WKRP.
# ===================================================================
def oaw_pacts():
    p = products.get('oaw')
    pact('oaw', 'exists', p is not None, 'product_id oaw must exist')
    if not p:
        return

    pact('oaw', 'identity_non_anonymous',
         p.get('identity_layer') == 'non-anonymous',
         f'actual={p.get("identity_layer")}')

    pact('oaw', 'funnels_to_oureventring',
         'oureventring' in (p.get('funnels_to') or []),
         f'funnels_to={p.get("funnels_to")}')

    # OAW expects tenant isolation invariant (#9) to apply
    inv9 = next((i for i in invariant_list if i['id'] == 9), None)
    pact('oaw', 'invariant9_applies',
         inv9 and 'oaw' in (inv9.get('applies_to') or []),
         f'applies_to={inv9.get("applies_to") if inv9 else "NOT FOUND"}')

    # OAW expects deprecation lock invariant (#10) to apply
    inv10 = next((i for i in invariant_list if i['id'] == 10), None)
    pact('oaw', 'invariant10_applies',
         inv10 and 'oaw' in (inv10.get('applies_to') or []),
         f'applies_to={inv10.get("applies_to") if inv10 else "NOT FOUND"}')

oaw_pacts()

# ===================================================================
# PACT: OSM (OurSharedMagnets)
# Anonymous whitelabel engine. Multi-tenant.
# ===================================================================
def osm_pacts():
    p = products.get('osm')
    pact('osm', 'exists', p is not None, 'product_id osm must exist')
    if not p:
        return

    pact('osm', 'identity_anonymous',
         p.get('identity_layer') == 'anonymous',
         f'actual={p.get("identity_layer")}')

    # OSM expects tenant isolation invariant (#9) to apply
    inv9 = next((i for i in invariant_list if i['id'] == 9), None)
    pact('osm', 'invariant9_applies',
         inv9 and 'osm' in (inv9.get('applies_to') or []),
         f'applies_to={inv9.get("applies_to") if inv9 else "NOT FOUND"}')

osm_pacts()

# ===================================================================
# PACT: SHARED (all consumers)
# Every product repo expects these baseline contracts.
# ===================================================================
def shared_pacts():
    # All consumers expect the taxonomy to have 47+ types
    total = et.get('total_types_v1', 0)
    pact('shared', 'taxonomy_minimum_47', total >= 47, f'total={total}')

    # All consumers expect tier-gates to define at least free and mid
    tiers = tg.get('tiers', {})
    pact('shared', 'free_tier_exists', 'free' in tiers, f'tiers={list(tiers.keys())}')
    pact('shared', 'mid_tier_exists', 'mid' in tiers, f'tiers={list(tiers.keys())}')

    # All consumers expect faith organizations forced free
    faith = tg.get('sponsor_type_overrides', {}).get('faith_organization', {})
    pact('shared', 'faith_forced_free', faith.get('forced_tier') == 'free',
         f'forced_tier={faith.get("forced_tier")}')

    # All consumers expect invariant #1 (anonymous ID) to be live
    inv1 = next((i for i in invariant_list if i['id'] == 1), None)
    pact('shared', 'invariant1_live',
         inv1 and inv1.get('status') == 'live',
         f'status={inv1.get("status") if inv1 else "NOT FOUND"}')

    # All consumers expect at least 5 founding corridors
    cd = load('corridor-definitions.yaml')
    corridors = cd.get('founding_corridors', [])
    pact('shared', 'minimum_5_corridors', len(corridors) >= 5,
         f'{len(corridors)} corridors')

shared_pacts()

# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')
print(f'{"="*76}')
print(f'  LEVEL 7 — PACT (consumer-driven)')
print(f'{"="*76}')
for name, status, detail in results:
    m = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {m}  {name:55} {detail}')
print(f'{"-"*76}')
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print(f'{"-"*76}')
sys.exit(0 if failed == 0 else 1)
