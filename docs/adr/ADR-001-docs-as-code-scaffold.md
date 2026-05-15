# ADR-001: Documentation-as-code scaffold before code

**Status:** Accepted
**Date:** 2026-04-01
**Deciders:** mzdan
**Scope:** Fleet-wide

> **Migration note (2026-05-15):** This ADR was originally written as `docs/decisions/OCR_ADR_001_repoScaffold.md` in a camelCase convention parallel to the per-repo MADR format. Migrated to MADR + the fleet ADR home as part of routing-matrix adoption. Original text preserved in Context / Decision / Consequences; Alternatives + Revisit sections added retroactively for completeness. See `CURRENT_STATE_INVENTORY.md` gap G9 closure.

## Context

Most product repos in the OCR product line exist at the **design stage**. As of decision date, only OSE (`ourSharedEvents`) and OW (`ourWKRP`) have implementation code. The remaining repos — OSG, OSR, OSP, OSM, OA — have no application code yet.

The architectural question: do we wait for code to exist in a repo before documenting its architecture, or do we scaffold the documentation structure now?

Two forces shape the answer:

1. **Documentation debt compounds.** Once code exists, architectural decisions accumulate as commit messages, PR descriptions, and tribal knowledge. Retrofitting a documentation layer after the fact is expensive and lossy.
2. **AI-assisted sessions need context to be productive.** A Claude / Co-Architect session that starts on a repo without `CLAUDE.md`, `SKILL.md`, and `README.md` either spends the first hour reconstructing context or makes architecturally-misaligned suggestions.

## Decision

**Docs-as-code scaffold is established before code so architecture is documented before inertia sets in.**

Every product repo gets three scaffold files at creation — `CLAUDE.md`, `SKILL.md`, `README.md` — regardless of whether it has application code yet.

The fleet-level vision lives in `OCR-docs/docs/OCR_VISION.md` and is the single source of truth. Product repos **derive from it but do not duplicate it.** Each repo's `README.md` references the vision rather than restating it.

The scaffold contract per repo:

| File | Role |
|------|------|
| `CLAUDE.md` | Session protocol — how a Claude / Co-Architect session should behave in this repo |
| `SKILL.md` | Operational skills specific to this product line |
| `README.md` | Human-readable orientation for the repo; references `OCR_VISION.md` |

## Alternatives Considered

### Alternative A: Write documentation only when code exists

Wait for the first feature commit before writing architectural docs. Documentation lives in the head of the founder until there's something to document.

**Rejected because:** the documentation debt compounds. By the time three sprints' worth of decisions have shipped, retrofitting the rationale is lossy and expensive — and the Claude/Co-Architect sessions that would otherwise accelerate the build are starved of context. The cost of scaffolding three small markdown files at repo creation is dwarfed by the cost of reconstruction.

### Alternative B: Centralize all per-repo docs in OCR-docs

Put every product's CLAUDE/SKILL/README under `OCR-docs/products/<name>/` rather than in the product repo itself.

**Rejected because:** the docs would drift from the code. The principle "docs live next to the code they describe" is what makes them stay current — a PR that changes behavior is the moment to update docs, and the diff in the same repo is the forcing function. Centralizing breaks that loop.

### Alternative C: One scaffold file per repo, not three

Combine CLAUDE / SKILL / README into a single `INDEX.md` per repo to reduce per-repo file count.

**Rejected because:** the three files serve three distinct audiences — a Claude session (CLAUDE.md), a developer learning the skills (SKILL.md), and a human visitor (README.md). Combining them creates a long file that none of those audiences reads end-to-end, defeating the point.

## Consequences

### Positive

- **Code grows into the documented structure.** When a repo moves from docs-as-code to implementation, the architecture is already defined, the cross-product dependencies are already mapped, and the skills are already written.
- **No discovery sprint when build begins.** The first engineering session in any repo starts with full context — not a blank page.
- **Documentation debt is prevented, not accumulated.** The structure exists from day one; not retrofitted after three sprints of undocumented decisions.
- **Every AI-assisted session in any repo starts at full speed.** `CLAUDE.md` provides the session protocol; `SKILL.md` provides operational skills; `OCR_VISION.md` provides product-line context.
- **Cross-product dependencies are visible early.** Because all eight surfaces share the same scaffold and reference the same vision, mismatches are surfaced before they become technical debt.

### Negative

- **Documentation must stay current.** This is an ongoing maintenance cost. Managed through the CCR protocol and the DAC compliance skill in OCR-docs.
- **Founder effort precedes founder revenue.** Time spent on scaffolds is time not spent on code or sales. The bet is that the scaffolding pays off in compounding AI velocity; if the founder pivots away from AI-heavy build, the cost is sunk.

### Neutral

- **Per-repo scaffold files create three commits per repo before any code exists.** This is a feature, not a bug — the repos are docs-first by intent — but it does mean `git log` in early repos consists largely of doc commits.

## Implementation Notes

- **Affected repos:** all 7 product repos in the fleet (OSE, OW, OSM, OSP, OSR, OSG, OA) + workspace root + OCR-docs hub.
- **Scaffold per repo:** `CLAUDE.md`, `SKILL.md`, `README.md`.
- **Fleet vision source:** `OCR-docs/docs/OCR_VISION.md`.
- **Compliance enforcement:** DAC (docs-as-code) compliance skill in `OCR-docs/.claude/skills/`.

## References

- Fleet vision: `OCR-docs/docs/OCR_VISION.md`
- Routing rule (this decision codified): `ourCommunityRituals/OPERATING_SYSTEM.md §3`
- DAC compliance skill: `OCR-docs/.claude/skills/dac-compliance.skill.md` (if extant)
- Doctrine memory: `~/.claude/projects/.../memory/feedback_*.md` files governing AI-assisted development
- CCR protocol: `OCR-docs/docs/standards/OCR_STANDARD_agentOperatingModel.md`

## Revisit Criteria

- If the fleet shrinks below 3 active products, the per-repo scaffold overhead may exceed its value; consolidation to a single `OCR-docs/products/<name>/` directory becomes worth reconsidering.
- If the AI-assisted-session pattern stops being central to the development model, the rationale for CLAUDE.md scaffolds weakens; SKILL.md and README.md still apply.
- If a new identity mode beyond anon / non-anon / both is introduced, the scaffold contract may need extension.

No expected revisit in the next 12 months; decision is foundational to the docs-first development pattern.
