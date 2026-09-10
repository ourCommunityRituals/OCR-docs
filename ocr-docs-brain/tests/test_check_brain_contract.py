#!/usr/bin/env python3
"""
test_check_brain_contract.py — Regression lock for check_brain_contract.py's
invariant test-file resolution.

Why this exists
===============
On 2026-08-10 a CCR pass (run wf_ec339828-8ce) caught the brain
conformance gate false-failing on live invariants #22 and #25. Their
`test_file` values in architectural-invariants.yaml carry a trailing
human annotation in parentheses, e.g.:

    scripts/check-cross-repo-imports.sh (OSE repo)
    tests/e2e/0-architecture/sponsor-share-covenant.invariant.spec.ts (OSE repo — planned, OSE-663 / OSE-662)

`check_invariant_test_files` passed that raw string straight into
`repo.glob(f'**/{tf}')`. Because the ` (OSE repo…)` suffix is not part of
the path, the glob could NEVER match the real file (which exists in the
sibling OSE repo) — so both live invariants reported `missing_live` and
the gate FAILed even though zero test files were actually missing.

The fix added `_resolve_test_file(tf)`, which strips a trailing
' (' + annotation before globbing. This test locks that behavior so the
false-fail cannot silently return.

Exit codes:
  0 — all contracts hold
  1 — at least one contract failed
"""
import sys
import json
import tempfile
from pathlib import Path

# Keep output legible on consoles whose default encoding (e.g. Windows
# cp1252) cannot represent the non-ASCII chars this file prints.
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# Import the module under test. This file lives in BRAIN/tests/,
# the checker lives in BRAIN/scripts/.
BRAIN_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(BRAIN_ROOT / 'scripts'))

import check_brain_contract as cbc  # noqa: E402

results = []


def check(name: str, fn) -> None:
    try:
        detail = fn()
        results.append((name, 'PASS', detail or ''))
    except AssertionError as e:
        results.append((name, 'FAIL', str(e)))
    except Exception as e:
        results.append((name, 'FAIL', f'{type(e).__name__}: {e}'))


# ─── _resolve_test_file unit contracts ───────────────────────────────────────

def test_strips_trailing_ose_repo_annotation():
    """#22's shape: 'path (OSE repo)' → 'path'."""
    got = cbc._resolve_test_file('scripts/check-cross-repo-imports.sh (OSE repo)')
    assert got == 'scripts/check-cross-repo-imports.sh', got
    return got


def test_strips_multiword_annotation():
    """#25's shape: 'path (OSE repo — planned, OSE-663 / OSE-662)' → 'path'."""
    raw = ('tests/e2e/0-architecture/sponsor-share-covenant.invariant.spec.ts '
           '(OSE repo — planned, OSE-663 / OSE-662)')
    got = cbc._resolve_test_file(raw)
    assert got == 'tests/e2e/0-architecture/sponsor-share-covenant.invariant.spec.ts', got
    return got


def test_leaves_plain_path_untouched():
    """A path with no annotation must pass through unchanged."""
    raw = 'tests/e2e/foo.invariant.spec.ts'
    got = cbc._resolve_test_file(raw)
    assert got == raw, got
    return got


# ─── End-to-end contract against check_invariant_test_files ──────────────────

def test_annotated_live_invariant_matches_when_file_exists():
    """The bug reproducer: a live invariant whose test_file carries an
    '(OSE repo)' suffix must PASS when the underlying file exists in the repo.

    Before the fix this FAILed (missing_live) because the annotated string
    was globbed verbatim and never matched."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        # Create the real file the invariant points at.
        target = repo / 'scripts' / 'check-cross-repo-imports.sh'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('#!/usr/bin/env bash\n', encoding='utf-8')

        brain = {
            'invariants': {
                'invariants': [
                    {
                        'id': 22,
                        'applies_to': ['ose'],
                        'status': 'live',
                        'test_file': 'scripts/check-cross-repo-imports.sh (OSE repo)',
                    },
                ]
            }
        }
        name, status, detail = cbc.check_invariant_test_files(repo, brain, 'ose')
        assert status == cbc.PASS, (
            f'expected PASS, got {status}: {detail}'
        )
    return 'annotated live invariant resolves to existing file -> PASS'


def test_annotated_live_invariant_still_fails_when_file_absent():
    """Guard against over-stripping: if the resolved file genuinely does
    NOT exist, a live invariant must still FAIL (missing_live)."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)  # empty repo — target file absent
        brain = {
            'invariants': {
                'invariants': [
                    {
                        'id': 22,
                        'applies_to': ['ose'],
                        'status': 'live',
                        'test_file': 'scripts/check-cross-repo-imports.sh (OSE repo)',
                    },
                ]
            }
        }
        name, status, detail = cbc.check_invariant_test_files(repo, brain, 'ose')
        assert status == cbc.FAIL, (
            f'expected FAIL for genuinely missing live file, got {status}: {detail}'
        )
    return 'genuinely missing live file still FAILs (no false pass)'


# ─── lives_in ownership axis (OCR-41) ────────────────────────────────────────
# `applies_to` = which products an invariant PROTECTS; that is not the same as
# where the enforcing artifact must physically LIVE. A fleet-wide invariant
# (shared runner/CI substrate, or the OSE×OW composition seam) can be authored +
# validated by a spec in one owner repo (`lives_in`); a protected-but-not-owning
# repo (e.g. standalone WKRP) must not be forced to carry the file.

def _owned_brain(lives_in):
    return {
        'invariants': {
            'invariants': [
                {
                    'id': 11,
                    'applies_to': ['ose', 'wkrp', 'oaw'],
                    'lives_in': lives_in,
                    'status': 'live',
                    'test_file': 'runner-environment.invariant.spec.ts',
                },
            ]
        }
    }


def test_lives_in_not_required_in_protected_only_repo():
    """A fleet-wide invariant WKRP is protected by (in applies_to) but does not
    own (not in lives_in) must PASS even though the file is absent. Accepts both
    a single-repo string and a list (composition invariants are multi-home)."""
    for lives_in in ('ose', ['ose']):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)  # empty — file deliberately absent
            name, status, detail = cbc.check_invariant_test_files(
                repo, _owned_brain(lives_in), 'wkrp')
            assert status == cbc.PASS, (
                f'lives_in={lives_in!r}: protected-only repo should not require '
                f'artifact; got {status}: {detail}')
    return 'lives_in invariant not demanded in protected-only repo (str + list)'


def test_lives_in_still_required_in_owner_repo():
    """The owner repo (in lives_in) must still FAIL when the artifact is
    genuinely missing — ownership routing must not blunt enforcement at the
    real site."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)  # empty — file absent
        name, status, detail = cbc.check_invariant_test_files(
            repo, _owned_brain('ose'), 'ose')
        assert status == cbc.FAIL, (
            f'owner repo must still fail on missing artifact; '
            f'got {status}: {detail}')
    return 'owner repo still FAILs on missing lives_in artifact'


def test_standalone_default_requires_in_every_applies_to():
    """Back-compat: an invariant with no lives_in is consumer-owned and required
    in EVERY applies_to product (unchanged legacy behavior)."""
    brain = {
        'invariants': {
            'invariants': [
                {
                    'id': 99,
                    'applies_to': ['ose', 'wkrp'],
                    'status': 'live',
                    'test_file': 'some.invariant.spec.ts',
                },
            ]
        }
    }
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)  # empty
        for pid in ('ose', 'wkrp'):
            _, status, detail = cbc.check_invariant_test_files(repo, brain, pid)
            assert status == cbc.FAIL, (
                f'standalone invariant must be required in {pid}; got {status}')
    return 'standalone (default) still required in every applies_to product'


# ─── Regulatory-pool / required-tag checks (OCR-70) ──────────────────────────

def test_regulatory_pools_pass_when_dataset_referenced():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        (repo / 'code.ts').write_text('const ds = "oer_general";\n', encoding='utf-8')
        product = {'regulatory_pools': ['general'],
                   'bigquery_datasets': {'general': 'oer_general'}}
        _, status, detail = cbc.check_regulatory_pools_present(repo, product)
        assert status == cbc.PASS, detail
    return 'dataset referenced in code → PASS'


def test_regulatory_pools_fail_when_dataset_absent():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)  # empty — dataset name never appears
        product = {'regulatory_pools': ['general'],
                   'bigquery_datasets': {'general': 'oer_general'}}
        _, status, detail = cbc.check_regulatory_pools_present(repo, product)
        assert status == cbc.FAIL, f'expected FAIL, got {status}: {detail}'
        assert 'oer_general' in detail, detail
    return 'dataset absent → FAIL with actionable detail'


def test_pipeline_present_false_skips_pool_and_tag_checks():
    """pipeline_present=false (has code, no BigQuery pipeline yet — the WKRP
    case) must PASS both data-pipeline checks without scanning code."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)  # empty
        product = {'pipeline_present': False,
                   'regulatory_pools': ['general'],
                   'bigquery_datasets': {'general': 'oer_general'},
                   'required_tags': ['corridor_id']}
        _, s1, _ = cbc.check_regulatory_pools_present(repo, product)
        _, s2, _ = cbc.check_required_tags_used(repo, product)
        assert s1 == cbc.PASS and s2 == cbc.PASS, (s1, s2)
    return 'pipeline_present=false → both checks PASS (deferred)'


def test_required_tags_fail_lists_missing():
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        (repo / 'code.ts').write_text('const a = "corridor_id";\n', encoding='utf-8')
        product = {'required_tags': ['corridor_id', 'venue_id']}
        _, status, detail = cbc.check_required_tags_used(repo, product)
        assert status == cbc.FAIL, detail
        assert 'venue_id' in detail and 'corridor_id' not in detail.replace('venue_id', ''), detail
    return 'present tag ignored, missing tag reported'


# ─── Stub-repo exemption end-to-end (code_present:false, #91) ────────────────

def _run_checker(product_id: str):
    """Invoke the real checker against the real brain with an EMPTY repo.
    Returns (exit_code, report_dict). Empty repo means any code-presence
    check must fail — so the only way to exit 0 is the stub exemption.

    Runs cbc.main() IN-PROCESS (catching SystemExit) rather than spawning a
    subprocess. The self-tests are themselves launched as a subprocess by
    run_script_tests.py; adding a third nested subprocess under
    capture_output triggered a Windows access violation (0xC0000005 /
    exit 3221225477) on the self-hosted runner — the OSE-696 SIGSEGV flake
    class. In-process keeps it to two levels and is deterministic."""
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / 'repo'
        repo.mkdir()
        report_path = Path(td) / 'report.json'
        argv = ['check_brain_contract.py', '--brain', str(BRAIN_ROOT),
                '--repo', str(repo), '--product-id', product_id,
                '--report-path', str(report_path)]
        old_argv = sys.argv
        sys.argv = argv
        code = 0
        try:
            cbc.main()
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
        finally:
            sys.argv = old_argv
        report = json.loads(report_path.read_text(encoding='utf-8')) \
            if report_path.exists() else {}
    return code, report


def test_stub_repo_code_present_false_exits_zero():
    """A registry entry flagged code_present:false (osp/osr/osg/oaw) must be
    exempt: exit 0 + skipped, even with zero application code. This locks the
    OCR-docs #91 fix that unblocked the stub-repo propagation PRs."""
    rc, report = _run_checker('osp')
    assert rc == 0, f'expected exit 0 for stub repo, got {rc}'
    assert report.get('skipped') is True, report
    return 'code_present:false → exit 0, skipped=true'


def test_code_present_product_runs_checks_and_fails_on_empty_repo():
    """Guard the other side: a product NOT flagged code_present:false (ose)
    must actually run conformance and FAIL against an empty repo — proving the
    exemption is narrow and the checks aren't globally disabled."""
    rc, report = _run_checker('ose')
    assert rc == 1, f'expected exit 1 for code-present product, got {rc}'
    assert report.get('skipped') is not True, report
    assert report.get('summary', {}).get('failed', 0) >= 1, report
    return 'code-present product → checks run, empty repo FAILs'


# ─── enforcement_kind: brain_script — workflow-wiring verification ───────────
# A brain-resident guard (Invariant #22's check_cross_repo_imports.py) is not a
# repo-local file to glob; conformance must verify a PR-blocking workflow step
# actually INVOKES it and is not neutered. Presence != enforcement.

_GUARD = 'check_cross_repo_imports.py'

def _brain_script_brain(status='live', applies_to=('ose', 'wkrp')):
    return {'invariants': {'invariants': [{
        'id': 22, 'name': 'cross_repo_import_isolation',
        'applies_to': list(applies_to), 'status': status,
        'enforcement_kind': 'brain_script',
        'test_file': 'ocr-docs-brain/scripts/check_cross_repo_imports.py',
    }]}}


def _repo_with_workflow(td, yaml_text):
    repo = Path(td)
    wf = repo / '.github' / 'workflows' / 'ci.yml'
    wf.parent.mkdir(parents=True, exist_ok=True)
    wf.write_text(yaml_text, encoding='utf-8')
    return repo


def test_brain_script_wired_step_passes():
    wf = ("name: CI\non:\n  pull_request:\n    branches: [main]\njobs:\n"
          "  sec:\n    runs-on: ubuntu-latest\n    steps:\n"
          "      - run: python scripts/check_cross_repo_imports.py --repo . "
          "--product-id ose --brain b\n")
    with tempfile.TemporaryDirectory() as td:
        _, status, detail = cbc.check_invariant_test_files(
            _repo_with_workflow(td, wf), _brain_script_brain(), 'ose')
        assert status == cbc.PASS, f'wired guard should PASS: {detail}'
    return 'brain_script: wired PR step -> PASS'


def test_brain_script_missing_step_fails_live():
    wf = ("name: CI\non:\n  pull_request:\njobs:\n  sec:\n    steps:\n"
          "      - run: npm test\n")
    with tempfile.TemporaryDirectory() as td:
        _, status, detail = cbc.check_invariant_test_files(
            _repo_with_workflow(td, wf), _brain_script_brain(), 'ose')
        assert status == cbc.FAIL, f'missing guard step should FAIL: {detail}'
    return 'brain_script: no wired step -> FAIL (live)'


def test_brain_script_continue_on_error_is_neutered():
    wf = ("name: CI\non:\n  pull_request:\njobs:\n  sec:\n    steps:\n"
          "      - run: python scripts/check_cross_repo_imports.py --repo .\n"
          "        continue-on-error: true\n")
    with tempfile.TemporaryDirectory() as td:
        _, status, detail = cbc.check_invariant_test_files(
            _repo_with_workflow(td, wf), _brain_script_brain(), 'ose')
        assert status == cbc.FAIL, f'continue-on-error step is neutered: {detail}'
    return 'brain_script: continue-on-error step -> FAIL'


def test_brain_script_swallowed_exit_is_neutered():
    wf = ("name: CI\non:\n  pull_request:\njobs:\n  sec:\n    steps:\n"
          "      - run: python scripts/check_cross_repo_imports.py --repo . || true\n")
    with tempfile.TemporaryDirectory() as td:
        _, status, detail = cbc.check_invariant_test_files(
            _repo_with_workflow(td, wf), _brain_script_brain(), 'ose')
        assert status == cbc.FAIL, f'|| true swallows exit: {detail}'
    return 'brain_script: run with || true -> FAIL'


def test_brain_script_non_pr_trigger_is_not_wired():
    wf = ("name: CI\non:\n  push:\n    branches: [main]\njobs:\n  sec:\n    steps:\n"
          "      - run: python scripts/check_cross_repo_imports.py --repo .\n")
    with tempfile.TemporaryDirectory() as td:
        _, status, detail = cbc.check_invariant_test_files(
            _repo_with_workflow(td, wf), _brain_script_brain(), 'ose')
        assert status == cbc.FAIL, f'push-only trigger is not PR-blocking: {detail}'
    return 'brain_script: non-PR trigger -> FAIL'


def test_brain_script_not_applicable_product_passes():
    """osm is not in #22 applies_to → no wiring demanded even with no workflow."""
    with tempfile.TemporaryDirectory() as td:
        _, status, detail = cbc.check_invariant_test_files(
            Path(td), _brain_script_brain(applies_to=('ose', 'wkrp')), 'osm')
        assert status == cbc.PASS, f'non-applicable product should PASS: {detail}'
    return 'brain_script: product not in applies_to -> PASS'


# ─── Run all contracts ───────────────────────────────────────────────────────

CONTRACTS = [
    ('resolve.strips_ose_repo_annotation', test_strips_trailing_ose_repo_annotation),
    ('resolve.strips_multiword_annotation', test_strips_multiword_annotation),
    ('resolve.leaves_plain_path_untouched', test_leaves_plain_path_untouched),
    ('invariant.annotated_live_matches_existing_file',
     test_annotated_live_invariant_matches_when_file_exists),
    ('invariant.annotated_live_missing_still_fails',
     test_annotated_live_invariant_still_fails_when_file_absent),
    ('lives_in.not_required_in_protected_only_repo',
     test_lives_in_not_required_in_protected_only_repo),
    ('lives_in.required_in_owner_repo',
     test_lives_in_still_required_in_owner_repo),
    ('lives_in.absent_default_required_in_every_applies_to',
     test_standalone_default_requires_in_every_applies_to),
    ('pools.pass_when_dataset_referenced', test_regulatory_pools_pass_when_dataset_referenced),
    ('pools.fail_when_dataset_absent', test_regulatory_pools_fail_when_dataset_absent),
    ('pipeline_present_false.skips_both', test_pipeline_present_false_skips_pool_and_tag_checks),
    ('tags.fail_lists_missing', test_required_tags_fail_lists_missing),
    ('stub.code_present_false_exits_zero', test_stub_repo_code_present_false_exits_zero),
    ('stub.code_present_product_still_runs', test_code_present_product_runs_checks_and_fails_on_empty_repo),
    ('brain_script.wired_step_passes', test_brain_script_wired_step_passes),
    ('brain_script.missing_step_fails_live', test_brain_script_missing_step_fails_live),
    ('brain_script.continue_on_error_neutered', test_brain_script_continue_on_error_is_neutered),
    ('brain_script.swallowed_exit_neutered', test_brain_script_swallowed_exit_is_neutered),
    ('brain_script.non_pr_trigger_not_wired', test_brain_script_non_pr_trigger_is_not_wired),
    ('brain_script.not_applicable_passes', test_brain_script_not_applicable_product_passes),
]

for name, fn in CONTRACTS:
    check(name, fn)

# ─── Report ──────────────────────────────────────────────────────────────────

passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')

bar = '=' * 76
print(bar)
print('  CHECK_BRAIN_CONTRACT — TEST_FILE RESOLUTION')
print(bar)
for name, status, detail in results:
    marker = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {marker}  {name:50} {detail}')
print('-' * 76)
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print('-' * 76)
print()
print('Source of test: CCR run wf_ec339828-8ce (2026-08-10) caught')
print('live invariants #22/#25 false-failing on annotated test_file values.')

sys.exit(0 if failed == 0 else 1)
