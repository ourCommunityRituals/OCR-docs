#!/usr/bin/env python3
"""
scan_phantom_invariants.py — Pre-emptively catch invariant-number references
that don't exist in `architectural-invariants.yaml`.

Doctrine: ADR-003 Self-Checking Infrastructure, L1 conformance machinery.
The brain rule "numbers assigned at write time, never reserved" is enforced
here. Standards docs and READMEs MUST reference only invariants encoded in
the registry; ADRs are EXEMPT because proposals legitimately reference
future-encoded numbers under the "Invariant numbers are indicative" escape
hatch (see ADR-002 provenance).

Modes:
  --pre-commit          Scan staged files only (fast, for git pre-commit hook).
  --sweep               Scan all relevant files (manual invoke; default).
  --emit-report PATH    Write a JSON report at PATH in the shape consumed by
                        ocr-docs-brain/scripts/open_drift_ticket.py. Written
                        on every run regardless of pass/fail so it can be
                        uploaded as a CI artifact in both states.
  -h / --help           Print this help and exit.

Exit codes:
  0 — clean (or nothing to scan in pre-commit mode).
  1 — phantom references found.
  2 — tool error (registry missing, not in a git repo, bad arg).

Properties (per ADR-003 §"Four properties that make it durable forever"):
  Idempotent — same files in, same result out. No state.
  Honest — produces evidence with file:line:matched-text.
  Observable — failure output names the phantom and the registry.
  Fast — pure regex, no I/O beyond reading staged files. Sub-second.

Coordination:
  - OCR-53 will fold this scanner's logic into check_brain_contract.py so
    CI catches what pre-commit catches.
  - OCR-75 will install equivalent hooks in every product repo so vendored
    standards stay clean too.
  - L5 auto-drift Epic — when a phantom is caught in CI (not pre-commit),
    the auto-drift pipeline files a Linear ticket.
"""

import json
import re
import subprocess
import sys
from pathlib import Path


# ─── Pattern ──────────────────────────────────────────────────────────────────
# "invariant" / "Invariant" / "invariants" + optional # + digits.
# Excludes "12 invariants" (count form — digit precedes the word).
PHANTOM_PATTERNS = [
    re.compile(r"\b[Ii]nvariants?\s+#?\s*(\d+)\b"),
    re.compile(r"\binvariant_(\d+)\b"),
]


# ─── Skip lists ───────────────────────────────────────────────────────────────
# Files that legitimately reference unencoded invariants (proposals, history,
# the source of truth itself, this script's own pattern strings).
SKIP_BASENAMES = {
    "architectural-invariants.yaml",
    "scan_phantom_invariants.py",
    "CURRENT_STATE_INVENTORY.md",
    "INVARIANT_COMPLETION_DECISIONS.md",
    "NCR_BRAIN_PROMOTION_PROPOSAL.md",
}

# Directories that legitimately reference unencoded invariants (proposals).
SKIP_DIRS = {"adr"}

# Only files with these extensions are scanned at all.
SCAN_EXTENSIONS = {".md", ".yaml", ".yml"}


# ─── Helpers ──────────────────────────────────────────────────────────────────
def find_repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("scan_phantom_invariants: not in a git repo", file=sys.stderr)
        sys.exit(2)
    return Path(result.stdout.strip())


def load_registry_ids(repo_root: Path) -> set:
    """Extract invariant IDs from the YAML via regex — no PyYAML dependency.

    The registry's invariant entries are formatted as:
        - id: N
    at two-space indent under the `invariants:` key. The enrichment_history
    entries use `- invariant_id: N` (different key) and are not matched.
    """
    yaml_path = repo_root / "ocr-docs-brain" / "architectural-invariants.yaml"
    if not yaml_path.exists():
        print(
            f"scan_phantom_invariants: registry not found at {yaml_path}",
            file=sys.stderr,
        )
        sys.exit(2)
    pat = re.compile(r"^  - id:\s+(\d+)\s*$", re.MULTILINE)
    text = yaml_path.read_text(encoding="utf-8")
    return {int(m.group(1)) for m in pat.finditer(text)}


def should_scan(rel_path: Path) -> bool:
    if rel_path.name in SKIP_BASENAMES:
        return False
    if rel_path.suffix not in SCAN_EXTENSIONS:
        return False
    for part in rel_path.parts:
        if part in SKIP_DIRS:
            return False
    return True


def staged_files(repo_root: Path) -> list:
    """Files staged for the current commit (Added/Copied/Modified/Renamed/Type-changed)."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT"],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
        check=False,
    )
    if result.returncode != 0:
        return []
    return [Path(line) for line in result.stdout.strip().splitlines() if line]


def all_relevant_files(repo_root: Path) -> list:
    paths = []
    for sub in ("docs", "ocr-docs-brain", "."):
        base = repo_root / sub
        if not base.exists():
            continue
        for ext in SCAN_EXTENSIONS:
            for p in base.rglob(f"*{ext}"):
                try:
                    paths.append(p.relative_to(repo_root))
                except ValueError:
                    continue
    # Dedupe (the "." sub-search overlaps with "docs" and "ocr-docs-brain").
    return sorted(set(paths))


def scan_file(abs_path: Path, legal_ids: set) -> list:
    """Return list of (line_number, line_text, claimed_id) for phantoms."""
    if not abs_path.exists() or not abs_path.is_file():
        return []
    try:
        text = abs_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    findings = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pat in PHANTOM_PATTERNS:
            for m in pat.finditer(line):
                n = int(m.group(1))
                if n not in legal_ids:
                    findings.append((lineno, line.strip(), n))
    return findings


# ─── Report emission ──────────────────────────────────────────────────────────
def build_report(findings_by_file: dict, legal_ids: set, files_checked: int,
                 mode: str) -> dict:
    """Build a report dict in the shape open_drift_ticket.py consumes.

    product_id="brain" routes the ticket to OCR-doc team via the helper's
    TEAM_ROUTING table. Each phantom finding becomes one entry in `failures`
    with check="phantom_invariant_reference".
    """
    failures = []
    for rel, findings in findings_by_file.items():
        for lineno, _text, n in findings:
            # Use forward slashes in the detail string so reports are stable
            # across Windows/Linux runners (Path uses backslash on Windows).
            rel_str = str(rel).replace("\\", "/")
            failures.append({
                "check": "phantom_invariant_reference",
                "detail": (
                    f"{rel_str}:{lineno}: claims invariant #{n} "
                    "(not in registry)"
                ),
            })

    if failures:
        summary = {"failed": len(failures), "passed": 0, "total": len(failures)}
        passes = []
    else:
        summary = {"failed": 0, "passed": 1, "total": 1}
        passes = [{
            "check": "phantom_invariant_reference",
            "detail": (
                f"Scanned {files_checked} files; all references resolve to "
                f"the {len(legal_ids)} invariants in the registry."
            ),
        }]

    return {
        "product_id": "brain",
        "scanner": "scan_phantom_invariants.py",
        "scanner_mode": mode,
        "registry_invariant_count": len(legal_ids),
        "registry_invariant_ids": sorted(legal_ids),
        "files_scanned": files_checked,
        "summary": summary,
        "failures": failures,
        "passes": passes,
    }


def write_report(path: str, report: dict) -> None:
    """Write the JSON report to `path`. Path is created if missing."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


# ─── Main ─────────────────────────────────────────────────────────────────────
def parse_args(argv: list) -> tuple:
    """Returns (mode, emit_report_path, error_message_or_None)."""
    mode = "sweep"
    emit_report = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--pre-commit":
            mode = "pre-commit"
        elif arg == "--sweep":
            mode = "sweep"
        elif arg == "--emit-report":
            i += 1
            if i >= len(argv):
                return mode, emit_report, "--emit-report requires a path argument"
            emit_report = argv[i]
        elif arg.startswith("--emit-report="):
            emit_report = arg.split("=", 1)[1]
        elif arg in ("-h", "--help"):
            return "help", None, None
        else:
            return mode, emit_report, f"unknown argument {arg!r}"
        i += 1
    return mode, emit_report, None


def main() -> int:
    mode, emit_report_path, err = parse_args(sys.argv[1:])
    if err:
        print(f"scan_phantom_invariants: {err}", file=sys.stderr)
        return 2
    if mode == "help":
        print(__doc__)
        return 0

    repo_root = find_repo_root()
    legal_ids = load_registry_ids(repo_root)

    if mode == "pre-commit":
        rel_paths = staged_files(repo_root)
    else:
        rel_paths = all_relevant_files(repo_root)

    findings_by_file = {}
    files_checked = 0
    for rel in rel_paths:
        if not should_scan(rel):
            continue
        files_checked += 1
        abs_path = repo_root / rel
        findings = scan_file(abs_path, legal_ids)
        if findings:
            findings_by_file[rel] = findings

    # Emit the JSON report (if requested) on every run — pass or fail. The
    # helper open_drift_ticket.py reads failures[] and no-ops on empty.
    # Uploaded as a CI artifact for both states so post-mortem queries work.
    if emit_report_path:
        report = build_report(findings_by_file, legal_ids, files_checked, mode)
        try:
            write_report(emit_report_path, report)
        except OSError as e:
            print(
                f"scan_phantom_invariants: could not write report to "
                f"{emit_report_path}: {e}",
                file=sys.stderr,
            )
            return 2

    if not findings_by_file:
        if mode == "sweep":
            print(
                "OK scan_phantom_invariants: clean. "
                f"Registry contains {len(legal_ids)} invariants: "
                f"{sorted(legal_ids)}. "
                f"Scanned {files_checked} files."
            )
        return 0

    print("", file=sys.stderr)
    print(
        "FAIL scan_phantom_invariants: phantom invariant reference(s) found.",
        file=sys.stderr,
    )
    print("", file=sys.stderr)
    print(
        f"  Registry contains {len(legal_ids)} invariants: {sorted(legal_ids)}",
        file=sys.stderr,
    )
    print("", file=sys.stderr)

    total = 0
    for rel, findings in findings_by_file.items():
        for lineno, text, n in findings:
            print(
                f"  {rel}:{lineno}: claims invariant #{n} "
                "(not in registry)",
                file=sys.stderr,
            )
            print(f"      {text}", file=sys.stderr)
            total += 1

    print("", file=sys.stderr)
    print(
        f"  {total} phantom reference(s) across "
        f"{len(findings_by_file)} file(s).",
        file=sys.stderr,
    )
    print("", file=sys.stderr)
    print(
        "  Kill switch:  git commit --no-verify  "
        "(doctrine: ADR-003, use sparingly)",
        file=sys.stderr,
    )
    print(
        "  Sibling: OCR-53 (Linear) will wire this into the brain "
        "conformance check.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
