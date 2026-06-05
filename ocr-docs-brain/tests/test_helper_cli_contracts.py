#!/usr/bin/env python3
"""
test_helper_cli_contracts.py — Lock the CLI signatures of helpers that
CI workflows depend on.

Why this exists
===============
On 2026-06-01 a CCR pass on the Self-Checking Infrastructure
operationalization caught that `phantom-scan.yml` invoked
`open_drift_ticket.py` with `--report-source` — an argument that does
NOT exist on the helper. The shell `|| echo warning` masked the
argparse error; the workflow would have appeared to succeed while
NEVER firing a Linear ticket. Silent-failure-by-design.

This test file is the structural lock against that pattern. Any
CI workflow that calls a helper script SHOULD have a corresponding
contract test here that asserts the helper accepts the args the
workflow passes. If the helper's CLI changes, this test fails before
the next deploy.

Doctrine: ADR-003 §"Four properties that make it durable forever",
specifically the **Honest** property — produces evidence, not testimony.
The workflow's `|| echo warning` was testimony; this test is evidence.

Contracts under test
====================
1. ocr-docs-brain/scripts/open_drift_ticket.py
   - Required args: --report, --repo, --pr-number, --pr-url,
     --pr-author, --commit (all required per main()).
   - Behavior with valid args + missing LINEAR_API_KEY: exit 0
     ("LINEAR_API_KEY not set; skipping ticket creation").
   - Behavior with valid args + valid LINEAR_API_KEY + missing report:
     exit 1 ("could not read report").
   - Behavior with valid args + valid LINEAR_API_KEY + empty failures
     in report: exit 0 ("no failures to report").

2. ocr-docs-brain/scripts/scan_phantom_invariants.py
   - Required args: none (--sweep is default).
   - Optional: --pre-commit, --sweep, --emit-report PATH.
   - Behavior with --emit-report PATH on clean state: writes a JSON
     file in the shape consumed by open_drift_ticket.py.

Exit codes:
  0 — all contracts hold
  1 — at least one contract failed (helper CLI drift)
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Find the brain root (this file lives in BRAIN/tests/).
BRAIN_ROOT = Path(__file__).parent.parent
SCRIPTS = BRAIN_ROOT / 'scripts'

# Helpers under contract test.
OPEN_DRIFT = SCRIPTS / 'open_drift_ticket.py'
SCAN_PHANTOMS = SCRIPTS / 'scan_phantom_invariants.py'

results = []


def check(name: str, fn) -> None:
    try:
        detail = fn()
        results.append((name, 'PASS', detail or ''))
    except AssertionError as e:
        results.append((name, 'FAIL', str(e)))
    except Exception as e:
        results.append((name, 'FAIL', f'{type(e).__name__}: {e}'))


def run_helper(script: Path, args: list, env: dict = None,
               cwd: Path = None) -> subprocess.CompletedProcess:
    """Run a helper script with the given args. Returns CompletedProcess."""
    cmd = [sys.executable, str(script)] + args
    full_env = os.environ.copy()
    if env is not None:
        full_env.update(env)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=full_env,
        cwd=str(cwd) if cwd else None,
        timeout=30,
    )


# ─── open_drift_ticket.py contracts ──────────────────────────────────────────

def test_open_drift_argparse_accepts_required_args():
    """Helper accepts all six required args from the brain-location-audit
    pattern. Verifies argparse signature against the workflow's call."""
    assert OPEN_DRIFT.exists(), f'helper missing: {OPEN_DRIFT}'

    # Use a nonexistent report path — we want to test argparse signature,
    # not report parsing. Empty LINEAR_API_KEY triggers the no-op path
    # BEFORE report loading happens (per the helper's main()).
    result = run_helper(
        OPEN_DRIFT,
        args=[
            '--report', '/nonexistent/report.json',
            '--repo', 'OurCommunityRituals/OCR-docs',
            '--pr-number', '0',
            '--pr-url', 'https://example.com/run/123',
            '--pr-author', 'test-author',
            '--commit', 'abc12345',
        ],
        env={'LINEAR_API_KEY': ''},
    )

    # With empty LINEAR_API_KEY the helper exits 0 BEFORE loading the
    # report (per main() lines 238-241 — checks api_key and exits early).
    # If argparse rejected any of our args, exit would be 2.
    assert result.returncode == 0, (
        f'expected exit 0 (no-op on empty LINEAR_API_KEY), got '
        f'{result.returncode}. stderr: {result.stderr[:500]}'
    )
    return 'six required args accepted; no-op exit on empty LINEAR_API_KEY'


def test_open_drift_missing_required_arg_fails():
    """Helper rejects missing --report (proves --report IS required)."""
    result = run_helper(
        OPEN_DRIFT,
        args=[
            # --report deliberately omitted
            '--repo', 'OurCommunityRituals/OCR-docs',
            '--pr-number', '0',
            '--pr-url', 'https://example.com',
            '--pr-author', 'a',
            '--commit', 'c',
        ],
        env={'LINEAR_API_KEY': ''},
    )
    assert result.returncode == 2, (
        f'expected exit 2 (argparse error on missing --report), got '
        f'{result.returncode}. stderr: {result.stderr[:500]}'
    )
    assert 'report' in result.stderr.lower(), (
        f'expected argparse error to mention --report; got: {result.stderr[:500]}'
    )
    return 'argparse correctly rejects missing --report'


def test_open_drift_unknown_arg_fails():
    """Helper rejects --report-source (the CCR-found phantom arg)."""
    result = run_helper(
        OPEN_DRIFT,
        args=[
            '--report-source', 'phantom-scan',  # the CCR-found phantom arg
            '--report', '/tmp/nonexistent.json',
            '--repo', 'r',
            '--pr-number', '0',
            '--pr-url', 'u',
            '--pr-author', 'a',
            '--commit', 'c',
        ],
        env={'LINEAR_API_KEY': ''},
    )
    assert result.returncode == 2, (
        f'expected exit 2 (argparse error on unknown --report-source), got '
        f'{result.returncode}. stderr: {result.stderr[:500]}'
    )
    return 'argparse rejects --report-source (the original CCR-found bug)'


def test_open_drift_reads_scanner_report_shape():
    """Helper reads scan_phantom_invariants.py's report shape without
    JSON-shape errors. Tests the format contract between scanner and helper."""
    # Build a minimal report matching scan_phantom_invariants.py's emit shape
    # for a CLEAN state — empty failures, one pass.
    clean_report = {
        'product_id': 'brain',
        'summary': {'failed': 0, 'passed': 1, 'total': 1},
        'failures': [],
        'passes': [
            {'check': 'phantom_invariant_reference',
             'detail': 'Clean state proof.'}
        ],
    }
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False, encoding='utf-8',
    ) as f:
        json.dump(clean_report, f)
        report_path = f.name

    try:
        # LINEAR_API_KEY=fake won't make a real API call because the
        # helper exits 0 BEFORE the auth check on empty failures
        # (per main() lines 249-252).
        result = run_helper(
            OPEN_DRIFT,
            args=[
                '--report', report_path,
                '--repo', 'OurCommunityRituals/OCR-docs',
                '--pr-number', '0',
                '--pr-url', 'https://example.com',
                '--pr-author', 'test',
                '--commit', 'abc123',
            ],
            env={'LINEAR_API_KEY': 'fake-key-not-used'},
        )
        assert result.returncode == 0, (
            f'expected exit 0 (no failures in report → no-op), got '
            f'{result.returncode}. stderr: {result.stderr[:500]}'
        )
        assert 'no failures' in (result.stdout + result.stderr).lower(), (
            f'expected "no failures" message; got: '
            f'{result.stdout[:200]} | {result.stderr[:200]}'
        )
    finally:
        os.unlink(report_path)
    return 'scanner clean-state report shape consumed without error'


# ─── scan_phantom_invariants.py contracts ────────────────────────────────────

def test_scan_phantoms_emit_report_writes_valid_json():
    """--emit-report writes JSON in the shape open_drift_ticket.py expects."""
    assert SCAN_PHANTOMS.exists(), f'scanner missing: {SCAN_PHANTOMS}'

    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False,
    ) as f:
        report_path = f.name

    try:
        result = run_helper(
            SCAN_PHANTOMS,
            args=['--sweep', '--emit-report', report_path],
            # Run from BRAIN_ROOT/.. so the scanner can find the repo root.
            cwd=BRAIN_ROOT.parent,
        )
        # Exit code is 0 (clean) or 1 (phantoms) — both are valid;
        # we're testing the report-emission contract, not the scan result.
        assert result.returncode in (0, 1), (
            f'scanner exit unexpected: {result.returncode}. '
            f'stderr: {result.stderr[:500]}'
        )

        report = json.loads(Path(report_path).read_text(encoding='utf-8'))

        # Shape contract — these keys MUST be present.
        required_keys = {
            'product_id', 'summary', 'failures', 'passes',
        }
        missing = required_keys - set(report.keys())
        assert not missing, f'report missing required keys: {missing}'

        # Routing contract — product_id MUST be "brain" so the helper
        # routes the ticket to OCR-doc team via TEAM_ROUTING.
        assert report['product_id'] == 'brain', (
            f'expected product_id="brain", got {report["product_id"]!r}'
        )

        # Summary shape contract.
        summary_keys = {'failed', 'passed', 'total'}
        missing_summary = summary_keys - set(report['summary'].keys())
        assert not missing_summary, (
            f'summary missing keys: {missing_summary}'
        )

        # Failures shape contract — each failure has check + detail.
        for i, f in enumerate(report['failures']):
            assert 'check' in f and 'detail' in f, (
                f'failures[{i}] missing check or detail: {f}'
            )
            assert f['check'] == 'phantom_invariant_reference', (
                f'failures[{i}] check name: {f["check"]!r} '
                '(should be phantom_invariant_reference for helper routing)'
            )
    finally:
        os.unlink(report_path)
    return 'JSON report matches open_drift_ticket.py consumption contract'


# ─── Run all contracts ───────────────────────────────────────────────────────

CONTRACTS = [
    ('open_drift.argparse_accepts_six_required_args',
     test_open_drift_argparse_accepts_required_args),
    ('open_drift.argparse_rejects_missing_required',
     test_open_drift_missing_required_arg_fails),
    ('open_drift.argparse_rejects_phantom_report_source_arg',
     test_open_drift_unknown_arg_fails),
    ('open_drift.reads_scanner_report_shape',
     test_open_drift_reads_scanner_report_shape),
    ('scan_phantoms.emit_report_matches_helper_contract',
     test_scan_phantoms_emit_report_writes_valid_json),
]

for name, fn in CONTRACTS:
    check(name, fn)

# ─── Report ──────────────────────────────────────────────────────────────────

passed = sum(1 for _, s, _ in results if s == 'PASS')
failed = sum(1 for _, s, _ in results if s == 'FAIL')

bar = '=' * 76
print(bar)
print('  HELPER CLI CONTRACTS')
print(bar)
for name, status, detail in results:
    marker = '[PASS]' if status == 'PASS' else '[FAIL]'
    print(f'  {marker}  {name:55} {detail}')
print('-' * 76)
print(f'  {passed} pass / {failed} fail  (total {len(results)})')
print('-' * 76)
print()
print('Source of test: CCR-2026-06-01 caught open_drift_ticket.py')
print('integration that would have silently no-op\'d in CI. This test')
print('locks the helper CLI contracts so the next drift fails loud.')

sys.exit(0 if failed == 0 else 1)
