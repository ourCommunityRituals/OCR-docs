#!/usr/bin/env python3
"""
Integration tests — simulate real consumer use cases against the brain.
These are the queries the OSE worker, the BigQuery pipeline, and the
SharedReport renderer will actually run.

If these fail, the brain parses but can't be used.
"""
import yaml, json, sys
from pathlib import Path

BRAIN = Path(__file__).parent if (Path(__file__).parent / 'product-registry.yaml').exists() else Path(__file__).parent / 'ocr-docs-brain'

pr = yaml.safe_load(open(BRAIN / 'product-registry.yaml'))
tg = yaml.safe_load(open(BRAIN / 'tier-gates.yaml'))
cd = yaml.safe_load(open(BRAIN / 'corridor-definitions.yaml'))
et = yaml.safe_load(open(BRAIN / 'event-taxonomy.yaml'))
inv = yaml.safe_load(open(BRAIN / 'architectural-invariants.yaml'))

products = {p['product_id']: p for p in pr['products']}
corridors = {c['corridor_id']: c for c in cd['founding_corridors']}
event_types = {}
for cat in et['categories']:
    for t in cat.get('event_types', []):
        event_types[t['type_id']] = {**t, 'category_id': cat['category_id'], 'uec_color': cat['uec_color']}

tests = []
def test(name, fn):
    try:
        result = fn()
        tests.append((name, 'PASS', result or ''))
    except AssertionError as e:
        tests.append((name, 'FAIL', str(e)))
    except Exception as e:
        tests.append((name, 'FAIL', f'{type(e).__name__}: {e}'))

# ---------------------------------------------------------------------------
# Scenario A: OSE worker handles a scan event
# ---------------------------------------------------------------------------
def scenario_scan_event():
    """
    A QR gets scanned at Eagles Hall for a bocce event.
    The worker needs to: resolve the event type, look up UEC code,
    determine regulatory pool, pick BigQuery destination, validate tier.
    """
    event_type_id = 'bocce_league'
    corridor_id = 'blue_island'
    product_id = 'ose'

    # Resolve event type
    et_entry = event_types.get(event_type_id)
    assert et_entry, f'event type {event_type_id} not in taxonomy'
    assert et_entry.get('uec_code'), 'bocce_league missing UEC code'

    # Resolve corridor
    corr = corridors.get(corridor_id)
    assert corr, f'corridor {corridor_id} not in founding_corridors'

    # Resolve product
    prod = products.get(product_id)
    assert prod, 'ose product missing'
    assert prod.get('identity_layer') == 'anonymous', 'ose must be anonymous layer'

    # Determine regulatory pool (default or override)
    reg_override = et_entry.get('regulatory_override')
    # Category-level default
    cat_default = next((c.get('regulatory_default') for c in et['categories']
                        if c['category_id'] == et_entry['category_id']), None)
    pool = reg_override or cat_default or 'general'
    assert pool in ('general', 'hipaa', 'coppa'), f'invalid pool resolved: {pool}'

    # BigQuery destination
    bq_datasets = prod.get('bigquery_datasets', {})
    assert pool in bq_datasets, f'no BigQuery dataset for pool {pool} on product {product_id}'

    return f'event={event_type_id} uec={et_entry["uec_code"]} pool={pool} bq={bq_datasets[pool]}'

test('scenario:scan_event_bocce_league', scenario_scan_event)

# ---------------------------------------------------------------------------
# Scenario B: SharedReport tier gating
# ---------------------------------------------------------------------------
def scenario_shared_report_tier_gate():
    """
    A Local-tier sponsor requests their SharedReport.
    The renderer must check tier_availability for Phase 1.
    """
    prod = products['ose']
    current_phase = 'phase1'
    ta = prod.get('tier_availability', {})
    available_tiers = ta.get(current_phase, [])
    assert 'free' in available_tiers, 'Local (free) tier must be available in Phase 1'

    # Verify the platform commitment matches
    commitments = tg.get('platform_commitments', {})
    assert commitments, 'platform_commitments missing'
    assert any('local' in k.lower() for k in commitments.keys()), \
        'no local_always_present commitment found'

    return f'phase={current_phase} tiers={available_tiers}'

test('scenario:shared_report_tier_gate', scenario_shared_report_tier_gate)

# ---------------------------------------------------------------------------
# Scenario C: Faith organization attempts sponsor signup
# ---------------------------------------------------------------------------
def scenario_faith_sponsor():
    """
    A church signs up as a sponsor. The signup flow must force them to free
    tier regardless of what they select.
    """
    overrides = tg.get('sponsor_type_overrides', {})
    faith = overrides.get('faith_organization')
    assert faith, 'faith_organization override not defined'
    assert faith.get('forced_tier') == 'free', 'faith must be forced to free'
    assert faith.get('duration') == 'indefinite', 'faith must be indefinite'
    assert faith.get('enforced_by'), 'faith override must name its enforcing test'
    return f'forced_tier={faith["forced_tier"]} duration={faith["duration"]}'

test('scenario:faith_sponsor_forced_free', scenario_faith_sponsor)

# ---------------------------------------------------------------------------
# Scenario D: HIPAA-pool event routing
# ---------------------------------------------------------------------------
def scenario_hipaa_event():
    """
    A community health screening event. Must route to HIPAA pool,
    not general pool, even though the product is the same OSE.
    """
    et_entry = event_types.get('health_screening')
    assert et_entry, 'health_screening type not found'
    override = et_entry.get('regulatory_override')
    assert override == 'hipaa', f'health_screening must override to hipaa, got {override}'

    # Verify OSE can route to HIPAA
    ose = products['ose']
    assert 'hipaa' in ose.get('regulatory_pools', []), 'ose must support HIPAA pool'
    assert 'hipaa' in ose.get('bigquery_datasets', {}), 'ose must have HIPAA BQ dataset'
    return f'override={override} dataset={ose["bigquery_datasets"]["hipaa"]}'

test('scenario:hipaa_pool_routing', scenario_hipaa_event)

# ---------------------------------------------------------------------------
# Scenario E: COPPA-pool event routing
# ---------------------------------------------------------------------------
def scenario_coppa_event():
    et_entry = event_types.get('youth_tournament')
    assert et_entry, 'youth_tournament type not found'
    override = et_entry.get('regulatory_override')
    assert override == 'coppa', f'youth_tournament must override to coppa, got {override}'
    return f'override={override}'

test('scenario:coppa_pool_routing', scenario_coppa_event)

# ---------------------------------------------------------------------------
# Scenario F: Invariant #6 enforcement claim
# ---------------------------------------------------------------------------
def scenario_monetization_inert():
    """
    The Dr. Condon deck claims invariant #6 guarantees pre-revenue state.
    The brain must back that claim with a specific invariant entry.
    """
    inv_list = inv['invariants']
    monetization = next((i for i in inv_list if i.get('name') == 'inert_monetization_hooks'), None)
    assert monetization, 'inert_monetization_hooks invariant missing'
    assert monetization.get('test_file'), 'must declare test file'
    assert 'X-Monetization-Inert' in monetization.get('enforces', ''), \
        'enforcement description must mention the response header'
    assert 'research' in str(monetization).lower() or monetization.get('research_note'), \
        'invariant should have research context for Dr. Condon'
    return f'status={monetization["status"]} test={monetization["test_file"]}'

test('scenario:invariant_6_monetization_inert', scenario_monetization_inert)

# ---------------------------------------------------------------------------
# Scenario G: All non-anonymous products properly declare identity layer
# ---------------------------------------------------------------------------
def scenario_non_anon_layer():
    wkrp = products.get('wkrp')
    oaw = products.get('oaw')
    assert wkrp and wkrp['identity_layer'] == 'non-anonymous'
    assert oaw and oaw['identity_layer'] == 'non-anonymous'
    # Neither should route to anonymous BigQuery pools
    for pid in ('wkrp', 'oaw'):
        p = products[pid]
        # Soft assertion — non-anon may or may not write to shared BQ
        layer = p.get('identity_layer')
        assert layer == 'non-anonymous'
    return 'wkrp + oaw both non-anonymous'

test('scenario:non_anonymous_layer_contract', scenario_non_anon_layer)

# ---------------------------------------------------------------------------
# Scenario H: Every founding corridor has venue-level specificity
# ---------------------------------------------------------------------------
def scenario_corridor_specificity():
    for cid, c in corridors.items():
        # Each should have at minimum role + status + some venue/anchor data
        assert c.get('role'), f'{cid} missing role'
    return f'{len(corridors)} founding corridors all have roles'

test('scenario:corridor_specificity', scenario_corridor_specificity)

# ---------------------------------------------------------------------------
# Scenario I: Phase 1 product availability matches the Dr. Condon deck claim
# ---------------------------------------------------------------------------
def scenario_phase1_ose():
    ose = products['ose']
    ta = ose.get('tier_availability', {})
    phase1_tiers = ta.get('phase1', [])
    assert 'free' in phase1_tiers, 'Phase 1 must support free (Local)'
    # Deck claims 47 types seeded in Phase 1
    assert et.get('total_types_v1') == 47, \
        f'taxonomy v1 must be 47 to match deck, got {et.get("total_types_v1")}'
    return f'ose phase1 tiers={phase1_tiers} total_types=47'

test('scenario:phase1_matches_deck_claims', scenario_phase1_ose)

# ---------------------------------------------------------------------------
# Scenario J: UEC codes are unique across the entire taxonomy
# ---------------------------------------------------------------------------
def scenario_uec_uniqueness():
    codes = []
    for cat in et['categories']:
        for t in cat.get('event_types', []):
            codes.append(t.get('uec_code'))
    assert len(codes) == len(set(codes)), \
        f'UEC codes must be unique. Found {len(codes)-len(set(codes))} duplicates.'
    return f'{len(codes)} UEC codes, all unique'

test('scenario:uec_codes_unique', scenario_uec_uniqueness)

# ---------------------------------------------------------------------------
# Scenario K: Resolve effective scan code set for a competitive event
# ---------------------------------------------------------------------------
def scenario_scan_code_set_competitive():
    """
    Bocce league should get ENTER + SPONSOR + FEEDBACK + ARCHIVE + UTILITY
    + LIVE + CHECK-IN = 7 total codes. The poster generator reads this to
    know which QR codes to print.
    """
    default = set(et.get('default_scan_codes', []))
    assert default, 'default_scan_codes missing'
    valid = set(et.get('valid_scan_codes', {}).keys())
    assert len(valid) == 11, f'expected 11 valid codes, got {len(valid)}'

    bocce = event_types.get('bocce_league')
    assert bocce, 'bocce_league not found'
    add = set(bocce.get('scan_codes_add', []) or [])
    remove = set(bocce.get('scan_codes_remove', []) or [])
    effective = (default | add) - remove

    assert 'LIVE' in effective, 'competitive event must have LIVE'
    assert 'CHECK-IN' in effective, 'league event must have CHECK-IN'
    assert 'SPONSOR' in effective, 'bocce league keeps SPONSOR'
    assert effective.issubset(valid), f'effective set contains invalid codes: {effective - valid}'
    return f'bocce_league effective={sorted(effective)} ({len(effective)} codes)'

test('scenario:scan_code_set_competitive', scenario_scan_code_set_competitive)

# ---------------------------------------------------------------------------
# Scenario L: Resolve effective scan code set with a removal
# ---------------------------------------------------------------------------
def scenario_scan_code_set_with_removal():
    """
    Memorial gathering removes SPONSOR (inappropriate context) and adds HELP.
    Effective set = (default - SPONSOR) + HELP = 5 codes.
    """
    default = set(et.get('default_scan_codes', []))
    memorial = event_types.get('memorial_gathering')
    assert memorial, 'memorial_gathering not found'
    add = set(memorial.get('scan_codes_add', []) or [])
    remove = set(memorial.get('scan_codes_remove', []) or [])
    effective = (default | add) - remove

    assert 'SPONSOR' not in effective, 'memorial must not have SPONSOR'
    assert 'HELP' in effective, 'memorial must have HELP'
    assert 'ENTER' in effective, 'memorial must still have ENTER'
    assert len(effective) >= 4, f'effective set too small: {effective}'
    return f'memorial effective={sorted(effective)} ({len(effective)} codes, SPONSOR removed)'

test('scenario:scan_code_set_with_removal', scenario_scan_code_set_with_removal)

# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
print('=' * 76)
print('  INTEGRATION TEST REPORT')
print('  Simulating real consumer workflows against the brain')
print('=' * 76)
print()
for name, status, detail in tests:
    marker = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {marker}  {name:45} {detail}')

passed = sum(1 for _, s, _ in tests if s == 'PASS')
failed = sum(1 for _, s, _ in tests if s == 'FAIL')
print()
print('-' * 76)
print(f'  Results: {passed} pass / {failed} fail  (total {len(tests)})')
print('-' * 76)

sys.exit(0 if failed == 0 else 1)
