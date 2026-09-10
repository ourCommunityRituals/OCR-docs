#!/usr/bin/env python3
"""
test_check_cross_repo_imports.py — Born-red logic lock for
check_cross_repo_imports.py (Invariant #22 canonical gate).

Why this exists
===============
A gate earns trust only if it is first shown FAILING against a deliberately
broken fixture. Every prohibited pattern below gets its own born-red case
(expect exit 1), every permitted pattern its own born-green case (expect
exit 0), plus the fail-closed / not-applicable / born-ready / bad-args
contracts. `run_script_tests.py` auto-discovers this file (glob `test_*.py`)
and `brain-validate.yml` runs that on every PR touching ocr-docs-brain/** —
so these contracts execute in CI, not just locally.

Hermetic: builds a fixture brain + fixture repo in a tempdir and runs the
real guard as a subprocess. No network, no real repos.

Exit codes:
  0 — all contracts hold
  1 — at least one contract failed
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

GUARD = Path(__file__).resolve().parent.parent / 'scripts' / 'check_cross_repo_imports.py'

PATTERNS = {
    "enforcement_mode": "block",
    "permitted_scopes": ["@ocr/"],
    "permitted_local_specifiers": ["file:../packages/"],
    "docs_url": "https://example/docs",
    "scan_dirs": ["src", "workers"],
    "scan_extensions": [".ts", ".js", ".mjs"],
    "exclude_dir_names": ["node_modules", ".git"],
}
REGISTRY = {
    "products": [
        {"product_id": "ose", "repo": "OurCommunityRituals/ourSharedEvents",
         "npm_scope": "@oursharedevents", "repo_status": "active"},
        {"product_id": "wkrp", "repo": "OurCommunityRituals/ourWKRP",
         "npm_scope": "@ourwkrp", "repo_status": "active"},
        {"product_id": "osm", "repo": "OurCommunityRituals/ourSharedMagnets",
         "npm_scope": "@oursharedmagnets", "repo_status": "active"},
    ],
}
INVARIANTS = {"invariants": [{"id": 22, "applies_to": ["ose", "wkrp"]}]}


def make_brain(tmp: Path, mode: str = "block") -> Path:
    brain = tmp / "brain"
    (brain / "scripts").mkdir(parents=True)
    pat = dict(PATTERNS, enforcement_mode=mode)
    (brain / "scripts" / "cross_repo_patterns.json").write_text(
        json.dumps(pat), encoding="utf-8")
    # product-registry.yaml / architectural-invariants.yaml as JSON (valid YAML).
    (brain / "product-registry.yaml").write_text(
        json.dumps(REGISTRY), encoding="utf-8")
    (brain / "architectural-invariants.yaml").write_text(
        json.dumps(INVARIANTS), encoding="utf-8")
    return brain


def make_repo(tmp: Path, name: str, files: dict) -> Path:
    repo = tmp / name
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    repo.mkdir(exist_ok=True)
    return repo


def run_guard(repo: Path, product_id: str, brain: Path):
    proc = subprocess.run(
        [sys.executable, str(GUARD), "--repo", str(repo),
         "--product-id", product_id, "--brain", str(brain)],
        capture_output=True, text=True, timeout=60)
    return proc.returncode, proc.stdout + proc.stderr


# --- cases: (name, product_id, files, mode, expected_exit) -----------------
CASES = [
    # born-red (prohibited) — expect exit 1 under mode=block
    ("red: ES import of sibling scope", "ose",
     {"src/a.ts": "import { X } from '@ourwkrp/types';\n"}, "block", 1),
    ("red: require of sibling bare pkg", "ose",
     {"src/a.ts": "const x = require('ourwkrp/foo');\n"}, "block", 1),
    ("red: URL-specifier import", "ose",
     {"src/a.ts": "import x from 'https://ourwkrp.com/mod.js';\n"}, "block", 1),
    ("red: dynamic/computed import() fails closed", "ose",
     {"src/a.ts": "const p = pick(); await import(p);\n"}, "block", 1),
    ("red: package.json links sibling repo", "ose",
     {"src/a.ts": "export const x = 1;\n",
      "package.json": json.dumps(
          {"name": "oursharedevents",
           "dependencies": {"ourwkrp": "file:../../ourWKRP"}})}, "block", 1),
    ("red: tsconfig path resolves outside repo", "ose",
     {"src/a.ts": "export const x = 1;\n",
      "tsconfig.json": json.dumps(
          {"compilerOptions": {"baseUrl": ".",
           "paths": {"@wk/*": ["../ourWKRP/src/*"]}}})}, "block", 1),

    # born-green (permitted) — expect exit 0
    ("green: @ocr shared package import", "ose",
     {"src/a.ts": "import { serveCss } from '@ocr/ui';\n"}, "block", 0),
    ("green: file:../packages dep", "ose",
     {"src/a.ts": "export const x = 1;\n",
      "package.json": json.dumps(
          {"name": "oursharedevents",
           "dependencies": {"@ocr/ui": "file:../packages/ui"}})}, "block", 0),
    ("green: fetch() to sibling URL is not an import", "ose",
     {"src/a.ts": "await fetch('https://ourwkrp.com/api');\n"}, "block", 0),
    ("green: comment mentioning sibling product", "ose",
     {"src/a.ts": "// integrates with the ourWKRP product over HTTP\n"
                  "export const x = 1;\n"}, "block", 0),
    ("green: seam fetch to /api/events/:id/music", "ose",
     {"src/a.ts": "await fetch('https://ourwkrp.com/api/events/1/music');\n"},
     "block", 0),
    ("green: JSDoc prose saying 'import (' not flagged", "ose",
     {"src/a.ts": "/**\n * Read handlers. No router import (sanity — same "
                  "pattern).\n * Mentions @ourwkrp/types in prose only.\n */\n"
                  "export const x = 1;\n"}, "block", 0),
    ("green: // line comment with import() not flagged", "ose",
     {"src/a.ts": "// await import('@ourwkrp/types') — example in a comment\n"
                  "export const x = 1;\n"}, "block", 0),
    ("green: self-name package.json, clean deps", "wkrp",
     {"src/a.ts": "export const x = 1;\n",
      "package.json": json.dumps(
          {"name": "ourwkrp", "dependencies": {"zod": "^4.0.0"}})}, "block", 0),

    # warn mode downgrades a real violation to exit 0 (soft-launch / kill-switch)
    ("warn: violation reports but exits 0", "ose",
     {"src/a.ts": "import { X } from '@ourwkrp/types';\n"}, "warn", 0),

    # not-applicable product (osm not in applies_to) — exit 0
    ("n/a: product not in applies_to", "osm",
     {"src/a.ts": "import { X } from '@ourwkrp/types';\n"}, "block", 0),

    # born-ready: active product, NO source anywhere — exit 0
    ("born-ready: no source at all", "ose",
     {"docs/readme.md": "# docs only\n"}, "block", 0),

    # fail-closed: active product with .ts OUTSIDE scan dirs — exit 2
    ("fail-closed: source in unexpected dir", "ose",
     {"app/a.ts": "import { X } from '@ourwkrp/types';\n"}, "block", 2),
]


def main() -> int:
    passed = failed = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        brains = {"block": make_brain(tmp / "b", "block"),
                  "warn": make_brain(tmp / "w", "warn")}
        for idx, (name, pid, files, mode, want) in enumerate(CASES):
            repo = make_repo(tmp, f"repo{idx}", files)
            code, out = run_guard(repo, pid, brains[mode])
            ok = code == want
            if ok:
                passed += 1
            else:
                failed += 1
                print(f"  [FAIL] {name}: expected exit {want}, got {code}")
                print("    " + out.strip().replace("\n", "\n    "))

        # bad args (missing --repo) — exit 2
        proc = subprocess.run(
            [sys.executable, str(GUARD), "--product-id", "ose",
             "--brain", str(brains["block"])],
            capture_output=True, text=True)
        if proc.returncode == 2:
            passed += 1
        else:
            failed += 1
            print(f"  [FAIL] bad args: expected exit 2, got {proc.returncode}")

    print("-" * 76)
    print(f"  {passed} pass / {failed} fail  (total {passed + failed} contracts)")
    print("-" * 76)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
