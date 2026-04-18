#!/usr/bin/env python3
"""
Level 2 — UNIT
===============
Value-level assertions. Counts match. Uniqueness holds.
Computed properties are correct. Each check tests one rule against one file.
"""
import re, sys, yaml
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

products = pr.get('products', [])
categories = et.get('categories', [])
invariants = inv.get('invariants', [])

# ---------------------------------------------------------------------------
# 2.1 — Taxonomy count matches declared total
# ---------------------------------------------------------------------------
declared = et.get('total_types_v1', 0)
actual = sum(len(c.get('event_types', [])) for c in categories)
check('taxonomy_count_match', declared == actual,
      f'declared={declared} actual={actual} drift={declared-actual}' if declared != actual
      else f'{actual} types, matches')

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
check('invariant_ids_sequential', inv_ids == expected_seq,
      f'expected {expected_seq[:5]}... got {inv_ids[:5]}...' if inv_ids != expected_seq else 'sequential')

# ---------------------------------------------------------------------------
# 2.8 — Invariant status summary matches actual counts
# ---------------------------------------------------------------------------
summary = inv.get('status_summary', {})
actual_live = sum(1 for i in invariants if i.get('status') == 'live')
actual_partial = sum(1 for i in invariants if i.get('status') == 'partial')
actual_planned = sum(1 for i in invariants if i.get('status') == 'planned')
check('invariant_summary_live', summary.get('live') == actual_live,
      f'declared={summary.get("live")} actual={actual_live}')
check('invariant_summary_partial', summary.get('partial') == actual_partial,
      f'declared={summary.get("partial")} actual={actual_partial}')
check('invariant_summary_planned', summary.get('planned') == actual_planned,
      f'declared={summary.get("planned")} actual={actual_planned}')
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
