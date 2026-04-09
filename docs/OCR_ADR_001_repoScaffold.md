# ADR-001: Documentation as Code Before Code

| Field | Value |
|-------|-------|
| Date | April 2026 |
| Status | Accepted |
| Author | Matt |

---

## Context

Most product repos in the OCR product line exist at the design stage. Only OSE and OW have implementation code. The remaining repos — OSG, OSR, OSP, OSM, OWL — have no application code yet.

The question: do we wait for code to exist before documenting architecture, or do we scaffold the documentation structure now?

## Decision

Docs-as-code scaffold established before code so architecture is documented before inertia sets in.

Every product repo gets three files at creation — CLAUDE.md, SKILL.md, README.md — regardless of whether it has application code. The org-level vision lives in OCR-docs `docs/OCR_VISION.md` and is the single source of truth. Product repos derive from it but do not duplicate it.

## Consequences

- Code grows into the documented structure. When a repo moves from docs-as-code to implementation, the architecture is already defined, the cross-product dependencies are already mapped, and the skills are already written.
- No discovery sprint needed when build begins. The first engineering session in any repo starts with full context — not a blank page.
- Documentation debt is prevented rather than accumulated. The structure exists from day one, not retrofitted after three sprints of undocumented decisions.
- Every AI-assisted session in any repo starts at full speed. CLAUDE.md provides the session protocol. SKILL.md provides the operational skills. The org VISION.md provides the product line context.
- The cost is maintenance. Documentation must stay current as decisions evolve. This is managed through the CCR protocol and the DAC compliance skill in OCR-docs.
