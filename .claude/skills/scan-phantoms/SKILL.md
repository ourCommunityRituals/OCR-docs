---
name: scan-phantoms
description: Scan every standards doc, ADR, vendored .ocr-standards copy, and (optionally) Linear project description for "invariant #N" references and validate each N against the canonical registry. Reports phantoms — references to numbers not encoded.
allowed-tools: Read Grep Glob Bash
---

# Scan for phantom invariant references

Catch references to invariant numbers that don't exist in the canonical registry — the failure mode that produced **#13** (`brain_enforcement_location`, resolved PR #68) and **#14** (`mobile_workability`, open as OCR-74), and the mis-attribution in OCR-RedTeamAgent's claim on `#12`.

## Source of truth

`OCR-docs/ocr-docs-brain/architectural-invariants.yaml` — the canonical registry. Every `- id: N` is a legal reference number.

## Scan targets (in order)

1. **OCR-docs canonical standards** — `OCR-docs/docs/standards/*.md`
2. **OCR-docs ADRs** — `OCR-docs/docs/adr/*.md`
3. **OCR-docs Vision & top-level** — `OCR-docs/docs/OCR_VISION.md`, `OCR-docs/README.md`, `OCR-docs/ocr-docs-brain/README.md`
4. **Vendored copies in every product repo** — for each sibling of `OCR-docs/` in the workspace, scan `<product>/.ocr-standards/**/*.md`. Sibling repos:
   - `ourWKRP/`
   - `ourSharedEvents/`
   - `ourSharedMagnets/`
   - `ourSharedGames/`
   - `ourSharedRecords/`
   - `ourSharedPulse/`
   - `ourAirwaves/`
5. **Linear project descriptions** (optional, requires Linear MCP) — fetch every project and scan its description. If MCP unavailable, skip with a note in the report.

## Detection patterns

Run case-insensitive regex against each target:

```
[Ii]nvariant\s*#?\s*(\d+)
```

```
invariant_(\d+)
```

```
\binvariants?\b[^.\n]{0,40}#(\d+)
```

For each match, extract N. Build the registry set from the YAML's `- id:` field. If N not in registry: **PHANTOM**.

## Report shape

For each phantom found, surface:

| File | Line | N | Matched text | Closest legitimate # | Suggested action |
|---|---|---|---|---|---|
| docs/standards/OCR_STANDARD_someStandard.md | LINE | `<N>` | `"invariant <N>'s exceptions"` | `<NEAREST>` | Encode via Linear Story |
| `<product>`/.ocr-standards/standards/OCR_STANDARD_someStandard.md | LINE | `<N>` | (vendored copy of above) | `<NEAREST>` | Auto-fixed by propagator once canonical resolves |

(Placeholder syntax `<N>` keeps this skill file from claiming a literal invariant number — its own examples would phantom under the very check it documents.)

For each legitimate reference, no output — silent on the happy path.

If zero phantoms found:

```
✓ No phantom invariant references found. Every #N in scanned content resolves to architectural-invariants.yaml.
Registry contains N invariants: [list]
Scanned: M files across K products.
```

## Phantom triage hints

When a phantom is found:

- If a nearby ADR proposes the same N → coordinate-with-ADR hint.
- If the file is a vendored copy AND the canonical also has the phantom → fix canonical first, then re-propagate.
- If the file is a vendored copy AND the canonical does NOT have the phantom → propagation drift; vendored is stale.
- If the file is a Linear project description AND the project claims to "introduce" or "implement" that N → flag as project-description error.

## Exit code

- 0 if zero phantoms.
- 1 if any phantoms.
- 2 on tool error (registry not readable, glob failed, etc.).

This makes the skill wire-able into a pre-commit hook downstream: `git config core.hooksPath` setup → fail commits that would land a new phantom.

## Doctrine link

ADR-003 success criterion #3 — *"a change that would violate an invariant fails CI before merge."* This skill is the manual-invoke version of the eventual CI gate. When OCR-53's `check_brain_contract.py` hardening lands the phantom-number guard, this skill becomes the developer's local mirror of that CI check.

## What this skill does NOT do

- Does not modify any file.
- Does not file Linear tickets (use `/story` or `/brain-check --file-tickets` if you want that).
- Does not validate that an invariant's *content* matches its referenced spec — only that the *number* is legitimate.
- Does not scan code (`src/**/*.ts`, etc.). Code references to invariants go through the conformance check (`/brain-check`); this skill scans documentation.
