#!/usr/bin/env python3
"""
Level 8 — ACADEMIC FOUNDATIONS
================================
Validates that the brain contains the design documents and structural
properties required for multi-disciplinary academic credibility.

These checks do not evaluate whether the methodology is correct —
that is an academic judgment. They verify that the brain CLAIMS are
documented in a form that academics can evaluate.

Target disciplines: economic geography, sociology, political science, education.
"""
import sys, yaml
from pathlib import Path

BRAIN = Path(__file__).parent.parent if (Path(__file__).parent.parent / 'product-registry.yaml').exists() \
    else Path(__file__).parent / 'ocr-docs-brain'

results = []

def check(name, condition, detail=''):
    results.append((name, 'PASS' if condition else 'FAIL', detail))

def load(f):
    path = BRAIN / f
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text())

DISCIPLINES = ['economic_geography', 'sociology', 'political_science', 'education']

# ---------------------------------------------------------------------------
# 8.1 — Construct validity map exists and covers all disciplines
# ---------------------------------------------------------------------------
cvm = load('construct-validity-map.yaml')
check('doc:construct_validity_map_exists', cvm is not None,
      'present' if cvm else 'MISSING — no disciplinary signal mapping')
if cvm:
    target_disc = cvm.get('target_disciplines', [])
    for d in DISCIPLINES:
        check(f'construct_validity:discipline:{d}', d in target_disc,
              'listed' if d in target_disc else 'MISSING')
    # Every signal type has all 4 discipline mappings
    for st_id, st_data in (cvm.get('signal_types') or {}).items():
        constructs = st_data.get('disciplinary_constructs', {})
        for d in DISCIPLINES:
            check(f'construct_validity:signal:{st_id}/{d}',
                  d in constructs and constructs[d].get('construct'),
                  constructs.get(d, {}).get('construct', 'MISSING'))
    check('construct_validity:known_limitations',
          bool(cvm.get('known_limitations')),
          f'{len(cvm.get("known_limitations", []))} limitations documented')

# ---------------------------------------------------------------------------
# 8.2 — Causal identification spec exists and is complete
# ---------------------------------------------------------------------------
cid = load('causal-identification.yaml')
check('doc:causal_identification_exists', cid is not None,
      'present' if cid else 'MISSING — no formal experimental design')
if cid:
    pd = cid.get('primary_design', {})
    check('causal:has_treatment', bool(pd.get('treatment')),
          pd.get('treatment', {}).get('definition', 'MISSING')[:60] if pd.get('treatment') else 'MISSING')
    check('causal:has_control', bool(pd.get('control')),
          'before_period + untreated_corridors' if pd.get('control') else 'MISSING')
    outcomes = pd.get('outcome_variables', {})
    check('causal:has_primary_outcomes',
          bool(outcomes.get('primary')),
          f'{len(outcomes.get("primary", []))} primary outcomes' if outcomes.get('primary') else 'MISSING')
    strategy = pd.get('identification_strategy', {})
    check('causal:has_identification_strategy', bool(strategy.get('primary')),
          strategy.get('primary', 'MISSING'))
    threats = strategy.get('threats_to_validity', [])
    check('causal:has_threats_to_validity', len(threats) >= 3,
          f'{len(threats)} threats documented')
    reqs = cid.get('minimum_requirements', {})
    check('causal:has_minimum_requirements', len(reqs) >= 3,
          f'{len(reqs)} requirements')

# ---------------------------------------------------------------------------
# 8.3 — Census integration plan exists
# ---------------------------------------------------------------------------
cip = load('census-integration-plan.yaml')
check('doc:census_integration_plan_exists', cip is not None,
      'present' if cip else 'MISSING — no demographic context for anonymous data')
if cip:
    tables = cip.get('acs_tables', {})
    demo_tables = tables.get('demographics', [])
    check('census:has_demographic_tables', len(demo_tables) >= 4,
          f'{len(demo_tables)} demographic ACS tables specified')
    check('census:has_representation_protocol',
          bool(cip.get('representation_gap_protocol')),
          'protocol present' if cip.get('representation_gap_protocol') else 'MISSING')
    check('census:has_joining_methodology',
          bool(cip.get('census_source', {}).get('joining_methodology')),
          'tract-level point-in-polygon' if cip.get('census_source', {}).get('joining_methodology') else 'MISSING')

# ---------------------------------------------------------------------------
# 8.4 — Qualitative validation protocol exists
# ---------------------------------------------------------------------------
qvp = load('qualitative-validation-protocol.yaml')
check('doc:qualitative_protocol_exists', qvp is not None,
      'present' if qvp else 'MISSING — sociology/education departments require mixed methods')
if qvp:
    protocol = qvp.get('observation_protocol', {})
    check('qualitative:has_pre_event', bool(protocol.get('pre_event')),
          'checklist present' if protocol.get('pre_event') else 'MISSING')
    check('qualitative:has_during_event', bool(protocol.get('during_event')),
          'checklist present' if protocol.get('during_event') else 'MISSING')
    check('qualitative:has_post_event', bool(protocol.get('post_event')),
          'checklist present' if protocol.get('post_event') else 'MISSING')
    before = qvp.get('before_period_requirements', {})
    check('qualitative:minimum_sessions',
          (before.get('minimum_sessions') or 0) >= 4,
          f'{before.get("minimum_sessions")} sessions required')
    alignment = qvp.get('quantitative_qualitative_alignment_checks', {})
    checks_list = alignment.get('checks', [])
    check('qualitative:alignment_checks', len(checks_list) >= 3,
          f'{len(checks_list)} alignment checks specified')

# ---------------------------------------------------------------------------
# 8.5 — Research questions registry exists and covers all disciplines
# ---------------------------------------------------------------------------
rqr = load('research-questions-registry.yaml')
check('doc:research_questions_registry_exists', rqr is not None,
      'present' if rqr else 'MISSING — no documented open questions')
if rqr:
    questions = rqr.get('questions', [])
    for d in DISCIPLINES:
        d_questions = [q for q in questions if q.get('discipline') == d]
        check(f'research_questions:{d}', len(d_questions) >= 2,
              f'{len(d_questions)} questions' if d_questions else 'NONE — discipline has no questions')
    # Every question has required fields
    for q in questions:
        qid = q.get('id', '?')
        check(f'research_question_complete:{qid}',
              all(q.get(f) for f in ('discipline', 'question', 'data_required', 'earliest_phase', 'status')),
              'complete' if all(q.get(f) for f in ('discipline', 'question', 'data_required', 'earliest_phase', 'status'))
              else 'incomplete')

# ---------------------------------------------------------------------------
# 8.6 — Statistical monitors spec exists
# ---------------------------------------------------------------------------
sm = load('statistical-monitors.yaml')
check('doc:statistical_monitors_exists', sm is not None,
      'present' if sm else 'MISSING — no post-launch monitoring plan')
if sm:
    monitors = sm.get('monitors', [])
    check('monitors:count', len(monitors) >= 5,
          f'{len(monitors)} monitors specified')
    # Key monitors must exist
    key_names = {'spatial_autocorrelation', 'temporal_autocorrelation',
                 'simpsons_paradox_detection', 'power_analysis', 'selection_bias_quantification'}
    found_names = {m.get('name') for m in monitors}
    missing = key_names - found_names
    check('monitors:key_monitors_present', not missing,
          f'all key monitors present' if not missing else f'MISSING: {missing}')
    # Every monitor has threshold and response
    for m in monitors:
        mid = m.get('id', '?')
        check(f'monitor_complete:{mid}',
              m.get('threshold') and m.get('response'),
              'has threshold + response' if m.get('threshold') and m.get('response') else 'incomplete')

# ---------------------------------------------------------------------------
# 8.7 — IRB readiness document exists
# ---------------------------------------------------------------------------
irb = load('irb-readiness.yaml')
check('doc:irb_readiness_exists', irb is not None,
      'present' if irb else 'MISSING — required before any academic partnership formalizes')
if irb:
    check('irb:no_exemption_claim',
          'does NOT claim' in str(irb.get('irb_classification_guidance', {}).get('note', '')),
          'correctly does not claim exemption')
    check('irb:has_consent_model', bool(irb.get('consent_model')),
          'consent model documented')
    check('irb:has_reidentification_assessment',
          bool(irb.get('re_identification_risk_assessment')),
          'risk assessment present')

# ---------------------------------------------------------------------------
# 8.8 — Selection bias is documented as a known limitation
# ---------------------------------------------------------------------------
if cvm:
    limitations = cvm.get('known_limitations', [])
    has_selection_bias = any('non-scanners' in str(l).lower() or 'non-attendees' in str(l).lower()
                            or 'selection' in str(l).lower() for l in limitations)
    check('limitation:selection_bias_documented', has_selection_bias,
          'documented in construct validity map' if has_selection_bias else 'NOT DOCUMENTED')

# ---------------------------------------------------------------------------
# 8.9 — MAUP is addressed
# ---------------------------------------------------------------------------
if sm:
    has_maup = any('maup' in str(m.get('name', '')).lower() for m in sm.get('monitors', []))
    check('limitation:maup_monitored', has_maup,
          'MAUP sensitivity monitor exists' if has_maup else 'NO MAUP MONITOR')
if rqr:
    has_maup_q = any('maup' in str(q).lower() for q in rqr.get('questions', []))
    check('limitation:maup_research_question', has_maup_q,
          'MAUP research question registered' if has_maup_q else 'NO MAUP QUESTION')

# ---------------------------------------------------------------------------
# REPORT
# ---------------------------------------------------------------------------
passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')
print(f'{"="*76}')
print(f'  LEVEL 9 — ACADEMIC FOUNDATIONS')
print(f'{"="*76}')
for name, status, detail in results:
    m = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {m}  {name:55} {detail}')
print(f'{"-"*76}')
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print(f'{"-"*76}')
sys.exit(0 if failed == 0 else 1)
