# Fleet Architecture Decision Records

This directory holds **fleet-wide** ADRs — decisions that apply across the OCR product line, not to one product repo alone. Single-repo ADRs live in the respective repo at `<repo>/docs/adr/`.

The routing rule is encoded in [`OPERATING_SYSTEM.md §3`](../../OPERATING_SYSTEM.md) at the OCR-docs root:

| Scope | Lives at |
|-------|----------|
| Single-repo architectural decision | `<repo>/docs/adr/ADR-NNN-kebab.md` |
| **Fleet-wide architectural decision** | **`OCR-docs/docs/adr/ADR-NNN-kebab.md` (this directory)** |
| Cross-app architectural invariant | `OCR-docs/ocr-docs-brain/*.yaml` (Brain) |
| Fleet-wide engineering standard | `OCR-docs/docs/standards/` |

ADRs and Brain invariants are complementary, not redundant:

- **Brain invariants** are machine-readable contracts that gate CI. They say _what_ must hold.
- **ADRs** are human-readable records of the reasoning behind a decision. They say _why_ that contract was chosen, what was considered, and what trade-offs were accepted.

## Status

| #                                                  | Title                                          | Status   | Date       |
| -------------------------------------------------- | ---------------------------------------------- | -------- | ---------- |
| [ADR-001](ADR-001-docs-as-code-scaffold.md)        | Documentation-as-code scaffold before code     | Accepted | 2026-04-01 |
| [ADR-002](ADR-002-identity-profile-keyed-invariants.md) | Key invariants to identity profile, not product-ID lists | Proposed | 2026-05-21 |

ADR series planned (fleet scope, not yet written — numbers are provisional and
assigned at write time per the Numbering rule below):

- Self-hosted runner pool as the single CI runtime (fleet rule from `feedback_self_hosted_only.md`)
- Security-first test pyramid: every product runs the same pyramid; security gates before lint
- `@ocr/flags` shared package as the runtime-binding contract surface for the Brain `flags-contract.yaml`
- Two-axis tier model: sponsor pricing (local/mid/premium) × flag presets (free/mid/enterprise) — never merged

## Numbering

Fleet ADRs are numbered independently from per-repo ADRs. This is intentional — the two sequences track different scopes:

- OSE ADR-001 is "Anonymous-identity architecture" (OSE-scoped).
- OCR-docs ADR-001 is "Docs-as-code scaffold before code" (fleet-scoped).

There is no collision because the path disambiguates: `ourSharedEvents/docs/adr/ADR-001-*.md` vs `OCR-docs/docs/adr/ADR-001-*.md`.

Numbers are assigned at write time, never reserved. Once an ADR is on `main`, **its number never changes**, even if it's later superseded or deprecated.

## When to write a FLEET ADR (not a per-repo one)

Write a fleet ADR when the decision satisfies **at least two**:

1. It applies to two or more product repos in the fleet.
2. It defines a pattern that new product repos must follow at creation.
3. It governs a shared package (`packages/*`), shared CI workflow, or shared brain contract.
4. It encodes a cross-cutting concern (security posture, runner model, identity-mode taxonomy, pricing model).
5. It supersedes or modifies an existing fleet-level decision.

If the decision only affects one repo, write a per-repo ADR in that repo's `docs/adr/` directory.

## When NOT to write any ADR

- Bug fixes (even fleet-wide ones).
- Library upgrades that don't change the integration surface.
- Per-product features (those go in `<repo>/docs/features/`).
- Anything the Linear ticket + PR description already captures adequately.

## Template

Copy [`template.md`](template.md) when starting a new fleet ADR. MADR (Markdown Any Decision Record) format throughout — same format as per-repo ADRs so they are interchangeable in tooling.

## Lifecycle

| Status         | Meaning                                                                                                                                                |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Proposed**   | Drafted but not yet implemented. Most ADRs skip this state because we record decisions as they ship.                                                   |
| **Accepted**   | The decision is in effect. The corresponding code, gates, and brain contracts are live.                                                                |
| **Deprecated** | The decision is no longer the recommended approach but is still in effect (e.g., legacy code hasn't been migrated yet). New code should not follow it. |
| **Superseded** | A later ADR has replaced this one. Mark the new ADR's number in the `Status` line: `Superseded by ADR-NNN`.                                            |

Accepted ADRs are immutable except for the Status line. To change a decision, write a NEW ADR that supersedes the old one. The historical record is preserved.

## Process for adding a new fleet ADR

1. Identify the decision while it's fresh.
2. Run the "should this be a FLEET ADR?" criteria above. If ≥ 2 apply, proceed.
3. Copy `template.md` to `ADR-NNN-kebab-case-title.md`. The number is `1 + max(existing ADR numbers in THIS directory)`.
4. Fill out all sections. Spend the most words on Alternatives Considered + Consequences.
5. Cross-link from the relevant code, brain invariant, standard, or doctrine memory file back to the ADR.
6. Update the Status table at the top of this README.
7. Land in a focused docs PR — not bundled with feature work.

## Migration note (2026-05-15)

The previous `OCR-docs/docs/decisions/OCR_ADR_001_repoScaffold.md` (camelCase, parallel format) has been migrated to this directory as `ADR-001-docs-as-code-scaffold.md` in MADR format. The original file is removed. This closes gap G9 in `CURRENT_STATE_INVENTORY.md` and aligns the fleet on a single ADR convention.

`OCR_DECISION_mockDataProvider.md` in `docs/decisions/` is **not** an ADR — it remains as a decision record under that name pending its own migration assessment.
