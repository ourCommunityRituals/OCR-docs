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
import sys, re, json, yaml
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
    'architectural-invariants.yaml': ['schema_version', 'invariant_groups', 'invariants'],
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
# 1.2b — npm_scope present for every product in Invariant #22's applies_to.
# The cross-repo import guard (scripts/check_cross_repo_imports.py) derives the
# prohibited sibling scopes from product-registry `npm_scope`. A product that
# #22 applies to MUST carry a scope or the guard silently under-enforces.
# Scoped to applies_to (not all products) so governance/planned products that
# are not npm packages (ocr-docs, oot) do not fail.
# ---------------------------------------------------------------------------
_inv = load('architectural-invariants.yaml')
_invs = _inv.get('invariants', []) if isinstance(_inv, dict) else []
if isinstance(_invs, dict):
    _invs = _invs.get('invariants', [])
_applies22 = next((i.get('applies_to', []) for i in _invs
                   if isinstance(i, dict) and i.get('id') == 22), [])
for p in pr.get('products', []):
    if p.get('product_id') in _applies22:
        scope = p.get('npm_scope')
        check(f'npm_scope:{p.get("product_id")}',
              isinstance(scope, str) and scope.startswith('@'),
              'Invariant #22 applies_to product must carry npm_scope (starts with @)')

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
INV_REQUIRED = ['id', 'name', 'label', 'group', 'group_order', 'title', 'status', 'test_file', 'enforces', 'applies_to']
# planned invariants do not have a spec yet — test_file is deferred until activation
INV_REQUIRED_PLANNED = [f for f in INV_REQUIRED if f != 'test_file']
# retired (added 2026-09-02, OSE-1194): the invariant's subject no longer exists
# (e.g. #11/#12 self-hosted runner apparatus). Entries are never deleted or
# renumbered; a retired entry keeps its historic test_file name for traceability
# even though the spec is gone from the substrate — check_brain_contract.py does
# not require the file for retired entries.
INV_STATUS_ENUM = ['live', 'partial', 'planned', 'retired']
INV_ENFORCEMENT_KIND_ENUM = ['brain_script']  # extend as new kinds are added
for i in inv.get('invariants', []):
    iid = i.get('id', '?')
    req = INV_REQUIRED_PLANNED if i.get('status') == 'planned' else INV_REQUIRED
    missing = [f for f in req if f not in i]
    check(f'invariant_required:#{iid}', not missing,
          f'missing {missing}' if missing else 'complete')
    status = i.get('status')
    check(f'invariant_status_enum:#{iid}', status in INV_STATUS_ENUM,
          f'{status} not in {INV_STATUS_ENUM}' if status not in INV_STATUS_ENUM else f'{status}')
    # enforcement_kind (OSE-1288 / F13): optional; when present must be a known
    # kind. `brain_script` = enforced by a WIRED brain-resident live-read guard
    # (verified by check_brain_contract._guard_step_wired), not a repo-local file.
    if 'enforcement_kind' in i:
        ek = i['enforcement_kind']
        check(f'invariant_enforcement_kind_enum:#{iid}', ek in INV_ENFORCEMENT_KIND_ENUM,
              f'{ek} not in {INV_ENFORCEMENT_KIND_ENUM}' if ek not in INV_ENFORCEMENT_KIND_ENUM else f'{ek}')

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
# 1.5d — status_summary consistency (added 2026-05-20)
# ---------------------------------------------------------------------------
# status_summary is a derived aggregate: live/partial/planned counts, total,
# and rich_form/lean_form counts. The file header used to read "Updated
# manually until level2_schema.py auto-computes" — this check closes that
# gap. It recomputes every count from the actual invariant records and
# asserts the declared summary matches. Catches:
#   - a status flip whose author forgot to update the summary (the #5 / #8
#     activation arc hand-checked this on every brain PR)
#   - a dropped or malformed `status_summary:` block (the OCR-docs#58
#     incident — a missing parent key broke YAML parse on brain main)
#   - drift between rich_form / lean_form and the real form distribution
# An invariant is "rich form" iff it carries a non-empty enforcement_statement
# (the load-bearing rich-form field; protective_statement + references travel
# with it). Form is orthogonal to status — a rich invariant may be partial.
invariants = inv.get('invariants', [])
ss = inv.get('status_summary')
check('status_summary_present',
      isinstance(ss, dict),
      f'expected dict, got {type(ss).__name__}' if not isinstance(ss, dict)
      else f'{len(ss)} keys')

if isinstance(ss, dict):
    SS_KEYS = ['live', 'partial', 'planned', 'retired', 'total', 'rich_form', 'lean_form']
    missing_ss = [k for k in SS_KEYS if k not in ss]
    check('status_summary_keys', not missing_ss,
          f'missing {missing_ss}' if missing_ss else f'all {len(SS_KEYS)} present')

    # Recompute every count straight from the invariant records.
    actual = {
        'live':    sum(1 for i in invariants if i.get('status') == 'live'),
        'partial': sum(1 for i in invariants if i.get('status') == 'partial'),
        'planned': sum(1 for i in invariants if i.get('status') == 'planned'),
        'retired': sum(1 for i in invariants if i.get('status') == 'retired'),
        'total':   len(invariants),
        'rich_form': sum(1 for i in invariants
                         if isinstance(i.get('enforcement_statement'), str)
                         and i['enforcement_statement'].strip()),
    }
    actual['lean_form'] = actual['total'] - actual['rich_form']

    for key, expected in actual.items():
        declared = ss.get(key)
        check(f'status_summary_count:{key}', declared == expected,
              f'declared {declared}, recomputed {expected}' if declared != expected
              else f'{declared}')

    # Internal arithmetic — the summary must be self-consistent even before
    # it is compared against the records.
    lpp = ss.get('live', 0) + ss.get('partial', 0) + ss.get('planned', 0) + ss.get('retired', 0)
    check('status_summary_sum:live+partial+planned+retired==total',
          lpp == ss.get('total'),
          f'live+partial+planned+retired = {lpp}, total = {ss.get("total")}'
          if lpp != ss.get('total') else f'{lpp}')
    rl = ss.get('rich_form', 0) + ss.get('lean_form', 0)
    check('status_summary_sum:rich+lean==total',
          rl == ss.get('total'),
          f'rich_form+lean_form = {rl}, total = {ss.get("total")}'
          if rl != ss.get('total') else f'{rl}')

# ---------------------------------------------------------------------------
# 1.5e — Invariant role sections (ADR-004 role-ready schema, added 2026-06-05)
# ---------------------------------------------------------------------------
# Per ADR-004, each rich-form invariant may declare up to six OPTIONAL role
# sections: pm, devops, sre, frontend, playwright, postman. Validated only when
# present. Two legal forms per section:
#   (a) not-applicable:  {applicable: false, reason: <non-empty str>}
#   (b) populated:        a map of canonical keys (closed set) for that role
# A scalar `null` is REJECTED — it cannot carry the required reason (per the
# ADR-004 2026-06-05 amendment). Unknown keys are REJECTED (closed key set);
# this is what catches a Playwright spec path mis-filed under devops (ADR-004
# finding C1). Design decision: a populated section is not required to carry
# *every* canonical key (future invariants may legitimately fill a subset), but
# every key it does carry must be canonical and correctly typed, and the
# section must be non-empty — declare `applicable: false` to opt out cleanly.
# Bundles into the schema v2.0.0 migration (OCR-49 / OCR-76); drafted here as
# the ADR-004 acceptance proof.
ROLE_SECTIONS = ['pm', 'devops', 'sre', 'frontend', 'playwright', 'postman']
ROLE_SHAPES = {
    'pm':       {'acceptance_criteria': list, 'user_impact': str,
                 'sprint_decomposition': str},
    'devops':   {'ci_gates': list, 'secrets': list, 'deploy_gates': list,
                 'rollback': str},
    'sre':      {'observability': list, 'slo': 'str_or_null', 'runbook': str,
                 'on_call_action': str},
    'frontend': {'governed_surfaces': 'list_or_str', 'component_constraints': list,
                 'design_system_dependencies': list, 'browser_matrix': str},
    'playwright': {'spec_files': 'spec_files', 'fixtures': str,
                   'viewport_matrix': str},
    'postman':  {'collections': list, 'endpoints': list, 'env_vars': list,
                 'adversarial_cases': list},
}

def _role_type_ok(val, spec):
    if spec is str:
        return isinstance(val, str) and len(val.strip()) > 0
    if spec is list:
        return isinstance(val, list)
    if spec == 'str_or_null':
        return val is None or isinstance(val, str)
    if spec == 'list_or_str':
        return isinstance(val, list) or (isinstance(val, str) and len(val.strip()) > 0)
    if spec == 'spec_files':
        return (isinstance(val, list) and len(val) > 0
                and all(isinstance(s, dict) and 'path' in s and 'asserts' in s
                        for s in val))
    return False

for i in inv.get('invariants', []):
    iid = i.get('id', '?')
    for role in ROLE_SECTIONS:
        if role not in i:
            continue  # optional; absence = "not yet authored"
        section = i[role]

        # A role section must be a map. Scalar null / str / list is rejected:
        # the not-applicable form must carry a reason, which only a map can hold.
        if not isinstance(section, dict):
            check(f'invariant_role_is_map:#{iid}.{role}', False,
                  f'expected map (applicable:false+reason, or populated shape), '
                  f'got {type(section).__name__}: {section!r}')
            continue

        # Not-applicable form: {applicable: false, reason: <non-empty str>}.
        if section.get('applicable') is False:
            reason = section.get('reason')
            reason_ok = isinstance(reason, str) and len(reason.strip()) > 0
            check(f'invariant_role_na_reason:#{iid}.{role}', reason_ok,
                  'applicable:false requires a non-empty reason' if not reason_ok
                  else 'not applicable + reason')
            extra = [k for k in section if k not in ('applicable', 'reason')]
            check(f'invariant_role_na_closed:#{iid}.{role}', not extra,
                  f'applicable:false form permits only applicable+reason; extra {extra}'
                  if extra else 'closed')
            continue

        # Populated form. An explicit `applicable: true` is permitted but optional.
        shape = ROLE_SHAPES[role]
        content_keys = [k for k in section if not (k == 'applicable' and section[k] is True)]
        unknown = [k for k in content_keys if k not in shape]
        check(f'invariant_role_closed:#{iid}.{role}', not unknown,
              f'unknown key(s) {unknown} not in {role} schema {sorted(shape)}'
              if unknown else f'{len(content_keys)} key(s), all canonical')
        check(f'invariant_role_nonempty:#{iid}.{role}', len(content_keys) > 0,
              'populated role section is empty — use applicable:false to opt out'
              if len(content_keys) == 0 else 'ok')
        for key, type_spec in shape.items():
            if key in section:
                ok = _role_type_ok(section[key], type_spec)
                tname = type_spec if isinstance(type_spec, str) else type_spec.__name__
                check(f'invariant_role_type:#{iid}.{role}.{key}', ok,
                      f'{key}: failed type check ({tname})' if not ok else 'ok')

# ---------------------------------------------------------------------------
# 1.5f — invariant_groups block validation (schema 1.2.0, added 2026-07-26)
# ---------------------------------------------------------------------------
# Top-level invariant_groups defines the six order-of-operations groups.
# Required per entry: id (str), title (str), order (positive int),
# description (non-empty str). Group IDs and order values must both be unique.
# valid_group_ids is built here and consumed by 1.5g below.
GROUP_REQUIRED = ['id', 'title', 'order', 'description']
groups = inv.get('invariant_groups', [])
check('invariant_groups_present',
      isinstance(groups, list) and len(groups) > 0,
      f'{len(groups)} group(s)' if isinstance(groups, list) and len(groups) > 0
      else f'expected non-empty list, got {type(groups).__name__}')

valid_group_ids = set()
if isinstance(groups, list):
    for g in groups:
        gid = g.get('id', '?') if isinstance(g, dict) else '?'
        if not isinstance(g, dict):
            check(f'invariant_group_is_dict:{gid}', False,
                  f'expected dict, got {type(g).__name__}')
            continue
        missing_g = [f for f in GROUP_REQUIRED if f not in g]
        check(f'invariant_group_required:{gid}', not missing_g,
              f'missing {missing_g}' if missing_g else 'complete')
        gorder = g.get('order')
        check(f'invariant_group_order_type:{gid}',
              isinstance(gorder, int) and gorder > 0,
              f'order = {gorder!r} (expected positive int)'
              if not (isinstance(gorder, int) and gorder > 0) else f'{gorder}')
        gdesc = g.get('description')
        check(f'invariant_group_description_type:{gid}',
              isinstance(gdesc, str) and len(gdesc.strip()) > 10,
              'expected non-empty str (>10 chars)'
              if not (isinstance(gdesc, str) and len(gdesc.strip()) > 10) else 'ok')
        valid_group_ids.add(gid)

    gids_all = [g.get('id') for g in groups if isinstance(g, dict)]
    check('invariant_group_ids_unique',
          len(gids_all) == len(set(gids_all)),
          f'duplicate group IDs: {[x for x in gids_all if gids_all.count(x) > 1]}'
          if len(gids_all) != len(set(gids_all)) else f'{len(gids_all)} unique')

    gorders_all = [g.get('order') for g in groups
                   if isinstance(g, dict) and isinstance(g.get('order'), int)]
    check('invariant_group_orders_unique',
          len(gorders_all) == len(set(gorders_all)),
          f'duplicate group orders: {[x for x in gorders_all if gorders_all.count(x) > 1]}'
          if len(gorders_all) != len(set(gorders_all)) else f'{len(gorders_all)} unique')

# ---------------------------------------------------------------------------
# 1.5g — per-invariant group fields validation (schema 1.2.0, added 2026-07-26)
# ---------------------------------------------------------------------------
# Every invariant must carry: label (str, "#N — Title"), group (str referencing
# a known invariant_groups id), group_order (positive int unique within group).
# label number must match the invariant's own id. group_order values must not
# collide within the same group (two invariants in the same group cannot share
# a position).
LABEL_PATTERN = re.compile(r'^#\d+ — .+$')  # em dash U+2014
group_order_seen: dict = {}  # group_id -> set of group_order values used

for i in inv.get('invariants', []):
    iid = i.get('id', '?')

    # label format: "#N — Title"
    label = i.get('label')
    label_ok = isinstance(label, str) and bool(LABEL_PATTERN.match(label))
    check(f'invariant_label_format:#{iid}', label_ok,
          f'label = {label!r} (expected "#N — Title" format)'
          if not label_ok else label)

    # label number must match invariant id
    if label_ok and isinstance(iid, int):
        label_num_str = label[1:].split('—')[0].strip()
        try:
            label_num = int(label_num_str)
            check(f'invariant_label_id_match:#{iid}', label_num == iid,
                  f'label #{label_num} does not match invariant id {iid}'
                  if label_num != iid else f'#{iid} matches')
        except ValueError:
            check(f'invariant_label_id_match:#{iid}', False,
                  f'label number {label_num_str!r} is not an integer')

    # group must reference a known group ID
    group = i.get('group')
    check(f'invariant_group_ref:#{iid}',
          group in valid_group_ids,
          f'group = {group!r} not in known groups {sorted(valid_group_ids)}'
          if group not in valid_group_ids else group)

    # group_order must be a positive int, unique within its group
    group_order = i.get('group_order')
    check(f'invariant_group_order_type:#{iid}',
          isinstance(group_order, int) and group_order > 0,
          f'group_order = {group_order!r} (expected positive int)'
          if not (isinstance(group_order, int) and group_order > 0) else f'{group_order}')
    if isinstance(group, str) and isinstance(group_order, int) and group_order > 0:
        if group not in group_order_seen:
            group_order_seen[group] = set()
        dup = group_order in group_order_seen[group]
        check(f'invariant_group_order_unique:#{iid}', not dup,
              f'group_order {group_order} already used in group "{group}"'
              if dup else f'group_order {group_order} in "{group}"')
        group_order_seen[group].add(group_order)

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
        # requires_alt_print boolean (OSE-324, added 2026-05-18) — carve-out
        # marker for codes that legitimately can't pass WCAG-on-white (e.g.,
        # ALERT yellow). Optional; when present must be boolean true (presence
        # is the signal; false is meaningless and would only add noise).
        if 'requires_alt_print' in code:
            rap = code['requires_alt_print']
            check(f'uec_code_requires_alt_print_type:{cid}',
                  isinstance(rap, bool) and rap is True,
                  f'must be boolean true (presence is the signal); got {type(rap).__name__}: {rap!r}'
                  if not (isinstance(rap, bool) and rap is True) else 'ok (true)')

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
# 1.11 — Sponsor allocation canonical (added 2026-05-18 / OSE-330 Phase 1)
# ---------------------------------------------------------------------------
# Validates sponsor-allocation.yaml — codifies the Local Sponsor Covenant
# (architectural-invariants.yaml Invariant #5) display-priority rule + future
# slot-cap floor scaffolding. Structural validation only here; mechanical
# enforcement happens in OSE substrate (OSE-330 Phase 2 — sponsor-resolver
# tierSort upgrade + tier-equity.invariant.spec.ts).
SPONSOR_ALLOC_FILE = 'sponsor-allocation.yaml'
if (BRAIN / SPONSOR_ALLOC_FILE).exists():
    sa = load(SPONSOR_ALLOC_FILE)

    # 1.11.1 — Required top-level keys
    SA_TOP_KEYS = ['schema_version', 'version', 'description', 'covenant',
                   'classification', 'display_priority', 'slot_floor',
                   'drift_detection']
    missing_sa = [k for k in SA_TOP_KEYS if k not in sa]
    check('sponsor_alloc_top_keys', not missing_sa,
          f'missing {missing_sa}' if missing_sa else f'all {len(SA_TOP_KEYS)} present')

    # 1.11.2 — covenant required subfields
    covenant = sa.get('covenant') or {}
    COV_REQUIRED = ['statement', 'brand_promise', 'applies_to']
    missing_cov = [f for f in COV_REQUIRED if f not in covenant]
    check('sponsor_alloc_covenant_required', not missing_cov,
          f'missing {missing_cov}' if missing_cov else 'complete')
    check('sponsor_alloc_covenant_applies_to_nonempty',
          isinstance(covenant.get('applies_to'), list) and len(covenant['applies_to']) > 0,
          f'{len(covenant.get("applies_to", []))} substrates')

    # 1.11.3 — classification required subfields (the is_local boolean contract)
    classification = sa.get('classification') or {}
    CLS_REQUIRED = ['field', 'type', 'default', 'description', 'semantics']
    missing_cls = [f for f in CLS_REQUIRED if f not in classification]
    check('sponsor_alloc_classification_required', not missing_cls,
          f'missing {missing_cls}' if missing_cls else 'complete')
    check('sponsor_alloc_classification_field',
          classification.get('field') == 'is_local',
          f'field = {classification.get("field")!r} (expected "is_local")')
    check('sponsor_alloc_classification_type',
          classification.get('type') == 'boolean',
          f'type = {classification.get("type")!r} (expected "boolean")')

    # 1.11.4 — display_priority rule enum
    display_priority = sa.get('display_priority') or {}
    DP_REQUIRED = ['rule', 'description', 'enforcement']
    missing_dp = [f for f in DP_REQUIRED if f not in display_priority]
    check('sponsor_alloc_display_priority_required', not missing_dp,
          f'missing {missing_dp}' if missing_dp else 'complete')
    DP_RULE_ENUM = ['locals_first']
    check('sponsor_alloc_display_priority_rule_enum',
          display_priority.get('rule') in DP_RULE_ENUM,
          f'rule = {display_priority.get("rule")!r} (expected one of {DP_RULE_ENUM})')

    # 1.11.5 — slot_floor surfaces (future-proofing scaffolding)
    slot_floor = sa.get('slot_floor') or {}
    SF_REQUIRED = ['status', 'description', 'surfaces']
    missing_sf = [f for f in SF_REQUIRED if f not in slot_floor]
    check('sponsor_alloc_slot_floor_required', not missing_sf,
          f'missing {missing_sf}' if missing_sf else 'complete')
    SF_STATUS_ENUM = ['scaffolded', 'active']
    check('sponsor_alloc_slot_floor_status_enum',
          slot_floor.get('status') in SF_STATUS_ENUM,
          f'status = {slot_floor.get("status")!r} (expected one of {SF_STATUS_ENUM})')
    # Each surface entry must have cap (null or int) + local_floor (int) + rationale
    surfaces = slot_floor.get('surfaces') or {}
    for surface_name, surface_def in surfaces.items():
        if not isinstance(surface_def, dict):
            check(f'sponsor_alloc_surface_is_dict:{surface_name}', False,
                  f'expected dict, got {type(surface_def).__name__}')
            continue
        cap = surface_def.get('cap')
        check(f'sponsor_alloc_surface_cap_type:{surface_name}',
              cap is None or isinstance(cap, int),
              f'cap = {cap!r} (expected null or int)')
        floor = surface_def.get('local_floor')
        check(f'sponsor_alloc_surface_local_floor_type:{surface_name}',
              isinstance(floor, int) and floor >= 0,
              f'local_floor = {floor!r} (expected non-negative int)')
        check(f'sponsor_alloc_surface_has_rationale:{surface_name}',
              isinstance(surface_def.get('rationale'), str) and len(surface_def['rationale']) > 10,
              'rationale missing or too short')

    # 1.11.6 — drift_detection status
    drift = sa.get('drift_detection') or {}
    DRIFT_STATUS_ENUM = ['planned', 'active']
    check('sponsor_alloc_drift_detection_status',
          drift.get('status') in DRIFT_STATUS_ENUM,
          f'status = {drift.get("status")!r} (expected one of {DRIFT_STATUS_ENUM})')

    # 1.11.7 — Invariant #5 references this artifact (cross-reference integrity)
    inv5 = next((i for i in inv.get('invariants', []) if i.get('id') == 5), None)
    if inv5 is not None:
        depends = inv5.get('depends_on') or []
        check('sponsor_alloc_invariant5_depends_on',
              SPONSOR_ALLOC_FILE in depends,
              f'Invariant #5 depends_on = {depends} (must include {SPONSOR_ALLOC_FILE})')
        refs = inv5.get('references') or {}
        check('sponsor_alloc_invariant5_brain_canonical',
              refs.get('brain_canonical', '').endswith(SPONSOR_ALLOC_FILE),
              f'Invariant #5 references.brain_canonical = {refs.get("brain_canonical")!r} (must end with {SPONSOR_ALLOC_FILE})')
else:
    # Soft-pass when artifact not present (future-tolerant; will become hard when
    # OSE-330 Phase 2 makes the artifact load-bearing for the OSE-side resolver)
    check('sponsor_alloc_file_present', True,
          f'{SPONSOR_ALLOC_FILE} not yet present (soft-pass; becomes hard once OSE-330 Phase 2 ships)')

# ---------------------------------------------------------------------------
# 1.9 — Invariant #13 CI lock: brain-location-audit.yml structural gate
# Asserts the workflow that enforces invariant #13 has the correct trigger
# paths and invokes the audit script — so the enforcement mechanism is
# code-shape-locked just like invariants #10, #11, #12.
# ---------------------------------------------------------------------------
AUDIT_WORKFLOW = BRAIN.parent / '.github' / 'workflows' / 'brain-location-audit.yml'

check(
    'inv13_audit_workflow_exists',
    AUDIT_WORKFLOW.exists(),
    f'brain-location-audit.yml must exist at {AUDIT_WORKFLOW}'
)

if AUDIT_WORKFLOW.exists():
    _wf_text = AUDIT_WORKFLOW.read_text(encoding='utf-8')

    check(
        'inv13_audit_workflow_schedule_trigger',
        'schedule:' in _wf_text and 'cron:' in _wf_text,
        'brain-location-audit.yml must have a nightly schedule trigger (cron:)'
    )

    check(
        'inv13_audit_workflow_pr_path_trigger',
        'ocr-docs-brain/' in _wf_text and 'pull_request:' in _wf_text,
        'brain-location-audit.yml must trigger on pull_request with ocr-docs-brain/ path filter'
    )

    check(
        'inv13_audit_workflow_invokes_script',
        'audit_brain_enforcement_location.py' in _wf_text,
        'brain-location-audit.yml must invoke audit_brain_enforcement_location.py'
    )

    check(
        'inv13_audit_script_exists',
        (BRAIN / 'scripts' / 'audit_brain_enforcement_location.py').exists(),
        'ocr-docs-brain/scripts/audit_brain_enforcement_location.py must exist'
    )

# ---------------------------------------------------------------------------
# 1.10 — Invariant #20: Standards Propagation Completeness
# Asserts every live invariant ID appears in docs/standards/standards-index.md.
# This check is the structural gate that advances #20 from planned → partial.
# Soft-pass for any live invariant IDs missing from the index — so the initial
# scaffolding doesn't block CI while the index is being filled in; becomes a
# hard gate once standards-index.md has been validated as complete.
# ---------------------------------------------------------------------------
STANDARDS_INDEX = BRAIN.parent / 'docs' / 'standards' / 'standards-index.md'

check(
    'inv20_standards_index_exists',
    STANDARDS_INDEX.exists(),
    f'docs/standards/standards-index.md must exist — it is the propagation target for invariant #20'
)

if STANDARDS_INDEX.exists():
    _idx_text = STANDARDS_INDEX.read_text(encoding='utf-8')
    _live_ids = [
        i.get('id') for i in inv.get('invariants', [])
        if isinstance(i, dict) and i.get('status') == 'live' and isinstance(i.get('id'), int)
    ]
    _missing_from_index = [iid for iid in _live_ids if f'| {iid} |' not in _idx_text]
    check(
        'inv20_all_live_invariants_in_index',
        len(_missing_from_index) == 0,
        f'live invariant IDs missing from standards-index.md: {_missing_from_index}'
        if _missing_from_index else f'{len(_live_ids)} live invariant(s) all present'
    )

# ---------------------------------------------------------------------------
# 1.12 — Invariant #22 enforcement_mode plane (OSE-1288 / F13, added 2026-09-10)
# scripts/cross_repo_patterns.json is #22's live-read SoT. Validate:
#   - enforcement_mode (fleet default) ∈ {block, warn}
#   - enforcement_mode_overrides (optional) is a dict; each value ∈ {block, warn}
#     and each key is a subset of #22's applies_to (an override for a product #22
#     does not protect is a silent no-op and almost certainly a typo).
# ---------------------------------------------------------------------------
CRP_FILE = BRAIN / 'scripts' / 'cross_repo_patterns.json'
if CRP_FILE.exists():
    crp = json.loads(CRP_FILE.read_text(encoding='utf-8'))
    MODE_ENUM = ['block', 'warn']
    mode = crp.get('enforcement_mode')
    check('cross_repo_enforcement_mode_enum', mode in MODE_ENUM,
          f'enforcement_mode = {mode!r} (expected one of {MODE_ENUM})')
    ov = crp.get('enforcement_mode_overrides', {})
    check('cross_repo_overrides_is_dict', isinstance(ov, dict),
          f'expected dict, got {type(ov).__name__}' if not isinstance(ov, dict)
          else f'{len(ov)} override(s)')
    if isinstance(ov, dict):
        for k, v in ov.items():
            check(f'cross_repo_override_mode_enum:{k}', v in MODE_ENUM,
                  f'{v!r} not in {MODE_ENUM}' if v not in MODE_ENUM else f'{v}')
            check(f'cross_repo_override_in_applies22:{k}', k in _applies22,
                  f'{k!r} not in #22 applies_to {_applies22} (override would be a no-op)'
                  if k not in _applies22 else 'in applies_to')
else:
    check('cross_repo_patterns_present', True,
          'cross_repo_patterns.json not present (soft-pass; brain_script guard not armed)')

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
