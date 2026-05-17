#!/usr/bin/env python3
"""
Level 2 — SCHEMA
=================
Required fields per record type. Type validation. Enum constraints.
Ensures every record in the brain has the shape consumers expect.

Validates these brain artifacts:
  - product-registry.yaml
  - tier-gates.yaml
  - corridor-definitions.yaml
  - event-taxonomy.yaml
  - architectural-invariants.yaml (including rich-form fields + enrichment_history)
  - event-phase-contract.yaml (optional)
  - uec-codes.yaml (added 2026-05-17 with OSE-319 / OSE-318 brain artifact)
"""
import sys, yaml
from pathlib import Path

BRAIN = Path(__file__).parent.parent if (Path(__file__).parent.parent / 'product-registry.yaml').exists() \
    else Path(__file__).parent / 'ocr-docs-brain'

results = []

def check(name, condition, detail=''):
    results.append((name, 'PASS' if condition else 'FAIL', detail))

def load(f):
    # encoding='utf-8' explicit — Windows .read_text() defaults to cp1252 which
    # fails on non-ASCII chars (em-dash, box-drawing, etc.). Brain YAMLs may
    # contain Unicode in human-readable headers; this ensures portability across
    # Windows and Linux/Mac runners.
    return yaml.safe_load((BRAIN / f).read_text(encoding='utf-8'))

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
# 1.5 — Invariant records: required fields and enum validation (LEAN form)
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
# 1.5a — Invariant records: RICH form optional field validation (added 2026-05-17)
# ---------------------------------------------------------------------------
# Rich-form invariant entries may add: protective_statement (str),
# enforcement_statement (str), references (dict), activation_note (str).
# When present, each must be the right type and non-empty. Rich form is
# preferred for load-bearing invariants but not required.
RICH_STRING_FIELDS = ['protective_statement', 'enforcement_statement', 'activation_note']
for i in inv.get('invariants', []):
    iid = i.get('id', '?')
    for field in RICH_STRING_FIELDS:
        if field in i:
            val = i[field]
            check(f'invariant_rich_type:#{iid}.{field}',
                  isinstance(val, str) and len(val.strip()) > 30,
                  f'expected non-empty str (>30 chars), got {type(val).__name__} len={len(val) if isinstance(val, str) else "n/a"}'
                  if not (isinstance(val, str) and len(val.strip()) > 30) else 'ok')
    if 'references' in i:
        refs = i['references']
        check(f'invariant_rich_type:#{iid}.references',
              isinstance(refs, dict) and len(refs) > 0,
              f'expected non-empty dict, got {type(refs).__name__}'
              if not (isinstance(refs, dict) and len(refs) > 0) else f'{len(refs)} reference(s)')

# ---------------------------------------------------------------------------
# 1.5b — Invariant records: ID uniqueness + sequence integrity (added 2026-05-17)
# ---------------------------------------------------------------------------
ids = [i.get('id') for i in inv.get('invariants', [])]
check('invariant_ids_unique',
      len(ids) == len(set(ids)),
      f'duplicate IDs found: {[x for x in ids if ids.count(x) > 1]}' if len(ids) != len(set(ids)) else f'{len(ids)} unique IDs')

# ---------------------------------------------------------------------------
# 1.5c — enrichment_history validation (added 2026-05-17 / OSE-319)
# ---------------------------------------------------------------------------
# Top-level enrichment_history is optional but, when present, must be:
#   - a list
#   - each entry: dict with invariant_id (int), invariant_name (str),
#     from_state (str), to_state (str), date (str), pr_refs (list), rationale (str)
#   - each entry's invariant_id MUST reference an actual invariant in the file
#     (cross-reference integrity)
EH_REQUIRED = ['invariant_id', 'invariant_name', 'from_state', 'to_state', 'date', 'pr_refs', 'rationale']
EH_TYPES = {
    'invariant_id': int,
    'invariant_name': str,
    'from_state': str,
    'to_state': str,
    'date': str,
    'pr_refs': list,
    'rationale': str,
}
existing_invariant_ids = set(ids)
existing_invariant_names = {i.get('name') for i in inv.get('invariants', []) if i.get('name')}

if 'enrichment_history' in inv:
    eh = inv['enrichment_history']
    check('enrichment_history_is_list',
          isinstance(eh, list),
          f'expected list, got {type(eh).__name__}' if not isinstance(eh, list) else f'{len(eh)} entries')
    if isinstance(eh, list):
        for idx, entry in enumerate(eh):
            tag = f'enrichment_history[{idx}]'
            if not isinstance(entry, dict):
                check(f'{tag}_is_dict', False, f'expected dict, got {type(entry).__name__}')
                continue
            # Required fields
            missing = [f for f in EH_REQUIRED if f not in entry]
            check(f'{tag}_required', not missing,
                  f'missing {missing}' if missing else 'all required fields present')
            # Type validation
            for field, expected_type in EH_TYPES.items():
                if field in entry:
                    val = entry[field]
                    check(f'{tag}_type:{field}',
                          isinstance(val, expected_type),
                          f'expected {expected_type.__name__}, got {type(val).__name__}'
                          if not isinstance(val, expected_type) else 'ok')
            # Cross-reference integrity
            inv_id = entry.get('invariant_id')
            check(f'{tag}_invariant_id_exists',
                  inv_id in existing_invariant_ids,
                  f'invariant_id {inv_id} not in invariants list {sorted(existing_invariant_ids)}'
                  if inv_id not in existing_invariant_ids else f'#{inv_id} exists')
            inv_name = entry.get('invariant_name')
            check(f'{tag}_invariant_name_exists',
                  inv_name in existing_invariant_names,
                  f'invariant_name "{inv_name}" not in invariants list'
                  if inv_name not in existing_invariant_names else f'"{inv_name}" exists')

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
# 1.10 — UEC canonical artifact (added 2026-05-17 / OSE-319 + OSE-318)
# ---------------------------------------------------------------------------
# Validates uec-codes.yaml — the canonical Universal Event Code standard
# brain artifact. Structural validation only here (per existing brain
# pattern of manual checks without jsonschema lib dep). The full
# WCAG-contrast computation gate is OSE-324's deliverable and will live
# in a future level addition (likely level3_unit.py).
UEC_FILE = 'uec-codes.yaml'
if (BRAIN / UEC_FILE).exists():
    uec = load(UEC_FILE)

    # 1.10.1 — Required top-level keys
    UEC_TOP_KEYS = ['schema_version', 'version', 'provenance', 'palette_usage',
                    'verticals', 'codes', 'changelog']
    missing_uec = [k for k in UEC_TOP_KEYS if k not in uec]
    check('uec_top_keys', not missing_uec,
          f'missing {missing_uec}' if missing_uec else f'all {len(UEC_TOP_KEYS)} present')

    # 1.10.2 — Version field shape
    ver = uec.get('version', '')
    version_ok = isinstance(ver, str) and ver.replace('v', '').replace('.', '').isdigit()
    check('uec_version_shape', version_ok,
          ver if version_ok else f'version = {ver!r} (expected like "1.1" or "v1.1")')

    # 1.10.3 — Exactly 11 codes (7 core + 4 extensions)
    codes = uec.get('codes', [])
    count_ok = isinstance(codes, list) and len(codes) == 11
    check('uec_code_count', count_ok,
          f'{len(codes)} codes' if count_ok else f'expected 11, got {len(codes) if isinstance(codes, list) else "non-list"}')

    # 1.10.4 — Every code has required fields (dual palette: scan_hex + display_hex)
    UEC_CODE_REQUIRED = ['id', 'num', 'label', 'scan_hex', 'display_hex',
                         'semantics', 'description', 'verticals', 'status',
                         'wcag_grade', 'rationale']
    UEC_CODE_STATUS_ENUM = ['KEEP', 'ADD', 'CHANGE']
    UEC_CODE_WCAG_ENUM = ['AAA', 'AA']  # FAIL is unrepresentable (brand promise)
    for code in codes:
        cid = code.get('id', '?') if isinstance(code, dict) else '?'
        if not isinstance(code, dict):
            check(f'uec_code_is_dict:{cid}', False, f'expected dict')
            continue
        missing_c = [f for f in UEC_CODE_REQUIRED if f not in code]
        check(f'uec_code_required:{cid}', not missing_c,
              f'missing {missing_c}' if missing_c else 'all required fields')
        # Status enum
        st = code.get('status')
        check(f'uec_code_status_enum:{cid}', st in UEC_CODE_STATUS_ENUM,
              f'{st} not in {UEC_CODE_STATUS_ENUM}' if st not in UEC_CODE_STATUS_ENUM else f'{st}')
        # WCAG grade enum (FAIL not permitted)
        wg = code.get('wcag_grade')
        check(f'uec_code_wcag_grade_enum:{cid}', wg in UEC_CODE_WCAG_ENUM,
              f'{wg} not in {UEC_CODE_WCAG_ENUM} (FAIL is unrepresentable)' if wg not in UEC_CODE_WCAG_ENUM else f'{wg}')
        # Hex format
        for hex_field in ('scan_hex', 'display_hex'):
            hex_val = code.get(hex_field, '')
            valid_hex = (isinstance(hex_val, str) and len(hex_val) == 7
                         and hex_val.startswith('#')
                         and all(c in '0123456789abcdefABCDEF' for c in hex_val[1:]))
            check(f'uec_code_{hex_field}_format:{cid}', valid_hex,
                  f'{hex_field} = {hex_val!r} (expected #RRGGBB)' if not valid_hex else hex_val)
        # rationale sub-fields
        rat = code.get('rationale')
        if isinstance(rat, dict):
            rat_required = ['psychology', 'why', 'contexts', 'verdict']
            missing_rat = [f for f in rat_required if f not in rat]
            check(f'uec_code_rationale_required:{cid}', not missing_rat,
                  f'missing rationale subs: {missing_rat}' if missing_rat else 'complete')

    # 1.10.5 — All code IDs unique
    code_ids = [c.get('id') for c in codes if isinstance(c, dict)]
    check('uec_code_ids_unique',
          len(code_ids) == len(set(code_ids)),
          f'duplicates: {[x for x in code_ids if code_ids.count(x) > 1]}' if len(code_ids) != len(set(code_ids)) else f'{len(code_ids)} unique')

    # 1.10.6 — All code nums unique
    code_nums = [c.get('num') for c in codes if isinstance(c, dict)]
    check('uec_code_nums_unique',
          len(code_nums) == len(set(code_nums)),
          f'duplicates: {[x for x in code_nums if code_nums.count(x) > 1]}' if len(code_nums) != len(set(code_nums)) else f'{len(code_nums)} unique')

    # 1.10.7 — Every code's verticals[] is a subset of top-level verticals
    top_verticals = set(uec.get('verticals', []))
    for code in codes:
        if not isinstance(code, dict): continue
        cid = code.get('id', '?')
        code_v = set(code.get('verticals', []))
        bad = code_v - top_verticals
        check(f'uec_code_verticals_subset:{cid}', not bad,
              f'not in top-level: {sorted(bad)}' if bad else f'{len(code_v)} verticals')

    # 1.10.8 — Schema file exists alongside the artifact (commitment from PR #49)
    schema_present = (BRAIN / 'uec-codes.schema.json').exists()
    check('uec_schema_file_present', schema_present,
          'present' if schema_present else 'uec-codes.schema.json missing alongside uec-codes.yaml')
else:
    check('uec_codes_file_present', False,
          f'{UEC_FILE} missing — required artifact since OSE-318 merge 2026-05-17')

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
