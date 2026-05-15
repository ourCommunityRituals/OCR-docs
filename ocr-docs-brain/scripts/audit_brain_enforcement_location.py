#!/usr/bin/env python3
"""
audit_brain_enforcement_location.py — enforce architectural invariant 13.

Scans a set of repository working trees (the workspace root and each
application repo listed in product-registry.yaml) for filenames that
look like Brain enforcement code living outside the allowed home
(OCR-docs/ocr-docs-brain/scripts/ or OCR-docs/ocr-docs-brain/tests/).

Detection is filename-pattern based. The boundary test in the standard
doc (`OCR_STANDARD_brainEnforcementLocation.md`) is semantic, but for
v1 we trust the convention that enforcement scripts are named with one
of the recognizable patterns below. Adding a new enforcement script
with a non-conforming filename outside OCR-docs would slip past this
audit — that's intentional and acceptable as long as the bulk of
real-world drift follows the patterns.

Exit codes:
  0 — no misplaced files (or only exempted ones).
  1 — at least one misplaced file detected. Report written to --report-path.
  2 — execution error (registry unreadable, paths missing, etc.).

Usage:
  python3 audit_brain_enforcement_location.py \\
    --brain <path-to-ocr-docs-brain> \\
    --workspace-root <path-to-ourCommunityRituals-clone-or-empty> \\
    --app-repos-root <path-to-dir-containing-app-repo-clones-or-empty> \\
    --report-path audit-report.json

If --workspace-root or --app-repos-root point at a non-existent path or
empty string, that target is silently skipped (so the workflow can run
even when one of the clones fails to set up).

Invoked from .github/workflows/brain-location-audit.yml on a nightly
schedule and on PRs touching ocr-docs-brain/ or docs/standards/.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


# ─── Detection patterns ────────────────────────────────────────────────────
#
# A filename matching any of these patterns is treated as Brain
# enforcement code. The list is conservative — false positives are
# easier to triage (add an exception) than false negatives (silent
# drift). If the audit starts producing noise on a legitimate consumer
# file, add an exception entry to invariant 13's `exceptions:` list
# rather than weakening the patterns.

FORBIDDEN_FILENAME_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^check_.*contract.*\.py$"),
    re.compile(r"^.*brain_contract.*\.py$"),
    re.compile(r"^.*drift_ticket.*\.py$"),
    re.compile(r"^audit_brain_.*\.py$"),
    re.compile(r"^validate_brain_.*\.py$"),
]
# NOTE: deliberately NOT including `level\d+_.*\.py` here. Application
# repos run their own 10-level test pyramid (security / lint / unit /
# regression / boundary / integration / contract / pact / academic) under
# this naming convention, and packages in the workspace root do the same.
# Those are legitimate app-level tests, not Brain enforcement. The
# explicit `*_contract*.py`, `*brain*.py`, `*drift_ticket*.py`,
# `audit_brain_*.py`, `validate_brain_*.py` patterns above are
# sufficient to catch the real failure mode (governance code drifting
# into a non-governance repo).

# Directories under the audit target that we never descend into. Cuts
# scanning cost and avoids false positives from node_modules vendor code.
SKIP_DIR_NAMES: set[str] = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".cache",
    ".venv",
    "__pycache__",
    "actions-runner",  # self-hosted runner work tree — vendored copies
    "_work",
}


def is_forbidden_filename(name: str) -> bool:
    return any(p.match(name) for p in FORBIDDEN_FILENAME_PATTERNS)


def walk_filtered(root: Path) -> Iterable[Path]:
    """Recursive walk that skips known noise directories."""
    if not root.exists():
        return
    stack: list[Path] = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except (PermissionError, FileNotFoundError, OSError):
            continue
        for entry in entries:
            if entry.is_dir():
                if entry.name in SKIP_DIR_NAMES:
                    continue
                stack.append(entry)
            elif entry.is_file():
                yield entry


def load_exceptions(brain_dir: Path) -> set[str]:
    """Return the set of exception entries from invariant 13.

    Exceptions are matched on basename only (a documented-and-approved
    file with a forbidden-looking name).
    """
    inv_path = brain_dir / "architectural-invariants.yaml"
    if not inv_path.exists():
        return set()
    try:
        data = yaml.safe_load(inv_path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError):
        return set()
    if not isinstance(data, list):
        return set()
    for entry in data:
        if not isinstance(entry, dict):
            continue
        if entry.get("id") != 13:
            continue
        exc = entry.get("exceptions") or []
        if isinstance(exc, list):
            return {str(x) for x in exc}
    return set()


def load_app_repo_dirs(brain_dir: Path, app_repos_root: Path | None) -> list[Path]:
    """Read product-registry.yaml, return clone paths under app_repos_root.

    If app_repos_root is missing, returns an empty list (target skipped).
    Each product's `repo:` field is `OurCommunityRituals/<repo>`; we
    expect a clone at `<app_repos_root>/<repo>`.
    """
    if not app_repos_root or not app_repos_root.exists():
        return []
    registry_path = brain_dir / "product-registry.yaml"
    if not registry_path.exists():
        return []
    try:
        data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, UnicodeDecodeError):
        return []
    if not isinstance(data, dict):
        return []
    products = data.get("products") or []
    out: list[Path] = []
    for p in products:
        if not isinstance(p, dict):
            continue
        repo_field = p.get("repo")
        if not isinstance(repo_field, str) or "/" not in repo_field:
            continue
        repo_name = repo_field.split("/", 1)[1]
        candidate = app_repos_root / repo_name
        if candidate.exists():
            out.append(candidate)
    return out


def scan_target(target_label: str, target_root: Path, exceptions: set[str]) -> list[dict]:
    """Return a list of violation records for files under target_root."""
    if not target_root.exists():
        return []
    violations: list[dict] = []
    for path in walk_filtered(target_root):
        if not is_forbidden_filename(path.name):
            continue
        if path.name in exceptions:
            continue
        violations.append(
            {
                "target": target_label,
                "path": str(path.relative_to(target_root)).replace("\\", "/"),
                "absolute_path": str(path),
                "matched_pattern_class": "brain_enforcement_filename",
                "remediation": (
                    "Move this file to OCR-docs/ocr-docs-brain/scripts/ or "
                    "OCR-docs/ocr-docs-brain/tests/. If it must live here, add the "
                    "basename to invariant 13's `exceptions:` list in "
                    "ocr-docs-brain/architectural-invariants.yaml with a comment "
                    "explaining why."
                ),
            }
        )
    return violations


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--brain", required=True, type=Path, help="Path to OCR-docs/ocr-docs-brain"
    )
    ap.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Path to a ourCommunityRituals workspace-root clone (optional)",
    )
    ap.add_argument(
        "--app-repos-root",
        type=Path,
        default=None,
        help="Path to a directory containing app-repo clones, named by repo (optional)",
    )
    ap.add_argument(
        "--report-path",
        type=Path,
        required=True,
        help="Where to write the JSON violation report",
    )
    args = ap.parse_args()

    if not args.brain.exists():
        print(f"ERROR: brain path does not exist: {args.brain}", file=sys.stderr)
        return 2

    exceptions = load_exceptions(args.brain)
    targets: list[tuple[str, Path]] = []

    if args.workspace_root and args.workspace_root.exists():
        targets.append(("workspace-root", args.workspace_root))
    if args.app_repos_root and args.app_repos_root.exists():
        for app_dir in load_app_repo_dirs(args.brain, args.app_repos_root):
            targets.append((f"app-repo:{app_dir.name}", app_dir))

    all_violations: list[dict] = []
    for label, root in targets:
        all_violations.extend(scan_target(label, root, exceptions))

    report = {
        "schema_version": 1,
        "invariant_id": 13,
        "exceptions_loaded": sorted(exceptions),
        "targets_scanned": [{"label": l, "path": str(p)} for l, p in targets],
        "violation_count": len(all_violations),
        "violations": all_violations,
    }
    args.report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if all_violations:
        print(
            f"[FAIL] {len(all_violations)} misplaced Brain-enforcement file(s) detected:",
            file=sys.stderr,
        )
        for v in all_violations[:20]:
            print(f"  - {v['target']}: {v['path']}", file=sys.stderr)
        if len(all_violations) > 20:
            print(f"  ... and {len(all_violations) - 20} more", file=sys.stderr)
        print(f"Full report: {args.report_path}", file=sys.stderr)
        return 1

    print(
        f"[OK] No misplaced Brain-enforcement files found across "
        f"{len(targets)} target(s). Report: {args.report_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
