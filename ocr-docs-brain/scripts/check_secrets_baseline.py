#!/usr/bin/env python3
"""
check_secrets_baseline.py — OCR-130 committed-secret gate for the brain.

Why this exists
===============
OCR-docs is a docs hub that propagates ×~8 to every spoke, so a leaked
credential multiplies across the org. `.gitignore` is only *name-based*
defense-in-depth and is porous — on 2026-09-03 an untracked
`docs/! gh secret set CF_ACCESS_CLIENT_ID --re.txt` was found by eye, not by a
gate. `OCR_STANDARD_reconciliationLoop` §8 rule 4 declares a **content
scanner** the authoritative gate; this makes that true rather than aspirational.

It is a straight port of OSE's OSE-911 gate (`scripts/check-secrets-baseline.py`)
so the org standardizes on one scanner (detect-secrets, pure-Python — no WASM
JIT, unlike gitleaks which panicked nondeterministically on the old Windows
runners). Behavior:

  1. Run `detect-secrets scan` over the working tree.
  2. Compare the set of (file, hashed_secret) pairs against the committed
     `.secrets.baseline`. Only a *new* secret — one not already accepted in the
     baseline — fails the gate. Line-number churn on an already-known secret
     does NOT fail it (we key on hashed_secret, not location), so it is not flaky.

A real credential value therefore fails brain CI **regardless of filename or
extension** — the property `.gitignore` could never give.

To accept a genuinely-new-but-false-positive detection, re-baseline:

    python -m detect_secrets scan --exclude-files '\\.secrets\\.baseline' \
      > .secrets.baseline

and commit the updated `.secrets.baseline` (review the diff first — never
baseline a value that is actually a live credential; rotate it instead).
"""
import json
import os
import subprocess
import sys

BASELINE = os.environ.get("SECRETS_BASELINE", ".secrets.baseline")

# Kept in lockstep with the re-baseline command in this module's docstring.
# OCR-docs is docs-only, so the sole exclude is the baseline file itself (a
# baseline necessarily contains hashed_secret values that would otherwise be
# re-flagged). Everything else — including tests/ — is scanned: a real secret
# pasted into a test file must still fail, while the known test fakes live in
# the committed baseline.
EXCLUDES = [
    r"\.secrets\.baseline",
]


def pairs(doc):
    """Set of (normalized-path, hashed_secret) for every detection in a baseline doc.

    Paths are normalized to forward slashes so a baseline written on Windows
    matches a scan run on Linux CI.
    """
    return {
        (f.replace("\\", "/"), entry["hashed_secret"])
        for f, entries in doc.get("results", {}).items()
        for entry in entries
    }


def _emit_summary(line):
    print(line)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        try:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            pass


def main():
    if not os.path.exists(BASELINE):
        print(f"::error::secret baseline not found at {BASELINE}", file=sys.stderr)
        return 1

    cmd = [sys.executable, "-m", "detect_secrets", "scan"]
    for pattern in EXCLUDES:
        cmd += ["--exclude-files", pattern]
    scan = subprocess.run(cmd, capture_output=True, text=True)
    if scan.returncode != 0:
        # A scanner crash is infra, not a clean pass — fail closed and say so.
        print(
            f"::error::detect-secrets scan failed (exit {scan.returncode}): "
            f"{scan.stderr.strip()[:500]}",
            file=sys.stderr,
        )
        return 1

    current = json.loads(scan.stdout)
    with open(BASELINE, encoding="utf-8") as fh:
        baseline = json.load(fh)

    new = pairs(current) - pairs(baseline)
    total = sum(len(v) for v in current.get("results", {}).values())
    _emit_summary(
        f"- **detect-secrets:** {total} known detections, "
        f"{len(new)} NEW vs baseline"
    )

    if new:
        print(
            f"::error::detect-secrets found secret(s) not present in {BASELINE}:"
        )
        for path, hashed in sorted(new):
            print(f"  NEW  {path}  ({hashed})")
        print(
            "If these are false positives, re-baseline per the header of "
            "ocr-docs-brain/scripts/check_secrets_baseline.py and commit "
            ".secrets.baseline. If a value is a REAL credential, remove and "
            "rotate it - never baseline it."
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
