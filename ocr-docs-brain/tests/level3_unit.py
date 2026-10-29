#!/usr/bin/env python3
"""
Level 3 — UNIT
===============
Value-level assertions. Counts match. Uniqueness holds.
Computed properties are correct. Each check tests one rule against one file.

Includes (added 2026-05-18 / OSE-324):
  - WCAG contrast computation for UEC scan_hex values. Promotes the
    dual-palette schema's `wcag_grade` enum from a DECLARED claim
    (level2_schema.py constrains the field to AA/AAA — FAIL
    unrepresentable) to a COMPUTED guarantee — actually computes the
    contrast ratio of every scan_hex against white (#FFFFFF) and asserts
    the computed grade meets or exceeds the declared wcag_grade.
    This is what makes the brand promise ("the color IS the instruction")
    mechanically enforceable: a future contributor (or agent) who edits
    a scan_hex to something visually nice but contrast-insufficient
    fails CI on this check, not at a customer's first failed scan.
  - Inline fixture tests proving the WCAG computation fires on
    deliberately-bad inputs (#FFFFFF as scan_hex with AAA declared
    grade, etc.) — negative-test discipline so the gate's behavior is
    proven, not just the artifact's pass-through.
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

products = pr.get('products', [])
categories = et.get('categories', [])
invariants = inv.get('invariants', [])

# ---------------------------------------------------------------------------
# 2.1 — Taxonomy count matches declared total
# ---------------------------------------------------------------------------
all_types = [t for c in categories for t in c.get('event_types', [])]
phase1_types = [t for t in all_types if t.get('phase', 1) == 1]
declared_v1 = et.get('total_types_v1', 0)
declared_all = et.get('total_types', 0)
count_ok = declared_v1 == len(phase1_types) and declared_all == len(all_types)
check('taxonomy_count_match', count_ok,
      f'total_types_v1 declared={declared_v1} actual={len(phase1_types)}; '
      f'total_types declared={declared_all} actual={len(all_types)}' if not count_ok
      else f'{len(phase1_types)} phase 1 types and {len(all_types)} in all, matches')

# ---------------------------------------------------------------------------
# 2.1a — Founding nodes (owner, 2026-10-29): six nodes first, then Harbor Country
#        (Southwest Michigan) as the network destination.
# ---------------------------------------------------------------------------
FOUNDING_SIX = ['blue_island', 'beverly', 'gresham_ashburn', 'evergreen_park', 'oak_lawn', 'mt_greenwood']
corridors_all = cd.get('founding_corridors', [])
six_found = [c.get('corridor_id') for c in corridors_all if c.get('node_set') == 'founding_six']
check('founding_six_nodes_exact', sorted(six_found) == sorted(FOUNDING_SIX),
      f'expected {sorted(FOUNDING_SIX)}, found {sorted(six_found)}' if sorted(six_found) != sorted(FOUNDING_SIX)
      else 'blue_island, beverly, gresham_ashburn, evergreen_park, oak_lawn, mt_greenwood')

bad_set = [c.get('corridor_id') for c in corridors_all if c.get('node_set') not in ('founding_six', 'network_destination')]
check('every_corridor_has_a_node_set', not bad_set,
      f'node_set must be founding_six or network_destination: {bad_set}' if bad_set
      else 'every corridor is a founding node or the network destination')

harbor = next((c for c in corridors_all if c.get('corridor_id') == 'harbor_country'), {})
check('harbor_country_is_network_destination', harbor.get('node_set') == 'network_destination',
      f'node_set={harbor.get("node_set")!r}' if harbor.get('node_set') != 'network_destination'
      else 'harbor_country follows the six as the network destination')

net_dest = sorted(c.get('corridor_id') for c in corridors_all if c.get('node_set') == 'network_destination')
check('only_harbor_country_is_network_destination', net_dest == ['harbor_country'],
      f'expected only harbor_country, found {net_dest}' if net_dest != ['harbor_country']
      else 'harbor_country is the only network destination')

# A founding node's description is the owner's to write. A placeholder must not ship as if it were one.
undescribed = [c.get('corridor_id') for c in corridors_all
               if c.get('node_set') == 'founding_six'
               and 'to be written by the owner' in str(c.get('role_description', '')).lower()]
check('founding_nodes_have_descriptions', not undescribed,
      f'still the placeholder: {undescribed}' if undescribed
      else 'every founding node has a description written from the owner\'s own words')

# ---------------------------------------------------------------------------
# 2.1b — Phase 2 types (owner decision: add parade and holy_day_gathering;
#        the heritage label is chosen by the organizer and is never part of a type)
# ---------------------------------------------------------------------------
PHASE2_EXPECTED = {
    'parade': ('SS-006', 'seasonal_special'),
    'holy_day_gathering': ('CR-008', 'community_ritual'),
    'recreational_league': ('GR-007', 'games_recreation'),
}
phase2_found = {}
for cat in categories:
    for t in cat.get('event_types', []):
        if t.get('phase', 1) == 2:
            phase2_found[t.get('type_id')] = (t.get('uec_code'), cat.get('category_id'))
check('phase2_types_registered', phase2_found == PHASE2_EXPECTED,
      f'expected {PHASE2_EXPECTED}, found {phase2_found}' if phase2_found != PHASE2_EXPECTED
      else f'{len(PHASE2_EXPECTED)} phase 2 types registered with the expected codes and categories')

bad_phase = [t.get('type_id') for t in all_types if t.get('phase', 1) not in (1, 2)]
check('phase_values_valid', not bad_phase,
      f'phase must be 1 or 2: {bad_phase}' if bad_phase else 'every phase is 1 or 2')

check('phase1_seed_is_47', len(phase1_types) == 47,
      f'the Phase 1 seed is fixed at 47, found {len(phase1_types)}' if len(phase1_types) != 47
      else '47 phase 1 types, the seed OSE migration 0024 shares')

holy = next((t for t in all_types if t.get('type_id') == 'holy_day_gathering'), {})
holy_adds = holy.get('scan_codes_add', []) or []
holy_removes = holy.get('scan_codes_remove', []) or []
check('holy_day_gathering_no_commerce_codes',
      bool(holy) and 'SPONSOR' in holy_removes and not {'SPONSOR', 'SHOP'} & set(holy_adds),
      f'add={holy_adds} remove={holy_removes}' if not (holy and 'SPONSOR' in holy_removes and not {'SPONSOR', 'SHOP'} & set(holy_adds))
      else 'SPONSOR removed, no SPONSOR or SHOP added')

# A type describes the form of the event. An ethnic, national, language or faith label
# belongs to the organizer's choice on the event, never to a type id or name.
LABEL_WORDS = {
    # ethnic, national and regional labels
    'palestinian', 'arab', 'arabic', 'hispanic', 'latino', 'latina', 'latinx', 'latin', 'mexican',
    'puerto', 'rican', 'cuban', 'jamaican', 'caribbean', 'asian', 'african', 'chinese', 'korean',
    'vietnamese', 'filipino', 'japanese', 'indian', 'persian', 'turkish', 'greek', 'armenian',
    'polish', 'irish', 'italian', 'ukrainian', 'nigerian', 'ethiopian', 'somali', 'hmong',
    'navajo', 'native', 'pacific',
    # language labels
    'spanish', 'french', 'russian', 'haitian', 'portuguese', 'amharic', 'tigrinya', 'yoruba',
    'igbo', 'swahili', 'thai', 'tagalog', 'hindi', 'urdu', 'mandarin', 'cantonese', 'hausa', 'wolof',
    # faith and observance labels
    'muslim', 'islamic', 'christian', 'catholic', 'jewish', 'hindu', 'sikh', 'buddhist',
    'diwali', 'eid', 'ramadan', 'hanukkah', 'lunar',
}


def _label_words(text):
    # Whole words, plus the singular of a plural, so "Hispanics" is caught as "hispanic".
    out = set()
    for w in re.findall(r'[a-z]+', text.lower()):
        out.add(w)
        if w.endswith('s'):
            out.add(w[:-1])
    return out


labelled = []
for t in all_types:
    text = f'{t.get("type_id", "")} {t.get("type_name", "")} {t.get("description", "")}'
    hit = _label_words(text) & LABEL_WORDS
    if hit:
        labelled.append(f'{t.get("type_id")}: {sorted(hit)}')
check('type_names_carry_no_community_label', not labelled,
      f'move the label to the organizer field: {labelled}' if labelled
      else 'no type id, name or description carries an ethnic, national, language or faith label')

# ---------------------------------------------------------------------------
# 2.1c — Activities (sports). A league-style type names one sport from a closed list,
#        so every sport is represented without a type per sport.
# ---------------------------------------------------------------------------
activities = et.get('activities', []) or []
act_ids = [a.get('activity_id') for a in activities]
act_codes = [a.get('activity_code') for a in activities]
act_names = [str(a.get('activity_name', '')).strip().lower() for a in activities]
ACT_PATTERN = re.compile(r'^AC-\d{3}$')
act_problems = []
if not activities:
    act_problems.append('no activities defined')
if any(not a.get('activity_id') or not a.get('activity_name') for a in activities):
    act_problems.append('an activity is missing its id or name')
if len(set(act_ids)) != len(act_ids):
    act_problems.append('duplicate activity_id')
if len(set(act_codes)) != len(act_codes):
    act_problems.append('duplicate activity_code')
if len(set(act_names)) != len(act_names):
    act_problems.append('duplicate activity_name')
if any(not (c and ACT_PATTERN.match(c)) for c in act_codes):
    act_problems.append('activity_code must look like AC-001')
check('activities_registry_valid', not act_problems,
      '; '.join(act_problems) if act_problems else f'{len(activities)} activities, ids, codes and names unique')

declared_acts = et.get('total_activities', 0)
count_acts_ok = bool(activities) and declared_acts == len(activities)
check('activities_count_match', count_acts_ok,
      f'total_activities declared={declared_acts} actual={len(activities)}' if not count_acts_ok
      else f'{len(activities)} activities, matches')

# The floor of "all sports": these must always be present. More may be added; none removed.
MUST_HAVE_ACTIVITIES = {
    # core and Olympic
    'soccer', 'futsal', 'beach_soccer', 'futevolei', 'volleyball', 'beach_volleyball',
    'basketball', 'baseball', 'softball', 'cricket', 'rugby', 'tennis', 'swimming', 'athletics',
    'flag_football', 'lacrosse', 'squash',
    # fast-growing and newer competitive sports
    'pickleball', 'padel', 'roundnet', 'beach_tennis', 'esports', 'breaking',
    'obstacle_course_racing', 'functional_fitness', 'wingfoiling',
    # adaptive and Paralympic sports with their own rules
    'wheelchair_basketball', 'wheelchair_rugby', 'goalball', 'boccia', 'sitting_volleyball',
}
missing_acts = sorted(MUST_HAVE_ACTIVITIES - set(act_ids))
check('activities_cover_required_sports', not missing_acts,
      f'missing: {missing_acts}' if missing_acts else f'all {len(MUST_HAVE_ACTIVITIES)} required sports present')

labelled_acts = [a.get('activity_id') for a in activities
                 if _label_words(f'{a.get("activity_id", "")} {a.get("activity_name", "")}') & LABEL_WORDS]
check('activities_carry_no_community_label', not labelled_acts,
      f'move the label to the organizer field: {labelled_acts}' if labelled_acts
      else 'no activity id or name carries an ethnic, national, language or faith label')

league = next((t for t in all_types if t.get('type_id') == 'recreational_league'), {})
check('recreational_league_takes_activity', league.get('takes_activity') is True,
      f'takes_activity={league.get("takes_activity")!r}' if league.get('takes_activity') is not True
      else 'recreational_league names one activity from the closed list')

# A sport is listed by its generic name, never by a company's trademark.
BRAND_WORDS = {
    'frisbee', 'spikeball', 'crossfit', 'hyrox', 'spartan', 'mudder', 'zumba', 'nerf',
    'wiffle', 'rollerblade', 'rollerblading',
}
branded_acts = [a.get('activity_id') for a in activities
                if _label_words(f'{a.get("activity_id", "")} {a.get("activity_name", "")}') & BRAND_WORDS]
check('activities_carry_no_brand_name', not branded_acts,
      f'use the generic name: {branded_acts}' if branded_acts
      else 'no activity id or name is a trademark')

# Codes are issued in order and never reused, so the list must read AC-001 up to AC-N.
expected_codes = [f'AC-{i:03d}' for i in range(1, len(activities) + 1)]
check('activities_codes_contiguous', bool(activities) and act_codes == expected_codes,
      'activity codes are not AC-001 up to AC-N in order' if act_codes != expected_codes
      else f'AC-001 to AC-{len(activities):03d}, in order')

# A sport that already has its own type (bocce, bowling) keeps it and is not repeated here.
type_id_tokens = set()
for t in all_types:
    type_id_tokens |= set(re.findall(r'[a-z]+', str(t.get('type_id', ''))))
repeated = [i for i in act_ids if i in type_id_tokens]
check('activities_do_not_repeat_typed_sports', not repeated,
      f'already has its own type: {repeated}' if repeated
      else 'no activity repeats a sport that has its own type')

# ---------------------------------------------------------------------------
# 2.2 — UEC codes are globally unique
# ---------------------------------------------------------------------------
all_codes = []
for cat in categories:
    for t in cat.get('event_types', []):
        all_codes.append(t.get('uec_code'))
dupes = [c for c in set(all_codes) if all_codes.count(c) > 1]
check('uec_codes_unique', not dupes,
      f'duplicates: {dupes}' if dupes else f'{len(all_codes)} codes, all unique')

# ---------------------------------------------------------------------------
# 2.3 — UEC codes follow the prefix-NNN pattern
# ---------------------------------------------------------------------------
UEC_PATTERN = re.compile(r'^[A-Z]{2}-\d{3}$')
bad_format = [c for c in all_codes if c and not UEC_PATTERN.match(c)]
check('uec_code_format', not bad_format,
      f'bad format: {bad_format[:5]}' if bad_format else 'all match XX-NNN')

# ---------------------------------------------------------------------------
# 2.4 — UEC prefix matches category
# ---------------------------------------------------------------------------
EXPECTED_PREFIX = {
    'community_ritual': 'CR', 'music_culture': 'MC', 'games_recreation': 'GR',
    'food_drink': 'FD', 'wellness_health': 'WH', 'youth_education': 'YE',
    'civic_commerce': 'CC', 'seasonal_special': 'SS',
}
wrong_prefix = []
for cat in categories:
    expected = EXPECTED_PREFIX.get(cat.get('category_id'))
    if not expected:
        continue
    for t in cat.get('event_types', []):
        code = t.get('uec_code', '')
        if not code.startswith(expected):
            wrong_prefix.append(f'{t.get("type_id")}={code} (expected {expected})')
check('uec_prefix_matches_category', not wrong_prefix,
      f'{wrong_prefix[:3]}' if wrong_prefix else 'all prefixes match')

# ---------------------------------------------------------------------------
# 2.5 — Every category has at least one event type
# ---------------------------------------------------------------------------
empty_cats = [c.get('category_id') for c in categories if not c.get('event_types')]
check('categories_nonempty', not empty_cats,
      f'empty: {empty_cats}' if empty_cats else f'all {len(categories)} have types')

# ---------------------------------------------------------------------------
# 2.6 — Product IDs are unique
# ---------------------------------------------------------------------------
pids = [p.get('product_id') for p in products]
dupe_pids = [p for p in set(pids) if pids.count(p) > 1]
check('product_ids_unique', not dupe_pids,
      f'duplicates: {dupe_pids}' if dupe_pids else f'{len(pids)} products, all unique')

# ---------------------------------------------------------------------------
# 2.7 — Invariant IDs are unique and sequential
# ---------------------------------------------------------------------------
inv_ids = [i.get('id') for i in invariants]
dupe_inv = [x for x in set(inv_ids) if inv_ids.count(x) > 1]
check('invariant_ids_unique', not dupe_inv,
      f'duplicates: {dupe_inv}' if dupe_inv else f'{len(inv_ids)} invariants, all unique')

expected_seq = list(range(1, len(inv_ids) + 1))
# Invariants may be ordered by invariant_group (for readability); check complete set, not YAML order
check('invariant_ids_sequential', sorted(inv_ids) == expected_seq,
      f'expected sorted={expected_seq[:5]}... got sorted={sorted(inv_ids)[:5]}...' if sorted(inv_ids) != expected_seq else f'complete sequential set 1–{len(inv_ids)} (group-ordered YAML)')

# ---------------------------------------------------------------------------
# 2.8 — Invariant status summary matches actual counts
# ---------------------------------------------------------------------------
summary = inv.get('status_summary', {})
actual_live = sum(1 for i in invariants if i.get('status') == 'live')
actual_partial = sum(1 for i in invariants if i.get('status') == 'partial')
actual_planned = sum(1 for i in invariants if i.get('status') == 'planned')
actual_retired = sum(1 for i in invariants if i.get('status') == 'retired')
check('invariant_summary_live', summary.get('live') == actual_live,
      f'declared={summary.get("live")} actual={actual_live}')
check('invariant_summary_partial', summary.get('partial') == actual_partial,
      f'declared={summary.get("partial")} actual={actual_partial}')
check('invariant_summary_planned', summary.get('planned') == actual_planned,
      f'declared={summary.get("planned")} actual={actual_planned}')
check('invariant_summary_retired', summary.get('retired', 0) == actual_retired,
      f'declared={summary.get("retired", 0)} actual={actual_retired}')
check('invariant_summary_total', summary.get('total') == len(invariants),
      f'declared={summary.get("total")} actual={len(invariants)}')

# ---------------------------------------------------------------------------
# 2.9 — Tier availability phases cover all 5 phases for operational products
# ---------------------------------------------------------------------------
REQUIRED_PHASES = {'phase1', 'phase2', 'phase3', 'phase4', 'phase5'}
for p in products:
    if p.get('identity_layer') in ('n/a', 'pre-tech'):
        continue
    ta = p.get('tier_availability')
    if not isinstance(ta, dict):
        check(f'tier_phases:{p.get("product_id")}', False, 'tier_availability missing')
        continue
    missing = REQUIRED_PHASES - set(ta.keys())
    check(f'tier_phases:{p.get("product_id")}', not missing,
          f'missing {missing}' if missing else 'all 5 phases')

# ---------------------------------------------------------------------------
# 2.10 — Phase gates are monotonically non-decreasing in tier count
# ---------------------------------------------------------------------------
for p in products:
    if p.get('identity_layer') in ('n/a', 'pre-tech'):
        continue
    ta = p.get('tier_availability', {})
    if not ta:
        continue
    counts = [len(ta.get(f'phase{i}', [])) for i in range(1, 6)]
    monotonic = all(counts[i] <= counts[i+1] for i in range(len(counts)-1))
    check(f'tier_monotonic:{p.get("product_id")}', monotonic,
          f'phase counts {counts}' + (' (non-monotonic!)' if not monotonic else ''))

# ---------------------------------------------------------------------------
# 3.X — UEC WCAG contrast computation (OSE-324 — added 2026-05-18)
# ---------------------------------------------------------------------------
# Computational enforcement of the brand promise: every scan_hex MUST yield
# WCAG contrast against white that meets or exceeds the declared wcag_grade.
# Per WCAG 2.1:
#   AA  = contrast ratio >= 4.5:1 (normal text minimum)
#   AAA = contrast ratio >= 7:1   (enhanced)
# A scan_hex declared as AAA that computes to 6.8:1 fails this check; ships
# would block in CI. Same for AA declared but computing < 4.5.
#
# Reference implementation matches the WCAG formula used in OSE's
# uec-codes.invariant.spec.ts (Playwright). Same math, different runtime.

WCAG_AA_RATIO = 4.5
WCAG_AAA_RATIO = 7.0
GRADE_THRESHOLDS = {'AA': WCAG_AA_RATIO, 'AAA': WCAG_AAA_RATIO}


def _channel_linear(c_srgb: float) -> float:
    """Convert an sRGB channel (0..1) to linear-light. Per WCAG 2.x spec."""
    return c_srgb / 12.92 if c_srgb <= 0.03928 else ((c_srgb + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color: str) -> float:
    """Relative luminance of a #RRGGBB color, per WCAG 2.x."""
    s = hex_color.lstrip('#')
    r = int(s[0:2], 16) / 255.0
    g = int(s[2:4], 16) / 255.0
    b = int(s[4:6], 16) / 255.0
    return 0.2126 * _channel_linear(r) + 0.7152 * _channel_linear(g) + 0.0722 * _channel_linear(b)


def wcag_contrast_ratio(hex_a: str, hex_b: str) -> float:
    """Compute WCAG contrast ratio between two #RRGGBB colors. Range [1, 21]."""
    la = _relative_luminance(hex_a)
    lb = _relative_luminance(hex_b)
    lighter, darker = (la, lb) if la > lb else (lb, la)
    return (lighter + 0.05) / (darker + 0.05)


def wcag_grade_passes(scan_hex: str, declared_grade: str, background: str = '#FFFFFF') -> tuple[bool, float]:
    """Returns (passes, computed_ratio). Threshold from GRADE_THRESHOLDS."""
    ratio = wcag_contrast_ratio(scan_hex, background)
    threshold = GRADE_THRESHOLDS.get(declared_grade)
    if threshold is None:
        # Unknown grade — caller's structural check should have rejected this;
        # treat as fail here so the issue surfaces somewhere.
        return False, ratio
    return ratio >= threshold, ratio


# Run WCAG computation against the live UEC artifact
UEC_FILE = 'uec-codes.yaml'
if (BRAIN / UEC_FILE).exists():
    uec = load(UEC_FILE)
    for code in uec.get('codes', []):
        if not isinstance(code, dict):
            continue
        cid = code.get('id', '?')
        scan_hex = code.get('scan_hex')
        declared = code.get('wcag_grade')
        # Carve-out: codes marked requires_alt_print=true bypass the WCAG-on-white
        # gate because they're designed for alternative-substrate print (e.g.,
        # ALERT yellow on yellow background with dark modules). The schema +
        # the code's rationale.verdict must justify the carve-out. The brain
        # changelog documents it. We surface a PASS with skip-reason so the
        # check is visible in the report (not silently absent).
        if code.get('requires_alt_print') is True:
            check(
                f'uec_wcag_compute:{cid}',
                True,
                f'SKIPPED (requires_alt_print=true): {declared} declaration not validated on white; '
                'standard contrast assumption does not apply per documented carve-out'
            )
            continue
        if not scan_hex or not declared:
            check(f'uec_wcag_compute_setup:{cid}', False,
                  f'missing scan_hex or wcag_grade (scan_hex={scan_hex!r}, grade={declared!r})')
            continue
        passes, ratio = wcag_grade_passes(scan_hex, declared)
        threshold = GRADE_THRESHOLDS.get(declared, 0.0)
        check(
            f'uec_wcag_compute:{cid}',
            passes,
            f'{declared} on white: computed {ratio:.2f}:1, threshold {threshold:.1f}:1 — '
            + ('OK' if passes else f'INSUFFICIENT (need >= {threshold:.1f})')
        )
else:
    check('uec_wcag_compute_setup', False,
          f'{UEC_FILE} not present — cannot run WCAG computation')

# ---------------------------------------------------------------------------
# 3.Y — Negative-test fixtures: prove the WCAG gate fires on bad inputs
# ---------------------------------------------------------------------------
# The structural validation in level2_schema.py is exercised by the live
# brain pyramid run (positive evidence). These fixtures provide negative
# evidence: prove the WCAG computation actually catches deliberately-bad
# scan_hex values. Without this, a regression in the contrast math could
# silently pass the gate; with this, the gate's BEHAVIOR is tested.
#
# Each fixture pairs (scan_hex, declared_grade, expected_pass). If the
# computation returns the wrong verdict, the fixture's check FAILs and
# the gate itself is broken.

WCAG_FIXTURES = [
    # (label, scan_hex, declared_grade, expected_pass, why)
    # Canonical-aligned fixtures (match the post-OSE-324-correction declared grades):
    ('canonical_enter_aa',          '#1A6B2F', 'AA',  True,  'ENTER scan_hex passes AA on white (corrected 2026-05-18 from AAA per OSE-324 — computed 6.59:1, below AAA 7:1)'),
    ('canonical_sponsor_aaa',       '#1A3A8A', 'AAA', True,  'SPONSOR scan_hex passes AAA on white (canonical)'),
    ('canonical_live_aa',           '#C04048', 'AA',  True,  'LIVE scan_hex passes AA on white (canonical)'),
    ('canonical_checkin_aa',        '#006B6B', 'AA',  True,  'CHECK-IN scan_hex passes AA on white (corrected 2026-05-18 from AAA per OSE-324 — computed 6.33:1, below AAA 7:1)'),
    # Negative fixtures — prove the gate fires on bad inputs:
    ('white_on_white_fails_any',    '#FFFFFF', 'AA',  False, 'white scan_hex on white background = 1:1 — must fail any grade'),
    ('near_white_fails_aa',         '#EEEEEE', 'AA',  False, '#EEEEEE on white ~1.32:1 — below AA threshold'),
    ('mid_grey_fails_aaa',          '#777777', 'AAA', False, '#777777 on white ~4.48:1 — below AAA threshold'),
    ('mid_grey_passes_aa',          '#767676', 'AA',  True,  '#767676 on white ~4.54:1 — just above AA threshold (regression guard for boundary)'),
    ('black_passes_aaa',            '#000000', 'AAA', True,  'black on white = 21:1 — sanity check upper bound'),
    # Boundary fixtures around the corrected canonical values — regression guards
    # so future hex tweaks don't silently push a code below the declared grade:
    ('enter_below_aaa_above_aa',    '#1A6B2F', 'AAA', False, 'regression guard — ENTER hex cannot be re-declared AAA without raising contrast first'),
    ('checkin_below_aaa_above_aa',  '#006B6B', 'AAA', False, 'regression guard — CHECK-IN hex cannot be re-declared AAA without raising contrast first'),
    # Alt-print exemption fixture — prove the ALERT yellow case is acknowledged
    # as failing standard WCAG and thus REQUIRES requires_alt_print=true:
    ('alert_yellow_fails_aa_unless_exempt', '#B8960A', 'AA', False, 'ALERT yellow ~2.84:1 on white — would fail AA if validated; documented carve-out via requires_alt_print=true skips the validation'),
]

for label, scan_hex, declared, expected_pass, why in WCAG_FIXTURES:
    actual_pass, ratio = wcag_grade_passes(scan_hex, declared)
    correct = actual_pass == expected_pass
    check(
        f'uec_wcag_fixture:{label}',
        correct,
        f'{declared} on white: computed {ratio:.2f}:1, expected pass={expected_pass}, got pass={actual_pass} ({why})'
    )

# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')
print(f'{"="*76}')
print(f'  LEVEL 3 — UNIT')
print(f'{"="*76}')
for name, status, detail in results:
    m = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {m}  {name:50} {detail}')
print(f'{"-"*76}')
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print(f'{"-"*76}')
sys.exit(0 if failed == 0 else 1)
