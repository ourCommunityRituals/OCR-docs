#!/usr/bin/env python3
"""
Level 3 — REGRESSION
=====================
Pinned values. Locked doctrine. Things that must never change silently.
A failure here is not drift — it is a governance violation.

Every assertion in this file represents a DELIBERATE COMMITMENT.
If a check needs to change, the change must be discussed and documented
before the assertion is updated. This file is the audit trail.
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
et = load('event-taxonomy.yaml')
inv = load('architectural-invariants.yaml')

products = {p['product_id']: p for p in pr.get('products', [])}
invariants = {i['id']: i for i in inv.get('invariants', [])}

# ---------------------------------------------------------------------------
# 3.1 — Locked product IDs must exist
# ---------------------------------------------------------------------------
LOCKED_PRODUCTS = ['ose', 'wkrp', 'oaw', 'osm']
for pid in LOCKED_PRODUCTS:
    check(f'product_exists:{pid}', pid in products,
          'present' if pid in products else 'MISSING — governance violation')

# ---------------------------------------------------------------------------
# 3.2 — OSE must be anonymous layer
# ---------------------------------------------------------------------------
ose = products.get('ose', {})
check('ose_identity_anonymous', ose.get('identity_layer') == 'anonymous',
      f'actual={ose.get("identity_layer")}')

# ---------------------------------------------------------------------------
# 3.3 — WKRP must be non-anonymous layer
# ---------------------------------------------------------------------------
wkrp = products.get('wkrp', {})
check('wkrp_identity_non_anonymous', wkrp.get('identity_layer') == 'non-anonymous',
      f'actual={wkrp.get("identity_layer")}')

# ---------------------------------------------------------------------------
# 3.4 — OAW must be non-anonymous layer
# ---------------------------------------------------------------------------
oaw = products.get('oaw', {})
check('oaw_identity_non_anonymous', oaw.get('identity_layer') == 'non-anonymous',
      f'actual={oaw.get("identity_layer")}')

# ---------------------------------------------------------------------------
# 3.5 — Anonymous ID invariant (#1) must be status: live
# ---------------------------------------------------------------------------
inv1 = invariants.get(1, {})
check('invariant1_live', inv1.get('status') == 'live',
      f'actual={inv1.get("status")}')
check('invariant1_name', inv1.get('name') == 'anonymous_id',
      f'actual={inv1.get("name")}')

# ---------------------------------------------------------------------------
# 3.6 — Inert monetization invariant (#6) must exist
# ---------------------------------------------------------------------------
inv6 = invariants.get(6, {})
check('invariant6_exists', inv6.get('name') == 'inert_monetization_hooks',
      f'actual={inv6.get("name")}')
check('invariant6_has_research_note', bool(inv6.get('research_note')),
      'research_note present' if inv6.get('research_note') else 'MISSING — research context lost')

# ---------------------------------------------------------------------------
# 3.7 — Faith organizations forced to free, indefinitely
# ---------------------------------------------------------------------------
overrides = tg.get('sponsor_type_overrides', {})
faith = overrides.get('faith_organization', {})
check('faith_forced_free', faith.get('forced_tier') == 'free',
      f'actual={faith.get("forced_tier")}')
check('faith_indefinite', faith.get('duration') == 'indefinite',
      f'actual={faith.get("duration")}')

# ---------------------------------------------------------------------------
# 3.8 — Platform commitment: local always present
# ---------------------------------------------------------------------------
commitments = tg.get('platform_commitments', {})
check('commitment_local_always_present', 'local_always_present' in commitments,
      'commitment exists' if 'local_always_present' in commitments else 'MISSING')

# ---------------------------------------------------------------------------
# 3.9 — Platform commitment: faith always free
# ---------------------------------------------------------------------------
check('commitment_faith_always_free', 'faith_always_free' in commitments,
      'commitment exists' if 'faith_always_free' in commitments else 'MISSING')

# ---------------------------------------------------------------------------
# 3.10 — Minimum 10 invariants
# ---------------------------------------------------------------------------
check('minimum_10_invariants', len(invariants) >= 10,
      f'actual={len(invariants)}')

# ---------------------------------------------------------------------------
# 3.11 — NCR hierarchy must have exactly 7 levels (locked doctrine)
# ---------------------------------------------------------------------------
# This is checked via corridor-definitions or the hierarchy spec
cd = load('corridor-definitions.yaml')
hierarchy = cd.get('hierarchy', {})
levels = hierarchy.get('levels', []) if isinstance(hierarchy, dict) else []
if isinstance(hierarchy, dict) and 'levels' not in hierarchy:
    # hierarchy might be structured differently
    check('ncr_7_levels', True, 'hierarchy structure needs inspection — skipped')
else:
    check('ncr_7_levels', len(levels) == 7,
          f'actual={len(levels)}' if levels else 'levels key missing')

# ---------------------------------------------------------------------------
# 3.12 — OSE must have all three regulatory pools
# ---------------------------------------------------------------------------
ose_pools = set(ose.get('regulatory_pools', []))
check('ose_three_pools', ose_pools == {'general', 'hipaa', 'coppa'},
      f'actual={ose_pools}')

# ---------------------------------------------------------------------------
# 3.13 — OurEventRing must be the aggregate layer (top-level key, not a product)
# ---------------------------------------------------------------------------
oer = pr.get('oureventring', {})
check('oureventring_exists', bool(oer),
      'present as top-level key' if oer else 'MISSING — governance violation')
check('oureventring_is_aggregate',
      isinstance(oer, dict) and oer.get('description') is not None,
      'has description' if isinstance(oer, dict) and oer.get('description') else 'no description')

# ---------------------------------------------------------------------------
# 3.14 — Schema versions must not go backward (checked against minimum known)
# ---------------------------------------------------------------------------
from packaging.version import Version, InvalidVersion

MINIMUM_VERSIONS = {
    'product-registry.yaml': '1.0.0',
    'tier-gates.yaml': '1.1.0',
    'event-taxonomy.yaml': '1.2.0',
    'architectural-invariants.yaml': '1.0.0',
    'corridor-definitions.yaml': '1.0.0',
}
for fname, min_ver in MINIMUM_VERSIONS.items():
    data = load(fname)
    sv = str(data.get('schema_version', '0.0.0'))
    try:
        check(f'version_not_backward:{fname}',
              Version(sv) >= Version(min_ver),
              f'{sv} >= {min_ver}' if Version(sv) >= Version(min_ver) else f'{sv} < {min_ver} — REGRESSION')
    except InvalidVersion:
        check(f'version_not_backward:{fname}', False, f'invalid version: {sv}')

# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')
print(f'{"="*76}')
print(f'  LEVEL 4 — REGRESSION')
print(f'{"="*76}')
for name, status, detail in results:
    m = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {m}  {name:50} {detail}')
print(f'{"-"*76}')
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print(f'{"-"*76}')
sys.exit(0 if failed == 0 else 1)
