#!/usr/bin/env python3
"""
Level 5 — INTEGRATION
======================
Cross-file coherence. These tests simulate real consumer workflows
that traverse multiple brain files in a single operation.
If these fail, individual files are correct but the brain as a whole is incoherent.
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

def check(name, fn):
    try:
        detail = fn()
        results.append((name, 'PASS', detail or ''))
    except AssertionError as e:
        results.append((name, 'FAIL', str(e)))
    except Exception as e:
        results.append((name, 'FAIL', f'{type(e).__name__}: {e}'))

def load(f):
    if f.endswith('.json'):
        return json.loads((BRAIN / f).read_text(encoding='utf-8'))
    return yaml.safe_load((BRAIN / f).read_text(encoding='utf-8'))

pr = load('product-registry.yaml')
tg = load('tier-gates.yaml')
cd = load('corridor-definitions.yaml')
et = load('event-taxonomy.yaml')
inv = load('architectural-invariants.yaml')

products = {p['product_id']: p for p in pr.get('products', [])}
event_types = {}
for cat in et.get('categories', []):
    for t in cat.get('event_types', []):
        event_types[t['type_id']] = {**t, 'category_id': cat['category_id']}

# ---------------------------------------------------------------------------
# 5.1 — Scan event full resolution chain
# ---------------------------------------------------------------------------
def scan_event_chain():
    """Resolve bocce_league: taxonomy → product → pools → BigQuery dataset."""
    et_entry = event_types.get('bocce_league')
    assert et_entry, 'bocce_league not in taxonomy'
    assert et_entry.get('uec_code'), 'bocce_league missing UEC code'
    prod = products.get('ose')
    assert prod, 'ose product missing'
    pool = et_entry.get('regulatory_override') or 'general'
    assert pool in prod.get('bigquery_datasets', {}), f'no dataset for pool {pool}'
    return f'bocce_league → ose → {pool} → {prod["bigquery_datasets"][pool]}'

check('scan_event_full_chain', scan_event_chain)

# ---------------------------------------------------------------------------
# 5.2 — HIPAA is a DECLINED regime for OSE — it must NOT route there.
#       (OCR_STANDARD_declinedRegimes.md; OSE-1220.) The governance layer must
#       not carry hipaa/coppa/soppa as an active OSE pool or dataset.
# ---------------------------------------------------------------------------
def hipaa_declined_not_routed():
    prod = products.get('ose')
    declined = {'hipaa', 'coppa', 'soppa'}
    pools = set(prod.get('regulatory_pools', []))
    datasets = set(prod.get('bigquery_datasets', {}))
    assert pools.isdisjoint(declined), f'declined regime in OSE pools: {sorted(pools & declined)}'
    assert datasets.isdisjoint(declined), f'declined regime in OSE datasets: {sorted(datasets & declined)}'
    return 'OSE declines hipaa/coppa/soppa — general pool only'

check('hipaa_declined_not_routed', hipaa_declined_not_routed)

# ---------------------------------------------------------------------------
# 5.2b — Declined regimes are refused FLEET-WIDE, not just for OSE (OSE-1296).
#        OCR_STANDARD_declinedRegimes.md is fleet-scoped, but #122 narrowed only
#        the OSE product block; OSM carried stranded hipaa/coppa pools+datasets
#        and the warehouse aggregate layer listed them as source pools. These
#        checks guard the back-propagation: (a) no product may carry a declined
#        regime as an active pool or dataset; (b) the aggregate warehouse layer
#        must list no declined source pool; (c) declined warehouse pool entries
#        are retained ONLY as status=declined records (mark, don't erase — ADR-018).
# ---------------------------------------------------------------------------
DECLINED_REGIMES = {'hipaa', 'coppa', 'soppa'}

def no_product_carries_declined_regime():
    offenders = {}
    for pid, prod in products.items():
        active = set(prod.get('regulatory_pools') or []) | set(prod.get('bigquery_datasets') or {})
        bad = active & DECLINED_REGIMES
        if bad:
            offenders[pid] = sorted(bad)
    assert not offenders, f'declined regime as active pool/dataset in products: {offenders}'
    return f'no product carries a declined regime ({len(products)} products checked)'

check('no_product_carries_declined_regime', no_product_carries_declined_regime)

def aggregate_excludes_declined_source_pools():
    agg = pr.get('oureventring', {}).get('pools', {}).get('aggregate', {})
    bad = set(agg.get('source_pools') or []) & DECLINED_REGIMES
    assert not bad, f'aggregate.source_pools lists declined regime(s): {sorted(bad)}'
    return f'aggregate source_pools active-only: {sorted(agg.get("source_pools") or [])}'

check('aggregate_excludes_declined_source_pools', aggregate_excludes_declined_source_pools)

def warehouse_declined_pools_are_marked():
    pools = pr.get('oureventring', {}).get('pools', {})
    unmarked = [n for n in ('hipaa', 'coppa') if n in pools and pools[n].get('status') != 'declined']
    assert not unmarked, f'warehouse pool(s) present but not marked status=declined: {unmarked}'
    return 'warehouse hipaa/coppa retained only as status=declined records'

check('warehouse_declined_pools_are_marked', warehouse_declined_pools_are_marked)

# ---------------------------------------------------------------------------
# 5.3 — COPPA routing chain
# ---------------------------------------------------------------------------
def coppa_chain():
    et_entry = event_types.get('youth_tournament')
    assert et_entry, 'youth_tournament not in taxonomy'
    assert et_entry.get('regulatory_override') == 'coppa'
    return f'youth_tournament → coppa'

check('coppa_routing_chain', coppa_chain)

# ---------------------------------------------------------------------------
# 5.4 — SharedReport tier gating
# ---------------------------------------------------------------------------
def shared_report_tier():
    prod = products['ose']
    ta = prod.get('tier_availability', {})
    p1 = ta.get('phase1', [])
    assert 'free' in p1, 'free tier must be in phase1'
    commitments = tg.get('platform_commitments', {})
    assert 'local_always_present' in commitments
    return f'phase1 tiers={p1}'

check('shared_report_tier_gate', shared_report_tier)

# ---------------------------------------------------------------------------
# 5.5 — Faith sponsor forced free
# ---------------------------------------------------------------------------
def faith_sponsor():
    overrides = tg.get('sponsor_type_overrides', {})
    faith = overrides.get('faith_organization')
    assert faith, 'faith_organization override missing'
    assert faith['forced_tier'] == 'free'
    assert faith['duration'] == 'indefinite'
    assert faith.get('enforced_by'), 'must name enforcing test'
    return f'forced_tier={faith["forced_tier"]}'

check('faith_sponsor_forced_free', faith_sponsor)

# ---------------------------------------------------------------------------
# 5.6 — Invariant #6 research claim integrity
# ---------------------------------------------------------------------------
def invariant6_claim():
    inv6 = next((i for i in inv['invariants'] if i['name'] == 'inert_monetization_hooks'), None)
    assert inv6, 'inert_monetization_hooks missing'
    assert inv6.get('test_file'), 'must declare test file'
    assert 'X-Monetization-Inert' in inv6.get('enforces', ''), 'must reference header'
    assert inv6.get('research_note'), 'must have research context'
    return f'status={inv6["status"]}'

check('invariant6_research_claim', invariant6_claim)

# ---------------------------------------------------------------------------
# 5.7 — Non-anonymous layer contract
# ---------------------------------------------------------------------------
def non_anon_layer():
    for pid in ('wkrp', 'oaw'):
        p = products.get(pid)
        assert p, f'{pid} missing'
        assert p['identity_layer'] == 'non-anonymous', f'{pid} wrong layer'
    return 'wkrp + oaw both non-anonymous'

check('non_anonymous_layer_contract', non_anon_layer)

# ---------------------------------------------------------------------------
# 5.8 — Anonymous required_tags consistency
# ---------------------------------------------------------------------------
def anon_tags_consistent():
    anon = [p for p in pr['products'] if p.get('identity_layer') == 'anonymous']
    if not anon:
        return 'no anonymous products'
    ref = set(anon[0].get('required_tags', []))
    for p in anon[1:]:
        tags = set(p.get('required_tags', []))
        assert tags == ref, f'{p["product_id"]} tags {tags} != {ref}'
    return f'{len(anon)} anonymous products share identical tags'

check('anonymous_tags_consistent', anon_tags_consistent)

# ---------------------------------------------------------------------------
# 5.9 — Corridor specificity
# ---------------------------------------------------------------------------
def corridor_specificity():
    corridors = cd.get('founding_corridors', [])
    for c in corridors:
        assert c.get('role'), f'{c.get("corridor_id")} missing role'
    return f'{len(corridors)} corridors all have roles'

check('corridor_specificity', corridor_specificity)

# ---------------------------------------------------------------------------
# 5.10 — Phase 1 alignment
# ---------------------------------------------------------------------------
def phase1_alignment():
    ose = products['ose']
    ta = ose.get('tier_availability', {})
    p1 = ta.get('phase1', [])
    assert 'free' in p1
    assert et.get('total_types_v1') == 47
    return f'ose phase1={p1} types=47'

check('phase1_alignment', phase1_alignment)

# ---------------------------------------------------------------------------
# 5.11 — UEC codes globally unique
# ---------------------------------------------------------------------------
def uec_unique():
    codes = [t.get('uec_code') for cat in et['categories'] for t in cat.get('event_types', [])]
    assert len(codes) == len(set(codes)), f'{len(codes)-len(set(codes))} duplicates'
    return f'{len(codes)} codes, all unique'

check('uec_codes_unique', uec_unique)

# ---------------------------------------------------------------------------
# 5.12 — BigQuery schemas exist for all four pools
# ---------------------------------------------------------------------------
def bq_schemas():
    for pool in ('general', 'hipaa', 'coppa', 'aggregate'):
        path = BRAIN / f'bigquery-schemas/{pool}.json'
        assert path.exists(), f'{pool}.json missing'
        data = json.loads(path.read_text(encoding='utf-8'))
        assert data, f'{pool}.json is empty'
    return 'all 4 pool schemas present and non-empty'

check('bigquery_schemas_complete', bq_schemas)

# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')
print(f'{"="*76}')
print(f'  LEVEL 6 — INTEGRATION')
print(f'{"="*76}')
for name, status, detail in results:
    m = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {m}  {name:50} {detail}')
print(f'{"-"*76}')
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print(f'{"-"*76}')
sys.exit(0 if failed == 0 else 1)
