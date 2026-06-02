---
name: brain-check
description: Run the brain conformance check against the current product repo, parse the report, surface drift in plain language, and (optionally) file Linear tickets for findings. The L1 daily-driver invocation.
allowed-tools: Bash Read Grep
argument-hint: "[--file-tickets]"
---

# Brain conformance check (L1 daily-driver)

Run the L1 conformance machinery from `OCR-docs/ocr-docs-brain/scripts/check_brain_contract.py` against the product in `cwd`, interpret the result, optionally file Linear tickets for findings.

This is the manual-invoke version of what CI runs on every PR. Use it when:

- You're about to open a PR and want to pre-flight.
- You just landed a doctrine change in OCR-docs and want to see what each product reports.
- A CI run failed on `check_brain_contract.py` and you want a faster local reproduction.

## Step 1 — Identify the product

Resolve `cwd` to a product registered in `OCR-docs/ocr-docs-brain/product-registry.yaml`. Match against:

- `ourWKRP/` → `wkrp`
- `ourSharedEvents/` → `ose`
- `ourSharedMagnets/` → `osm`
- `ourAirwaves/` → `oaw`
- `OCR-docs/` → `ocr` (self-check)

If `cwd` is outside a recognized product repo, report and stop.

## Step 2 — Run the check

```bash
PYTHON_BIN=$(command -v python || command -v py || command -v python3)
$PYTHON_BIN OCR-docs/ocr-docs-brain/scripts/check_brain_contract.py --product <inferred>
```

Capture stdout, stderr, exit code. If the script doesn't exist where expected, surface the path issue and stop.

## Step 3 — Parse and interpret

Read the conformance report (today: `OCR-docs/ocr-docs-brain/conformance-report.json` — confirm path; the script may emit elsewhere). Categorize findings:

### Per-invariant findings

For each invariant whose `applies_to` (v1) or per-surface resolution (v2 once ADR-002 lands) includes this product:

- **OK** — test file present at expected path; no further action.
- **MISSING** — test file declared in registry but not found in repo. Surface invariant N, expected path, suggested location.
- **NON-CANONICAL** (when OCR-53 ships) — test file exists but lives outside the canonical path. Surface current path, expected path.
- **UNREACHABLE** (when OCR-53 ships) — test file exists at canonical path but no CI workflow invokes it. Surface the spec path and the absence of `npm run` / `playwright test` / `vitest run` invocation in any workflow.

### Cross-cutting findings

- **VENDORED STANDARDS DRIFT** (when OCR-75 ships) — `.ocr-standards/` differs from OCR-docs canonical. Surface diff summary.
- **PHANTOM INVARIANT REFERENCES** (when phantom-scan integrates) — any `invariant #N` reference in vendored docs to N not in registry. Cross-link to `/scan-phantoms` for detail.
- **PRODUCT-REGISTRY MISMATCH** — if `product-registry.yaml` says this product is in regulatory pool X, but its actual code references pool Y, flag.

## Step 4 — Plain-language report

Format output as:

```
brain-check: <product>
=========================

Invariants in scope: <count>
  ✓ OK: <count>
  ⚠ Findings: <count>

[per-finding block]
  Invariant: #<N> <name>
  Type:      <MISSING | NON-CANONICAL | UNREACHABLE | ...>
  File:      <path or "n/a">
  Expected:  <expected state>
  Action:    <human-readable fix>
  Linear:    <existing related ticket if found, else "none">

[summary]
Verdict: PASS / FINDINGS
Run again after fix or with --file-tickets to auto-file Linear stories.
```

## Step 5 — Optional: file Linear tickets

If invoked with `--file-tickets`:

For each finding, draft via `/story` conventions, route to the correct project:

- **MISSING / NON-CANONICAL / UNREACHABLE** → project: `Brain invariant hygiene` (if cross-product) or the product's invariant Epic (if product-specific).
- **VENDORED STANDARDS DRIFT** → project: `Brain invariant hygiene` (OCR-75 work).
- **PHANTOM INVARIANT REFERENCES** → project: `Brain invariant hygiene` (OCR-74 work).
- **PRODUCT-REGISTRY MISMATCH** → project: the product's own backlog (e.g., `ourWKRP` general).

### Idempotency

Don't create duplicate tickets. Fingerprint each finding as `sha256(product | invariant | finding-type | offending-path)`. Before creating, search Linear for existing tickets with that fingerprint in a `framework-drift` label or in the description. If found, comment-refresh instead of duplicating.

This is the same idempotency contract the L5 auto-drift-tickets Epic (Initiative-level) will operate under in CI. The skill is the manual-invoke prototype.

## Step 6 — Exit code

- 0 if zero findings.
- 1 if any findings (PR pre-flight fails loudly).
- 2 on tool error (script not found, product not registered, etc.).

## Doctrine link

This is L1 of the framework as a daily-driver command, per ADR-003 §"The six-layer model".

When the L5 auto-drift Epic ships, the CI version of this check files tickets automatically; this skill becomes the developer's local mirror for pre-flight runs.

## What this skill does NOT do

- Doesn't modify any code.
- Doesn't run the full pyramid (L2 — that's `npm test` etc., per product).
- Doesn't validate ADR doctrine compliance (that's `/ccr`).
- Doesn't scan for invariant-number phantoms in docs (that's `/scan-phantoms`).
- Doesn't deploy anything (that's `/deploy-ourwkrp` per product).

It is specifically the L1 conformance check as a developer command.
