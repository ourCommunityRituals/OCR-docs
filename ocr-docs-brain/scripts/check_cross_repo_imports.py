#!/usr/bin/env python3
"""
check_cross_repo_imports.py — Canonical gate for Invariant #22
(Cross-Repo Import Isolation), brain-resident and repo-agnostic.

Why this exists
===============
Invariant #22 forbids module-level coupling across the OSE / WKRP / OAW (and
the other product) repo boundaries. The anonymous pole (OSE) and the named
pole (WKRP) carry opposite identity invariants; a module import across the
boundary would couple the two identity models in code, bypassing the one
documented HTTP seam (GET /api/events/:id/music) and its CORS controls.

IMPORTANT — this is NECESSARY BUT NOT SUFFICIENT. It blocks *module imports*.
It does NOT prove the HTTP seam's payload is clean (that is a separate
control). Do not read a green run here as "the identity firewall is closed."

Single source, no per-repo copies
==================================
Before this script, the gate lived only in ourSharedEvents/scripts/
check-cross-repo-imports.sh (bash, scanned `workers/` only, OSE-perspective
scopes hardcoded). Copying it per repo IS the drift pattern. This canonical
version is invoked from each product repo's CI against its own checkout:

    python check_cross_repo_imports.py --repo <path> --product-id <id> \
        --brain <ocr-docs-brain path>

- Prohibited sibling scopes/dirs are DERIVED from product-registry.yaml
  (npm_scope + repo), so adding a product updates enforcement everywhere.
- The enforcement MODE and permitted allowlist come from
  scripts/cross_repo_patterns.json (read live from main).

Detection is a TRIPWIRE, not a proof (v1): it resolves literal specifiers,
tsconfig `paths`, and package.json dependency links, and FAILS CLOSED on
dynamic/computed import()/require(). Full TS module-graph resolution is a
documented v2.

Exit codes:
  0 — no violations (or product not in applies_to, or mode=warn)
  1 — violation(s) found and enforcement_mode == block
  2 — usage / configuration error (missing repo, bad registry, fail-closed
      source discovery for an active product with no source root)
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

try:
    import yaml
except ImportError:
    print('FATAL: pyyaml not available (pip install pyyaml)', file=sys.stderr)
    sys.exit(2)

INVARIANT_ID = 22
# repo_status values that mean "this repo has (or should have) code now".
ACTIVE_STATUSES = {'active', 'pre-tech'}


# ---------------------------------------------------------------------------
# Brain data
# ---------------------------------------------------------------------------
def load_patterns(brain: Path) -> dict:
    f = brain / 'scripts' / 'cross_repo_patterns.json'
    return json.loads(f.read_text(encoding='utf-8'))


def load_registry(brain: Path) -> dict:
    f = brain / 'product-registry.yaml'
    return yaml.safe_load(f.read_text(encoding='utf-8'))


def invariant_applies(brain: Path, product_id: str) -> bool:
    """True if product_id is in invariant #22's applies_to list.

    `invariants` is a flat list of invariant dicts at the brain's top level
    (verified against architectural-invariants.yaml). If #22 cannot be found
    we fail SAFE (assume it applies) rather than silently skip the gate.
    """
    data = yaml.safe_load(
        (brain / 'architectural-invariants.yaml').read_text(encoding='utf-8'))
    invs = data.get('invariants', []) if isinstance(data, dict) else []
    if isinstance(invs, dict):                      # tolerate a nested shape
        invs = invs.get('invariants', [])
    for inv in invs:
        if isinstance(inv, dict) and inv.get('id') == INVARIANT_ID:
            return product_id in (inv.get('applies_to') or [])
    return True


def sibling_index(registry: dict):
    """Return (scopes, dirs) of ALL product repos — the prohibited set.

    Importing any product scope (including one's own) is prohibited: a repo
    uses relative imports internally, never its published package. @ocr/* is
    handled by the permitted allowlist, not here.
    """
    scopes, dirs = set(), set()
    for p in registry.get('products', []):
        scope = p.get('npm_scope')
        if scope:
            scopes.add(scope.rstrip('/') + '/')
        repo = p.get('repo')
        if repo:
            dirs.add(str(repo).split('/')[-1])
    return scopes, dirs


def product_status(registry: dict, product_id: str) -> str:
    for p in registry.get('products', []):
        if p.get('product_id') == product_id:
            return p.get('repo_status', 'unknown')
    return 'unknown'


# ---------------------------------------------------------------------------
# Source discovery (fail-closed)
# ---------------------------------------------------------------------------
def _walk_sources(roots, exts, excludes):
    """os.walk with in-place dir pruning (never descend into excluded dirs —
    node_modules/.stryker-tmp etc.) and OS-error tolerance (broken symlinks,
    long paths on Windows would otherwise crash an rglob)."""
    import os
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
            dirnames[:] = [d for d in dirnames if d not in excludes]
            for fn in filenames:
                if Path(fn).suffix in exts:
                    yield Path(dirpath) / fn


def iter_source_files(repo: Path, patterns: dict):
    scan_dirs = patterns.get('scan_dirs', ['src', 'workers'])
    exts = set(patterns.get('scan_extensions', ['.ts', '.js', '.mjs']))
    excludes = set(patterns.get('exclude_dir_names', ['node_modules', '.git']))
    roots = [repo / d for d in scan_dirs if (repo / d).is_dir()]
    yield from _walk_sources(roots, exts, excludes)


def has_any_source(repo: Path, patterns: dict) -> bool:
    """True if ANY .ts/.js exists anywhere (outside excludes) — used for the
    fail-closed check so code in an unexpected dir can't escape the gate."""
    exts = set(patterns.get('scan_extensions', ['.ts', '.js', '.mjs']))
    excludes = set(patterns.get('exclude_dir_names', ['node_modules', '.git']))
    for _ in _walk_sources([repo], exts, excludes):
        return True
    return False


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------
def strip_comments(lines):
    """Yield (line_no, code) with // line-comments and /* */ block comments
    removed, so prose like a JSDoc "... import (sanity)" can't trip the
    detectors. Heuristic (not a full tokenizer): protects '://' so URL import
    specifiers survive for the url-import check. Good enough for a tripwire;
    full tokenization is the documented v2."""
    in_block = False
    for i, line in enumerate(lines, 1):
        out, j, n = [], 0, len(line)
        while j < n:
            if in_block:
                end = line.find('*/', j)
                if end == -1:
                    j = n
                else:
                    j, in_block = end + 2, False
                continue
            if line.startswith('/*', j):
                in_block = True
                j += 2
                continue
            if line.startswith('//', j) and not (j > 0 and line[j - 1] == ':'):
                break  # rest of line is a // comment (but not part of '://')
            out.append(line[j])
            j += 1
        yield i, ''.join(out)


class Violation:
    def __init__(self, path, line_no, kind, snippet, hint):
        self.path, self.line_no, self.kind = path, line_no, kind
        self.snippet, self.hint = snippet.strip(), hint

    def render(self, docs_url):
        return (f'  VIOLATION [{self.kind}] {self.path}:{self.line_no}\n'
                f'    {self.snippet}\n'
                f'    → {self.hint}\n'
                f'    permitted: @ocr/* packages + the HTTP seam '
                f'GET /api/events/:id/music. See {docs_url}')


def scan_source_line(path, i, line, scopes, hosts):
    """Yield Violations for one source line. Tripwire-grade (regex)."""
    out = []
    # 1) ES import / export-from a prohibited product scope (incl. bare pkg name)
    for scope in scopes:
        name = scope[1:].rstrip('/') if scope.startswith('@') else scope.rstrip('/')
        # from '@ourwkrp/...'  |  from 'ourwkrp/...'  |  require('@ourwkrp/...')
        pat = re.compile(
            r"""(?:from|require\(|import\()\s*['"]"""
            + r'(?:' + re.escape(scope) + r'|' + re.escape(name) + r'/)')
        if pat.search(line):
            out.append(Violation(path, i, 'module-import', line,
                                  f"imports sibling product scope '{scope}'"))
    # 2) import from a sibling-repo URL specifier (anchored to a scheme —
    #    avoids the bash version's greedy false-positive on comments)
    for host in hosts:
        if re.search(r"""(?:from|import\(|require\()\s*['"]https?://[^'"]*"""
                     + re.escape(host), line):
            out.append(Violation(path, i, 'url-import', line,
                                  f"module import from sibling URL host '{host}'"))
    # 3) FAIL CLOSED on dynamic / computed import()/require() (non string-literal)
    for m in re.finditer(r'(?<![\w.])(?:import|require)\s*\(', line):
        rest = line[m.end():].lstrip()
        if not rest[:1] in ('"', "'", '`'):
            out.append(Violation(path, i, 'dynamic-specifier', line,
                                  'non-literal import()/require() — cannot be '
                                  'statically verified; resolve to a literal or '
                                  'justify (fails closed under Invariant #22)'))
    return out


def check_tsconfig_paths(repo: Path):
    """Flag tsconfig `paths` entries that resolve outside the repo root."""
    out = []
    for tsc in list(repo.glob('tsconfig*.json')):
        try:
            # tsconfig allows comments/trailing commas; strip the common cases.
            raw = tsc.read_text(encoding='utf-8')
            raw = re.sub(r'//[^\n]*', '', raw)
            raw = re.sub(r'/\*.*?\*/', '', raw, flags=re.S)
            raw = re.sub(r',(\s*[}\]])', r'\1', raw)
            cfg = json.loads(raw)
        except Exception:
            continue
        paths = (cfg.get('compilerOptions') or {}).get('paths') or {}
        base = (cfg.get('compilerOptions') or {}).get('baseUrl', '.')
        for alias, targets in paths.items():
            for t in targets:
                resolved = (repo / base / t).resolve()
                try:
                    resolved.relative_to(repo.resolve())
                except ValueError:
                    # resolves outside the repo — allowed only into packages/
                    if 'packages' not in resolved.parts:
                        out.append(Violation(
                            tsc.relative_to(repo), 0, 'tsconfig-path',
                            f'"{alias}": "{t}"',
                            'tsconfig path alias resolves outside the repo root '
                            '(cross-repo coupling via alias)'))
    return out


def check_package_json(repo: Path, sibling_dirs):
    """Inspect ALL dependency-bearing keys; flag file:/link:/workspace: deps
    that resolve into a sibling product-repo dir. Never flag the repo's own
    name or file:../packages/*."""
    out = []
    pkg = repo / 'package.json'
    if not pkg.is_file():
        return out
    try:
        data = json.loads(pkg.read_text(encoding='utf-8'))
    except Exception:
        return out
    dep_keys = ['dependencies', 'devDependencies', 'peerDependencies',
                'optionalDependencies', 'bundledDependencies', 'bundleDependencies',
                'resolutions', 'overrides']
    blocks = [data.get(k) or {} for k in dep_keys]
    if isinstance(data.get('pnpm'), dict):
        blocks.append(data['pnpm'].get('overrides') or {})
    for block in blocks:
        if not isinstance(block, dict):
            continue
        for name, spec in block.items():
            if not isinstance(spec, str):
                continue
            m = re.match(r'(?:file|link|workspace|portal):(.+)', spec)
            if not m:
                continue
            target = m.group(1).lstrip('/')
            if target.startswith('../packages') or '/packages/' in target \
                    or target.startswith('packages'):
                continue  # permitted shared workspace
            resolved = (repo / m.group(1)).resolve()
            if any(d in resolved.parts for d in sibling_dirs if d != repo.name):
                out.append(Violation(
                    Path('package.json'), 0, 'package-dep',
                    f'"{name}": "{spec}"',
                    'dependency links a sibling product repo'))
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def run(repo: Path, product_id: str, brain: Path):
    patterns = load_patterns(brain)
    registry = load_registry(brain)
    docs_url = patterns.get('docs_url', '(see brain docs)')
    mode = patterns.get('enforcement_mode', 'block')

    if not invariant_applies(brain, product_id):
        print(f'Invariant #{INVARIANT_ID}: product "{product_id}" not in '
              f'applies_to — nothing to enforce. PASS.')
        return 0

    scopes, sibling_dirs = sibling_index(registry)
    # URL hosts = <dir>.com for product dirs (e.g. ourwkrp.com).
    hosts = {d.lower() + '.com' for d in sibling_dirs}

    print(f'=== Invariant #{INVARIANT_ID} Cross-Repo Import Isolation '
          f'(product={product_id}, mode={mode}) ===')

    source = list(iter_source_files(repo, patterns))
    status = product_status(registry, product_id)
    if not source:
        if status in ACTIVE_STATUSES and has_any_source(repo, patterns):
            print(f'FAIL (config): product "{product_id}" is {status} and has '
                  f'.ts/.js outside the expected scan dirs '
                  f'{patterns.get("scan_dirs")}. Refusing to pass vacuously.',
                  file=sys.stderr)
            return 2
        print(f'No source under {patterns.get("scan_dirs")} — born-ready PASS '
              f'(status={status}). Gate activates when source lands.')
        return 0

    violations = []
    for f in source:
        rel = f.relative_to(repo)
        try:
            lines = f.read_text(encoding='utf-8', errors='replace').splitlines()
        except Exception:
            continue
        for i, code in strip_comments(lines):
            violations.extend(scan_source_line(rel, i, code, scopes, hosts))
    violations.extend(check_tsconfig_paths(repo))
    violations.extend(check_package_json(repo, sibling_dirs))

    if not violations:
        print(f'PASS — scanned {len(source)} source file(s); no cross-repo '
              f'module coupling. (Tripwire-grade; full graph resolution is v2.)')
        return 0

    print(f'\n{len(violations)} cross-repo isolation violation(s):\n')
    for v in violations:
        print(v.render(docs_url))
    print(f'\nInvariant #{INVARIANT_ID} prohibits module-level imports across '
          f'product repos. The only permitted cross-repo data flow is the HTTP '
          f'seam. enforcement_mode={mode}.')
    if mode == 'block':
        return 1
    print('enforcement_mode=warn — reporting only, not failing. '
          '*** FLEET SIGNAL: Invariant #22 is running in WARN mode. ***')
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description='Invariant #22 cross-repo import gate')
    ap.add_argument('--repo', required=True, help='product repo checkout root')
    ap.add_argument('--product-id', required=True, help='brain product_id (ose, wkrp, …)')
    ap.add_argument('--brain', required=True, help='path to ocr-docs-brain')
    args = ap.parse_args(argv)

    repo, brain = Path(args.repo), Path(args.brain)
    if not repo.is_dir():
        print(f'FATAL: --repo {repo} is not a directory', file=sys.stderr)
        return 2
    if not (brain / 'product-registry.yaml').is_file():
        print(f'FATAL: --brain {brain} has no product-registry.yaml', file=sys.stderr)
        return 2
    try:
        return run(repo, args.product_id, brain)
    except Exception as e:  # configuration / parse errors fail closed
        print(f'FATAL: {type(e).__name__}: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
