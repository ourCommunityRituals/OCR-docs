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
# 1.9 — Event-phase contract: canonical signature + decision rules
# ---------------------------------------------------------------------------
# Added 2026-04-26 with OSE-242 (event-phase canonical resolver). The
# contract file is optional today (only OSE consumes); when a second
# consumer arrives (WKRP, OSM, OSP, OSR, OSG, OAW, OER) the drift-detection
# arms-on logic activates. For now, validate the contract's own shape.
EVENT_PHASE_FILE = 'event-phase-contract.yaml'
if (BRAIN / EVENT_PHASE_FILE).exists():
    ep = load(EVENT_PHASE_FILE)

    # 1.9.1 — Required top-level keys
    EP_TOP_KEYS = [
        'schema_version', 'status', 'owners', 'purpose',
        'relationship_to_status', 'canonical_signature',
        'phase_derivation_rule', 'null_handling', 'required_helpers',
        'drift_detection',
    ]
    missing = [k for k in EP_TOP_KEYS if k not in ep]
    check('event_phase_top_keys', not missing,
          f'missing {missing}' if missing else f'all {len(EP_TOP_KEYS)} present')

    # 1.9.2 — Canonical signature shape
    sig = ep.get('canonical_signature') or {}
    check('event_phase_function_name',
          sig.get('function_name') == 'computeEventPhase',
          f'function_name = {sig.get("function_name")!r} (expected computeEventPhase)')
    sig_input = sig.get('input') or {}
    sig_required = sig_input.get('required_fields') or {}
    EP_INPUT_FIELDS = ['status', 'start_date', 'end_date']
    missing_input = [f for f in EP_INPUT_FIELDS if f not in sig_required]
    check('event_phase_input_fields', not missing_input,
          f'missing {missing_input}' if missing_input else 'status + start_date + end_date present')
    sig_output = sig.get('output') or {}
    EP_OUTPUT_VALUES = {'pre_event', 'event', 'post_event'}
    output_values = set(sig_output.get('values') or [])
    check('event_phase_output_enum', output_values == EP_OUTPUT_VALUES,
          f'output values = {sorted(output_values)} (expected {sorted(EP_OUTPUT_VALUES)})')

    # 1.9.3 — Phase derivation rule covers all 4 OSE-199 statuses + unknown
    rule = ep.get('phase_derivation_rule') or {}
    EP_RULE_KEYS = ['status_draft', 'status_ready', 'status_active', 'status_archived', 'status_unknown']
    missing_rule = [k for k in EP_RULE_KEYS if k not in rule]
    check('event_phase_rule_completeness', not missing_rule,
          f'missing branches {missing_rule}' if missing_rule else 'all 4 statuses + unknown covered')

    # 1.9.4 — Null-handling has all four edge cases
    nh = ep.get('null_handling') or {}
    EP_NULL_CASES = [
        'both_dates_null_status_active',
        'start_set_end_null_status_active',
        'start_null_end_set_status_active',
        'malformed_string_either_field',
    ]
    missing_nh = [k for k in EP_NULL_CASES if k not in nh]
    check('event_phase_null_handling', not missing_nh,
          f'missing edge cases {missing_nh}' if missing_nh else 'all 4 null/malformed cases covered')

    # 1.9.5 — Required helpers list
    helpers = ep.get('required_helpers') or []
    helper_names = {h.get('name') for h in helpers if isinstance(h, dict)}
    EP_HELPERS = {'explainEventPhase', 'assertSurfaceCoherence', 'VALID_EVENT_PHASES', 'EVENT_PHASE_LABELS'}
    missing_helpers = EP_HELPERS - helper_names
    check('event_phase_required_helpers', not missing_helpers,
          f'missing helpers {sorted(missing_helpers)}' if missing_helpers else f'{len(EP_HELPERS)} helpers declared')

    # 1.9.6 — Drift-detection wired
    dd = ep.get('drift_detection') or {}
    check('event_phase_drift_pyramid_check_id',
          dd.get('pyramid_check_id') == 'phase_resolver_signature_match',
          f'pyramid_check_id = {dd.get("pyramid_check_id")!r}')
    check('event_phase_drift_state',
          dd.get('state') in ('no_op_until_second_consumer', 'armed'),
          f'state = {dd.get("state")!r}')
else:
    # File optional today; presence is checked at OCR-24 time
    check('event_phase_contract_present', True,
          f'{EVENT_PHASE_FILE} not yet present (no-op until OCR-24 / first sibling consumer)')

# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')
print(f'{"="*76}')
print(f'  LEVEL 2 — SCHEMA')
print(f'{"="*76}')
for name, status, detail in results:
    m = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {m}  {name:50} {detail}')
print(f'{"-"*76}')
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print(f'{"-"*76}')
sys.exit(0 if failed == 0 else 1)
