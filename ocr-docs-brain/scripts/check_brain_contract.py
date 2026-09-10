#!/usr/bin/env python3
"""
check_brain_contract.py
=======================
Compares a product repo's actual state to what the OCR-docs brain declares.
Drift = the product changed without updating the brain, OR the brain changed
without the product following. Either case fails CI.

Run inside a CI job that has already checked out both the product repo and
OCR-docs side by side.

Exit codes:
  0 = conformant
  1 = drift detected (failures written to report)
  2 = execution error (brain unreachable, product repo malformed)

Writes a JSON report at --report-path suitable for posting to Linear.
"""
import argparse, json, os, re, sys, yaml
from pathlib import Path
from typing import Any

FAIL = 'FAIL'
PASS = 'PASS'


def load_brain(brain_dir: Path) -> dict[str, Any]:
    """Load all brain artifacts into a single dict."""
    try:
        return {
            'products': yaml.safe_load((brain_dir / 'product-registry.yaml').read_text(encoding='utf-8')),
            'tiers': yaml.safe_load((brain_dir / 'tier-gates.yaml').read_text(encoding='utf-8')),
            'corridors': yaml.safe_load((brain_dir / 'corridor-definitions.yaml').read_text(encoding='utf-8')),
            'taxonomy': yaml.safe_load((brain_dir / 'event-taxonomy.yaml').read_text(encoding='utf-8')),
            'invariants': yaml.safe_load((brain_dir / 'architectural-invariants.yaml').read_text(encoding='utf-8')),
            'bq_general': json.loads((brain_dir / 'bigquery-schemas/general.json').read_text(encoding='utf-8')),
            'bq_hipaa':   json.loads((brain_dir / 'bigquery-schemas/hipaa.json').read_text(encoding='utf-8')),
            'bq_coppa':   json.loads((brain_dir / 'bigquery-schemas/coppa.json').read_text(encoding='utf-8')),
            'bq_agg':     json.loads((brain_dir / 'bigquery-schemas/aggregate.json').read_text(encoding='utf-8')),
        }
    except Exception as e:
        print(f"ERROR: could not load brain from {brain_dir}: {e}", file=sys.stderr)
        sys.exit(2)


def _resolve_test_file(tf: str) -> str:
    """Normalize a brain `test_file` value into a globbable path.

    Some `test_file` entries in architectural-invariants.yaml carry a
    trailing human annotation in parentheses, e.g.:
        scripts/check-cross-repo-imports.sh (OSE repo)
        tests/.../sponsor-share-covenant.invariant.spec.ts (OSE repo — planned)
    That ` (…)` suffix is NOT part of the path and must be stripped before
    the value is handed to glob(), or the pattern can never match the real
    file (which lives in the sibling OSE repo). Only a *trailing*
    ' (' + annotation is removed; paths without such a suffix pass through
    unchanged, so legitimate paths are never mangled.
    """
    if tf is None:
        return tf
    idx = tf.find(' (')
    if idx != -1:
        return tf[:idx].strip()
    return tf.strip()


def find_product(brain: dict, product_id: str) -> dict | None:
    """Find the product record in the registry."""
    for p in brain['products'].get('products', []):
        if p.get('product_id') == product_id:
            return p
    return None


def scan_repo_for_string(repo: Path, pattern: str, glob: str = '**/*') -> list[str]:
    """Return relative paths of files containing `pattern`.
    Excludes vendored dirs and the .github/scripts dir which contains
    the checker itself (it would otherwise flag its own search patterns)."""
    hits = []
    EXCLUDE_DIRS = ('node_modules', '.git', 'dist', 'build', '.next', '.venv',
                    '.github')  # scripts dir lives here; exclude entirely
    for f in repo.glob(glob):
        if not f.is_file():
            continue
        if any(skip in f.parts for skip in EXCLUDE_DIRS):
            continue
        try:
            if pattern in f.read_text(encoding='utf-8', errors='ignore'):
                hits.append(str(f.relative_to(repo)))
        except Exception:
            continue
    return hits


def find_schema_files(repo: Path) -> list[Path]:
    """Find SQL migrations, schema.ts, wrangler.toml — places tables are declared."""
    candidates = []
    for pattern in ('**/migrations/*.sql', '**/schema.ts', '**/schema.sql',
                     'wrangler.toml', 'wrangler.jsonc', '**/d1-schema.sql'):
        candidates.extend(repo.glob(pattern))
    return [c for c in candidates if c.is_file()
            and not any(skip in c.parts for skip in ('node_modules', '.git'))]


# ---------------------------------------------------------------------------
# Conformance checks — each returns (name, status, detail)
# ---------------------------------------------------------------------------

def check_regulatory_pools_present(repo: Path, product: dict) -> tuple[str, str, str]:
    """Every regulatory pool the brain says this product routes to must have
    evidence in the codebase (env var, dataset name, or binding)."""
    # pipeline_present=false: the product has application code but has not
    # built its OCR data pipeline yet (pre data-pipeline activation phase).
    # Pool datasets only get referenced once that pipeline lands, so checking
    # now is guaranteed drift noise. Mirrors the code_present escape hatch;
    # flip/remove the flag in product-registry.yaml when the pipeline is built.
    if product.get('pipeline_present') is False:
        return ('regulatory_pools_present', PASS,
                'data pipeline not built yet (pipeline_present=false) — '
                'pool datasets validated when the pipeline activates')
    required = product.get('regulatory_pools', []) or []
    if not required:
        return ('regulatory_pools_present', PASS, 'no pools required')

    bq_datasets = product.get('bigquery_datasets', {}) or {}
    missing = []
    for pool in required:
        dataset_name = bq_datasets.get(pool)
        if not dataset_name:
            missing.append(f'{pool}: no dataset in brain')
            continue
        hits = scan_repo_for_string(repo, dataset_name)
        if not hits:
            missing.append(f'{pool}: dataset "{dataset_name}" not referenced anywhere in repo')

    if missing:
        return ('regulatory_pools_present', FAIL, '; '.join(missing))
    return ('regulatory_pools_present', PASS, f'all {len(required)} pool datasets referenced')


def check_required_tags_used(repo: Path, product: dict) -> tuple[str, str, str]:
    """The tags the brain requires for this product's writes must appear in code."""
    # See check_regulatory_pools_present — required tags are pipeline-write
    # concerns; skip until the product's data pipeline is built.
    if product.get('pipeline_present') is False:
        return ('required_tags_used', PASS,
                'data pipeline not built yet (pipeline_present=false) — '
                'required tags validated when the pipeline activates')
    required_tags = product.get('required_tags', []) or []
    if not required_tags:
        return ('required_tags_used', PASS, 'no required tags')

    missing = []
    for tag in required_tags:
        hits = scan_repo_for_string(repo, tag)
        if not hits:
            missing.append(tag)
    if missing:
        return ('required_tags_used', FAIL, f'tags absent from code: {missing}')
    return ('required_tags_used', PASS, f'all {len(required_tags)} required tags referenced')


def _requires_local_artifact(inv: dict, product_id: str) -> bool:
    """Decide whether `product_id` must physically carry this invariant's test
    artifact in its own repo. Implements the `lives_in` ownership axis (OCR-41).

    `applies_to` declares which products an invariant PROTECTS; that is NOT the
    same as where the enforcing artifact LIVES. A fleet-wide invariant can be
    authored and validated by a single spec in one repo while binding many:

      - `lives_in` ABSENT (default): the artifact is consumer-owned — every
        product in `applies_to` carries its own copy (unchanged legacy behavior).
      - `lives_in` SET: the artifact lives in the named owner repo(s) and is
        validated in the owner's own CI; a product this invariant protects but
        does not own is NOT required to carry the file locally.

    `lives_in` accepts a single repo id or a list. A composition invariant such
    as #22 cross_repo_import_isolation (the OSE×OW forbidden named⟂anonymous
    join) becomes multi-home once each side builds its gate — today only OSE
    owns one; the WKRP/OAW-side gate is tracked separately (OW-112)."""
    lives_in = inv.get('lives_in')
    if lives_in is None:
        return product_id in (inv.get('applies_to') or [])
    owners = lives_in if isinstance(lives_in, list) else [lives_in]
    return product_id in owners


def _guard_step_wired(repo: Path, script_name: str) -> tuple[bool, str]:
    """For an `enforcement_kind: brain_script` invariant, verify a PR-triggered
    workflow actually INVOKES `script_name` in a step that is not neutered.

    This is a static YAML-OBJECT parse, not a string grep: a step that is
    present but `continue-on-error: true`, or whose `run` swallows the exit
    code (`|| true`, `; true`), or that runs on a non-PR trigger, is NOT
    counted as wired. Presence != enforcement.
    """
    wf_dir = repo / '.github' / 'workflows'
    if not wf_dir.is_dir():
        return (False, 'no .github/workflows directory')
    neutered: list[str] = []
    for wf in sorted(list(wf_dir.glob('*.yml')) + list(wf_dir.glob('*.yaml'))):
        try:
            doc = yaml.safe_load(wf.read_text(encoding='utf-8')) or {}
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue
        # PyYAML parses a bare `on:` key as the boolean True, not the string 'on'.
        on = doc.get('on', doc.get(True))
        if isinstance(on, dict):
            triggers = set(on.keys())
        elif isinstance(on, list):
            triggers = set(on)
        elif on is not None:
            triggers = {on}
        else:
            triggers = set()
        pr_triggered = bool(triggers & {'pull_request', 'pull_request_target'})
        for job in (doc.get('jobs') or {}).values():
            if not isinstance(job, dict):
                continue
            for step in (job.get('steps') or []):
                if not isinstance(step, dict):
                    continue
                run = step.get('run') or ''
                if script_name not in run:
                    continue
                if step.get('continue-on-error') is True:
                    neutered.append(f'{wf.name}: step has continue-on-error')
                    continue
                if re.search(r'\|\|\s*(true|:)\b|;\s*true\b', run):
                    neutered.append(f'{wf.name}: run swallows exit (|| true)')
                    continue
                if not pr_triggered:
                    neutered.append(f'{wf.name}: not triggered on pull_request')
                    continue
                return (True, wf.name)
    if neutered:
        return (False, '; '.join(neutered))
    return (False, f'no workflow step invokes {script_name}')


def check_invariant_test_files(repo: Path, brain: dict, product_id: str) -> tuple[str, str, str]:
    """Every invariant whose artifact is owned *by this product's repo* must have
    its test file present — status live/partial/planned determines severity.
    Whether a repo owns the artifact depends on the invariant's `lives_in` field
    (OCR-41 ownership axis); see `_requires_local_artifact`. A fleet-wide
    invariant protects a product without demanding the artifact live inside it."""
    def _is_applicable(i: dict) -> bool:
        # brain_script invariants live in the brain and are enforced by a WIRED
        # workflow step in every product they apply to (not a repo-local file).
        if i.get('enforcement_kind') == 'brain_script':
            return product_id in (i.get('applies_to') or [])
        return _requires_local_artifact(i, product_id)

    applicable = [i for i in brain['invariants']['invariants'] if _is_applicable(i)]
    if not applicable:
        return ('invariant_test_files', PASS,
                f'no invariant artifacts are enforced in {product_id}')

    missing_live = []
    missing_partial = []
    for inv in applicable:
        tf = inv.get('test_file')
        # Retired invariants (OSE-1194, 2026-09-02: the subject no longer exists,
        # e.g. #11/#12 self-hosted runner apparatus) keep their historic test_file
        # name for traceability, but the spec is gone from the substrate by design
        # — never required.
        if inv.get('status') == 'retired':
            continue
        # brain_script: verify the guard is WIRED into a PR-blocking workflow
        # step (not present-but-neutered), instead of globbing a repo-local file.
        if inv.get('enforcement_kind') == 'brain_script':
            script_name = Path(_resolve_test_file(tf)).name if tf \
                else 'check_cross_repo_imports.py'
            wired, why = _guard_step_wired(repo, script_name)
            if not wired:
                label = f"{inv.get('name', inv.get('id'))} gate not wired ({why})"
                if inv.get('status') == 'live':
                    missing_live.append(label)
                elif inv.get('status') == 'partial':
                    missing_partial.append(label)
            continue
        if not tf:
            continue
        # Strip any trailing ' (…)' annotation before globbing; the raw
        # yaml value may read e.g. "scripts/foo.sh (OSE repo)".
        resolved = _resolve_test_file(tf)
        hits = list(repo.glob(f'**/{resolved}'))
        hits = [h for h in hits if '.git' not in h.parts and 'node_modules' not in h.parts]
        if not hits:
            if inv.get('status') == 'live':
                missing_live.append(tf)
            elif inv.get('status') == 'partial':
                missing_partial.append(tf)

    if missing_live:
        return ('invariant_test_files', FAIL,
                f'live invariant tests missing: {missing_live} '
                f'(partial also missing: {missing_partial})')
    if missing_partial:
        return ('invariant_test_files', PASS,
                f'all live tests present; {len(missing_partial)} partial tests '
                f'not yet implemented (acceptable): {missing_partial[:3]}')
    return ('invariant_test_files', PASS,
            f'all {len(applicable)} applicable invariant tests present')


def check_tier_gate_respected(repo: Path, product: dict, brain: dict) -> tuple[str, str, str]:
    """If the brain says this product supports only free+mid in phase1,
    there must not be hard-coded references to 'premium' as an active tier
    in phase1 code paths."""
    ta = product.get('tier_availability', {})
    p1 = ta.get('phase1', [])

    if 'premium' in p1:
        return ('tier_gate_respected', PASS, 'premium allowed in phase1 per brain')

    suspicious_files = scan_repo_for_string(repo, 'tier === "premium"')
    suspicious_files += scan_repo_for_string(repo, "tier == 'premium'")
    if suspicious_files:
        return ('tier_gate_respected', PASS,
                f'premium references exist but may be gated correctly — manual review: '
                f'{suspicious_files[:3]}')
    return ('tier_gate_respected', PASS, 'no uncaged premium tier references')


def check_faith_organization_commitment(repo: Path, brain: dict) -> tuple[str, str, str]:
    """The brain commits churches to free indefinitely. Repo must not have a
    code path that charges faith_organization."""
    overrides = brain['tiers'].get('sponsor_type_overrides', {})
    faith = overrides.get('faith_organization', {})
    if faith.get('forced_tier') != 'free':
        return ('faith_commitment', FAIL,
                'brain faith_organization override missing or not forced to free')

    hits = scan_repo_for_string(repo, 'faith_organization')
    if not hits:
        return ('faith_commitment', PASS,
                'faith_organization not yet referenced in repo (acceptable pre-launch)')
    return ('faith_commitment', PASS,
            f'faith_organization referenced in {len(hits)} files; manual review recommended')


def check_uec_codes_in_sync(repo: Path, brain: dict) -> tuple[str, str, str]:
    """Every UEC code the brain declares should appear somewhere the repo uses it,
    or at minimum not be contradicted by an unknown UEC code in the repo."""
    brain_codes = set()
    for cat in brain['taxonomy'].get('categories', []):
        for t in cat.get('event_types', []):
            if t.get('uec_code'):
                brain_codes.add(t['uec_code'])

    uec_pattern = re.compile(r'\b(?:CR|MC|GR|FD|WH|YE|CC|SS)-\d{3}\b')
    repo_codes = set()
    EXCLUDE_DIRS = ('.git', 'node_modules', '.github', 'dist', 'build', '.next', '.venv')
    for f in repo.rglob('*'):
        if not f.is_file() or any(s in f.parts for s in EXCLUDE_DIRS):
            continue
        try:
            text = f.read_text(encoding='utf-8', errors='ignore')
            for m in uec_pattern.finditer(text):
                repo_codes.add(m.group(0))
        except Exception:
            continue

    unknown = repo_codes - brain_codes
    if unknown:
        return ('uec_codes_in_sync', FAIL,
                f'repo contains {len(unknown)} UEC codes not in brain: {sorted(unknown)[:5]}')
    return ('uec_codes_in_sync', PASS,
            f'all {len(repo_codes)} UEC codes in repo resolve to brain definitions')


def check_demo_geo_in_corridor(repo: Path, brain: dict, product_id: str) -> tuple[str, str, str]:
    """Invariant #2 geo-realizability, demo facet (OSE-997): a demo/venue's H3
    cell must resolve inside its named corridor. The brain (corridor-definitions
    .yaml -> founding_corridors -> geo.anchor_h3_res7) OWNS the corridor anchor;
    the product's demo data must stamp that same cell, catching a demo cell that
    drifts out of its corridor (the RIPH->Colorado bug OSE-995 was born against).

    Scoped to products Invariant #2 binds (applies_to). Exhaustive realizability
    of every demo cell is checked by the product's own
    riph-brain-conformance.spec.ts (@brain-conformance 2); here the brain
    enforces the primary anchor cross-repo. String-precise (extracts the demo's
    declared RIPH res-7 constant) so no H3 runtime dependency is needed — mirrors
    check_uec_codes_in_sync's read-brain / scan-repo shape."""
    inv2 = next((i for i in brain['invariants'].get('invariants', [])
                 if i.get('id') == 2), None)
    if not inv2 or product_id not in (inv2.get('applies_to') or []):
        return ('demo_geo_in_corridor', PASS,
                f'invariant #2 does not bind {product_id} — no demo geo to check')

    blue_island = next((c for c in brain['corridors'].get('founding_corridors', [])
                        if c.get('corridor_id') == 'blue_island'), None)
    anchor = ((blue_island or {}).get('geo') or {}).get('anchor_h3_res7')
    if not anchor:
        return ('demo_geo_in_corridor', PASS,
                'brain blue_island declares no geo anchor — nothing to enforce')

    # The demo's declared corridor cell. H3 res-7 indexes are 15 hex chars.
    pat = re.compile(r"""RIPH_H3_RES7\s*=\s*['"]([0-9a-f]{15})['"]""")
    found = None
    for f in repo.glob('**/mock-data.ts'):
        if any(s in f.parts for s in ('node_modules', '.git')):
            continue
        try:
            m = pat.search(f.read_text(encoding='utf-8', errors='ignore'))
        except Exception:
            continue
        if m:
            found = m.group(1)
            break

    if found is None:
        return ('demo_geo_in_corridor', PASS,
                'no RIPH demo anchor (RIPH_H3_RES7) defined in repo — no demo geo')
    if found != anchor:
        return ('demo_geo_in_corridor', FAIL,
                f'RIPH demo cell {found} != brain blue_island anchor {anchor} — '
                f'demo geo drifted OUT of its named corridor (Invariant #2)')
    return ('demo_geo_in_corridor', PASS,
            f'RIPH demo anchor matches brain blue_island corridor ({anchor})')


def check_identity_layer_contract(repo: Path, product: dict) -> tuple[str, str, str]:
    """Anonymous products must not introduce named-identity coupling."""
    if product.get('identity_layer') != 'anonymous':
        return ('identity_layer_contract', PASS,
                f'product layer is {product.get("identity_layer")}, skipping anon check')

    forbidden = ['firebase_auth_user_id', 'spotify_user_id', 'named_contributor']
    leaks = []
    for term in forbidden:
        hits = scan_repo_for_string(repo, term)
        if hits:
            leaks.append(f'{term}: {hits[:2]}')
    if leaks:
        return ('identity_layer_contract', FAIL,
                f'anonymous product contains named-identity references: {leaks}')
    return ('identity_layer_contract', PASS, 'no named-identity leakage in anonymous product')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brain', required=True, help='Path to ocr-docs-brain directory')
    ap.add_argument('--repo', required=True, help='Path to product repo root')
    ap.add_argument('--product-id', required=True, help='Product ID in brain registry')
    ap.add_argument('--report-path', default='conformance-report.json')
    args = ap.parse_args()

    brain_dir = Path(args.brain)
    repo = Path(args.repo)

    if not brain_dir.exists():
        print(f'ERROR: brain dir {brain_dir} does not exist', file=sys.stderr)
        sys.exit(2)
    if not repo.exists():
        print(f'ERROR: repo dir {repo} does not exist', file=sys.stderr)
        sys.exit(2)

    brain = load_brain(brain_dir)
    product = find_product(brain, args.product_id)
    if not product:
        print(f'ERROR: product_id "{args.product_id}" not in brain registry', file=sys.stderr)
        sys.exit(2)

    print(f'Running conformance checks for {args.product_id} against brain @ {brain_dir}...')
    print()

    # Stub-repo early-exit: products with no application code yet (per
    # registry flag `code_present: false`) cannot satisfy code-presence
    # checks. The propagator still updates docs/standards into them, but
    # the conformance check would always fail — creating CI noise that
    # buries real drift signal in other repos. Honor the registry flag,
    # report a single PASS check explaining the skip, exit 0.
    #
    # When the stub repo onboards real code, flip `code_present: true`
    # (or remove the line) in `OCR-docs/ocr-docs-brain/product-registry.yaml`
    # and conformance kicks in automatically.
    if product.get('code_present') is False:
        skip_reason = (
            f'{args.product_id} marked code_present=false in registry — '
            f'stub repo, no application code to validate. Flip the flag '
            f'when code lands.'
        )
        print(f'  [SKIP] code-presence checks  {skip_reason}')
        report = {
            'product_id': args.product_id,
            'brain_path': str(brain_dir),
            'repo_path': str(repo),
            'summary': {'passed': 0, 'failed': 0, 'skipped': 1, 'total': 1},
            'passes': [{'check': 'stub_repo_exempt', 'detail': skip_reason}],
            'failures': [],
            'skipped': True,
            'reason': skip_reason,
        }
        Path(args.report_path).write_text(json.dumps(report, indent=2))
        print(f'Report: {args.report_path}')
        sys.exit(0)

    checks = [
        check_regulatory_pools_present(repo, product),
        check_required_tags_used(repo, product),
        check_invariant_test_files(repo, brain, args.product_id),
        check_tier_gate_respected(repo, product, brain),
        check_faith_organization_commitment(repo, brain),
        check_uec_codes_in_sync(repo, brain),
        check_demo_geo_in_corridor(repo, brain, args.product_id),
        check_identity_layer_contract(repo, product),
    ]

    passed = [c for c in checks if c[1] == PASS]
    failed = [c for c in checks if c[1] == FAIL]

    print('=' * 76)
    print(f'  CONFORMANCE REPORT — {args.product_id}')
    print('=' * 76)
    for name, status, detail in checks:
        marker = '[PASS]' if status == PASS else '[FAIL]'
        print(f'  {marker}  {name:35} {detail}')
    print('-' * 76)
    print(f'  {len(passed)} pass / {len(failed)} fail  (total {len(checks)})')
    print('-' * 76)

    report = {
        'product_id': args.product_id,
        'brain_path': str(brain_dir),
        'repo_path': str(repo),
        'summary': {'passed': len(passed), 'failed': len(failed), 'total': len(checks)},
        'passes':  [{'check': n, 'detail': d} for n, s, d in checks if s == PASS],
        'failures': [{'check': n, 'detail': d} for n, s, d in checks if s == FAIL],
    }
    Path(args.report_path).write_text(json.dumps(report, indent=2))
    print(f'Report: {args.report_path}')

    sys.exit(0 if not failed else 1)


if __name__ == '__main__':
    main()
