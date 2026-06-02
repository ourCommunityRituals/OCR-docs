---
name: adr
description: Scaffold a new Architectural Decision Record in OCR-docs/docs/adr/ following the established pattern (ADR-001/002/003). Picks the next number, populates Status/Date/Deciders/Context/Decision/Consequences/Cross-refs/Validation.
allowed-tools: Read Glob Write Bash
argument-hint: "<short kebab-case title>"
---

# New Architectural Decision Record

Create `OCR-docs/docs/adr/ADR-NNN-$ARGUMENTS.md`.

## Step 1 — Next available number

Glob `OCR-docs/docs/adr/ADR-*.md`. Parse the numeric prefix from each filename. **Next number = max + 1.**

**Numbers are assigned at write time, never reserved.** This is the same rule as the brain's invariant registry — reserving in advance is what produced phantoms #13 and #14. If a prior ADR or standards doc references "ADR-NNN" before NNN is written, that reference is a phantom and should be flagged via `/scan-phantoms` (extended for ADR numbers — see Step 5).

If there's a gap in the sequence (e.g., 001, 003, 005 — missing 002 and 004), ASK the user whether to fill the gap or take the next-after-max. Don't auto-fill.

## Step 2 — Gather inputs

Prompt for or infer:

- **Title** — from `$ARGUMENTS` (kebab-case → Title Case).
- **Context** — *what problem? Why now? What evidence motivates this decision?* The user provides 2-5 sentences of background.
- **Decision** — *the choice being recorded.* One paragraph maximum.
- **Deciders** — default `Matt (Co-Architect convener)`. Confirm.
- **Cross-refs** — propose the actually-relevant predecessor ADRs by reading their summaries. ADR-001 (Docs-as-Code) and ADR-002 (Identity-Profile-Keyed) and ADR-003 (Self-Checking Infrastructure) are the current foundation; pick which apply.

## Step 3 — Scaffold

Use the **ADR-003 shape** as the template (it's the most-evolved):

```markdown
# ADR-NNN: <Title>

**Status:** Proposed
**Date:** <today YYYY-MM-DD>
**Deciders:** <from input>
**Supersedes:** None  | <prior ADR if applicable>
**Cross-refs:** <picked from Step 2>

---

## Context

<from input — what's the problem, what's currently broken or aspirational, what evidence motivates the decision>

## Decision

<the actual choice — one paragraph, declarative>

## Consequences

### Positive

- <bulleted>

### Negative / trade-offs

- <bulleted — be honest about what this costs>

### Neutral / explicit

- <bulleted — what this does NOT decide; scope boundary>

---

## Implementation

<sketch — what Linear Initiative / Project / Epic this implies; what self-check hook applies to it>

## Validation

<how do we know the ADR is being honored; what catches drift; which invariant or CI gate is the structural lock>

## Open questions

- <bulleted — pending decisions not made in this ADR; tracked elsewhere>

## References

- <bulleted — canonical files, Linear URLs, related docs, prior art>
```

## Step 4 — Status discipline

Default new ADRs to `Proposed`.

Transitions:
- `Proposed` → `Accepted — implementation in flight` when the matching Linear Initiative/Project lands.
- `Accepted — implementation in flight` → `Accepted — implemented` when all six success criteria (or whatever the ADR defines as DOD) are true.
- Any state → `Superseded by ADR-NNN` when a successor ADR formally replaces it. Update the successor's `Supersedes:` field in lockstep.

Never delete an ADR. Never renumber. The sequence is the contract.

## Step 5 — Coordination with Linear

If `Status: Accepted — implementation in flight`, propose:

- A Linear Initiative if the ADR is foundation-level (like ADR-003).
- A Linear Project (Epic) if the ADR is feature-level (like ADR-002).
- Sub-Issues (Features/Stories) under that.

Don't fire `save_initiative` or `save_project` from this skill — output the proposal for review and let the user invoke `/story` or the Linear MCP directly.

## Step 6 — Validate

After writing:

1. Run `/scan-phantoms` to confirm no new phantom references were introduced.
2. Run `/ccr <new-ADR-path>` to put the ADR itself through review before it's accepted.

The ADR doesn't ship until both pass.

## Anti-patterns

- **Don't number-reserve in advance** (the failure mode that produced phantoms #13 and #14 — both predicted to exist by other docs before the registry encoded them).
- **Don't skip the Validation section** — an ADR without a self-check hook is doctrine without teeth.
- **Don't conflate Accepted with Implemented** — Accepted = binding decision; Implemented = success criteria met.
- **Don't write "Open questions" as a TODO list** — every open question must trace to a Linear story or a future ADR; otherwise it's not really tracked.
- **Don't omit Cross-refs** — ADRs that don't cite their predecessors lose the chain that future agents need to navigate.
