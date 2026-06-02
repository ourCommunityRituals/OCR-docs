# OCR-docs Git Hooks

Regression-tolerant infrastructure triggers for OCR-docs.

Doctrine: [ADR-003 Self-Checking Infrastructure](../../docs/adr/ADR-003-self-checking-infrastructure.md).

---

## Install

```bash
bash ocr-docs-brain/hooks/install.sh
```

Sets `git config core.hooksPath` to this directory. Idempotent — safe to run
many times.

The hooks themselves live in git, version-controlled like everything else in
the brain. New clones inherit the hook *files*; running the install script
once per clone makes them *active*.

---

## What's installed

### `pre-commit`

Runs `scan_phantom_invariants.py --pre-commit` against the files in your
current commit. Fails the commit if any `invariant #N` reference points at
an N not present in `architectural-invariants.yaml`.

**What it catches:**

- A new standards doc claiming an invariant number not in the registry.
- An edit to `OCR_VISION.md` introducing a fresh phantom reference.
- A vendored `.ocr-standards/` copy gone stale (when run in a product repo
  via OCR-75's per-product hook installation).

**What it does NOT catch:**

- Conformance drift between code and registry — that's
  `check_brain_contract.py` running in CI.
- Wrong-direction renumbering — separate audit.
- Anything outside the OCR-docs repo — per-product hooks land via OCR-75.

**ADRs are exempt.** Files under `docs/adr/` may legitimately reference
future-encoded numbers under the "Invariant numbers are indicative —
assigned at implementation per the brain's write-time numbering rule" escape
hatch (see ADR-002 provenance). Proposals need to name their proposed
numbers; the rule keeps standards (and only standards) from claiming numbers
that don't exist.

Runs in under a second on the staged file set. The full `--sweep` mode
(manual invoke) runs in under three seconds on the whole repo.

---

## Verify it's working

Three-command end-to-end test (no git history touched). Pick any number
above the registry's current max — e.g., if the registry has 14
invariants, use 99 (or any unused number) in your test phantom file:

```bash
# 1. Inject synthetic phantom into a scanned directory.
#    Substitute <N> with a number greater than the registry's current max.
printf 'Per invariant <N> (not in registry)\n' \
  | sed 's/<N>/99/' \
  > docs/standards/_test_phantom.md

# 2. Run scanner — expect FAIL with exit code 1
python3 ocr-docs-brain/scripts/scan_phantom_invariants.py --sweep
echo "exit: $?"

# 3. Clean up, re-verify clean
rm docs/standards/_test_phantom.md
python3 ocr-docs-brain/scripts/scan_phantom_invariants.py --sweep
echo "exit: $?"
```

Expected behavior:
- Step 2: scanner reports the file path, line number, and the phantom
  number; exit code is `1`.
- Step 3: scanner reports `OK ... clean. Registry contains N invariants`;
  exit code is `0`.

If both steps show the expected pattern, the trigger is operational.

This README itself uses the `<N>` placeholder convention so the
scanner doesn't flag its own examples as phantoms. If you write a
test recipe elsewhere, follow the same convention or whitelist the
file in `scan_phantom_invariants.py::SKIP_BASENAMES`.

---

## CI mirror — `.github/workflows/phantom-scan.yml`

The same scanner runs in CI on every PR and push to main. Catches what
`--no-verify` would bypass locally.

Behavior matches `brain-location-audit.yml`:

- **PR runs** — informational (does not fail the workflow). Posts a comment
  on the PR with the phantom list so the author sees it before merging.
- **Push to main / scheduled / manual dispatch** — blocking. On failure,
  invokes `open_drift_ticket.py` to file a Linear ticket automatically
  (the L5 auto-drift mechanism, prototyped here, reuses the same helper
  that handles invariant #13 audit drift).

Trigger paths:

- `docs/**` — any standards doc, ADR, vision doc
- `ocr-docs-brain/architectural-invariants.yaml` — registry changes can
  invalidate or re-validate existing references
- `ocr-docs-brain/scripts/scan_phantom_invariants.py` — scanner changes
- `ocr-docs-brain/hooks/**` — hook changes
- `README.md` / `ocr-docs-brain/README.md` — top-level docs
- `.github/workflows/phantom-scan.yml` — workflow self-changes

Nightly scheduled run (`0 10 * * *` UTC) catches drift introduced by paths
not covered by the on-PR trigger (e.g., a vendored copy modified outside
the standard propagation flow).

---

## Troubleshooting — what to do when it fires

### Pre-commit fired and you don't think you introduced a phantom

Read the failure output carefully. The scanner names the file, line, and
the specific invariant number claimed. If the reference is in a file you
didn't touch:

```bash
# What did the scanner see?
python3 ocr-docs-brain/scripts/scan_phantom_invariants.py --sweep

# Was the registry recently updated?
git log -p --since=14.days -- ocr-docs-brain/architectural-invariants.yaml
```

A recent registry change may have removed or renumbered an invariant,
causing previously-valid references to phantom. Either: update the stale
reference, or revert the registry change (with reason).

### Pre-commit fired on a legitimate proposal in an ADR

ADRs are exempt. If the scanner flags an ADR, it's a bug in `SKIP_DIRS` in
`scan_phantom_invariants.py`. Open a Story under Brain invariant hygiene
Epic.

### CI fired on main after a clean PR pass

The PR-event scan is informational. A subsequent push (e.g., merging into
main) re-runs blocking. If a phantom slipped past PR review, the main-branch
scan catches it and files a Linear ticket. Action: read the ticket; revert
or follow-up commit.

### Linear ticket says `LINEAR_API_KEY missing`

The CI workflow saw a phantom and tried to file a ticket but the secret
wasn't present. Set it in repo Settings → Secrets → Actions:
`LINEAR_API_KEY` with a key that has write access to OCR-doc team. The
secret is already used by `brain-location-audit.yml`; same key applies.

### Hook is firing on every commit even with clean code

Check `core.hooksPath`:

```bash
git config core.hooksPath  # should print "ocr-docs-brain/hooks"
```

If unset, install: `bash ocr-docs-brain/hooks/install.sh`.
If set but commits still loop, the hook script may have a syntax error.
Run it directly: `bash ocr-docs-brain/hooks/pre-commit`.

---

## Kill switches

For a single commit:

```bash
git commit --no-verify
```

For all hooks entirely:

```bash
git config --unset core.hooksPath
```

Reverting is one line. The doctrine (ADR-003) says use sparingly — every
bypass is signal that either (a) the hook is wrong or (b) the doctrine is
being violated knowingly. Either way, it should be loud.

---

## Maintenance load

- **Token rotations:** N/A for this hook (no secrets touched).
- **Kill switch:** documented above.
- **Annual drift-of-drift check:** the Q3 quarterly framework review reads
  this hook's bypass-rate (count of `--no-verify` commits per month, from
  `git log --grep` or similar) and decides whether the friction level is
  right. High bypass rate → the hook is wrong. Zero bypass rate over a year
  → the hook never caught anything → revisit whether it's still needed
  (probably yes, but verify).

---

## Coordination with other framework hardening

- **OCR-53** (Linear) — Will fold this scanner's logic into
  `check_brain_contract.py` so the brain conformance check catches what
  pre-commit catches. Pre-commit + `phantom-scan.yml` are the fast local +
  CI mirrors; the conformance check is the authoritative gate.
- **OCR-75** (Linear) — Will install equivalent hooks in every product repo
  so vendored standards stay clean too. This OCR-docs hook is the
  prototype; the per-product hooks reuse the scanner with `--registry-url`
  pointing at the canonical YAML in OCR-docs main.
- **L5 auto-drift Epic** (Linear) — Already partly operational. The CI
  workflow `phantom-scan.yml` calls `open_drift_ticket.py` on
  scheduled/push failures — the same helper used by
  `brain-location-audit.yml` for invariant #13 audit drift. Extension Story
  needed: route phantom-scan tickets to the right team and project (today
  the helper has a generic routing fallback).

---

## Why this shape

Per ADR-003 §"Four properties that make it durable forever":

| Property | This hook |
|---|---|
| Idempotent | Same staged files in → same exit code out. No state. |
| Honest | Failure prints file:line:matched-text + registry contents. |
| Observable | Failure mode is loud and actionable. |
| Fast | Sub-second on the staged file set. |

One file, one job, one failure mode, one kill switch. Minimum viable
trigger.
