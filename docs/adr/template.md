# ADR-NNN: [Decision title in imperative voice]

**Status:** Accepted
**Date:** YYYY-MM-DD
**Deciders:** [Names or roles — e.g., "mzdan + Co-Architect"]
**Scope:** Fleet-wide
**Enforced-by:** invariant #N, #M

<!-- Enforced-by: name every brain invariant that enforces this decision (`invariant #N, #M`), or write `none - <one-line reason>`; each named invariant must list this ADR as `fleet:ADR-NNN` in its `references.adr`, or check_adr_edges.py fails. Every #N on this line is read as an invariant number, so keep PR or ticket numbers off it. -->

## Context

[One to three paragraphs. What is the situation? What forces are at play? What problem does this decision solve? What constraints are non-negotiable?]

[Cite the trigger — the Linear story, PR, brain invariant, doctrine memory file, or product-line moment that exposed the need for this decision. Fleet ADRs typically derive from a pattern that has already been used in one repo and is now being canonized across the fleet.]

## Decision

[A crisp statement of the choice that was made. Imperative voice when possible: "Every product repo gets three scaffold files at creation — CLAUDE.md, SKILL.md, README.md — regardless of whether it has application code yet."]

[Optionally, a small diagram or list summarizing the chosen pattern's moving parts.]

## Alternatives Considered

### Alternative A: [Name]

[1-2 sentence description.]

**Rejected because:** [Specific reason — not "it's worse" but "it fails X requirement / introduces Y risk / has Z cost we can't absorb."]

### Alternative B: [Name]

[Same format.]

### Alternative C: [Name (optional, but include any seriously-considered option)]

[Same format.]

## Consequences

### Positive

- [What becomes easier, safer, or cheaper as a direct result of this choice.]
- [Be specific. "Improves consistency" is not specific; "every new repo starts with full Co-Architect context, eliminating the discovery sprint" is.]

### Negative

- [What becomes harder, more expensive, or requires ongoing discipline.]
- [Be honest. The point of an ADR is to surface trade-offs, not to advocate.]

### Neutral

- [Trade-offs that are neither wins nor losses but worth knowing.]

## Implementation Notes

[Optional. Link to the specific commits, PRs, files, or brain entries that realize the decision. Keep this short — the code IS the implementation; this section just routes a future reader to where to look.]

- [Affected repos:] [list, or "all 7 product repos"]
- [Brain invariant:] [`OCR-docs/ocr-docs-brain/architectural-invariants.yaml` invariant ID, if applicable]
- [Standard:] [`OCR-docs/docs/standards/OCR_STANDARD_*.md`, if applicable]
- [PR:] [Number(s)]

## References

- [Linear story / epic that triggered or shaped the decision]
- [Prior ADRs that this builds on, modifies, or supersedes]
- [Brain contracts that codify the enforcement]
- [Doctrine memory file(s) that govern this class of decision]

## Revisit Criteria

[When should we re-open this decision? Examples:]

- [If the fleet expands beyond N repos, the per-repo overhead may exceed its value.]
- [If a new identity mode is introduced beyond anon/non-anon/both, the scaffold contract changes.]
- [If the workspace migrates off pnpm-workspace, this decision's mechanics need updating.]

[If there's no clear revisit trigger, write "No expected revisit; decision is foundational."]
