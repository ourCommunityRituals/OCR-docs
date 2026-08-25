# ADR-007: Reconciliation is the process paradigm — results must return to the brain

**Status:** Accepted
**Date:** 2026-08-25
**Deciders:** mzdan (founder) + Co-Architect
**Scope:** Fleet-wide

## Context

The org's work has always been described as a **reconciliation loop**:

`shared brain → code → CI/CD → test pyramid → red team → results → shared brain`

Every stage was real except the last arrow. Findings travelled *forward* — a fix merged, a check went green — and stopped. They did not return to the brain as trustable input. The practical cost: every review re-derived context from scratch, and hard-won knowledge evaporated at the PR boundary. The loop was drawn but never closed.

On 2026-08-25 a single defect became a **test by fire** that closed the leg end-to-end for the first time. A forms bug invisible to ~200 assertion-by-substring tests (OSE-1003) was root-caused, **generalized into a reusable standard** (`OCR_STANDARD_artifactIntegrityChecks.md`, OSE-1005/1006), **enforced as a CI gate** (the honest T4 gate + the embedded-JS / testid-drift checks), and **returned to the brain** as a role-attributed, evidence-cited results readout. The finding did not just get fixed; it made the system permanently harder to break in that whole class. That worked example is the trigger for canonizing the pattern as the org's process paradigm — this is the founder's operating process, made explicit.

## Decision

**Reconciliation is the fleet's process paradigm, and its defining obligation is that results return to the brain.** Every substantive close-out (a merged body of work, a gate landing, a milestone) MUST close the `results → brain` leg by producing, in order:

1. **A brain artifact** — generalize the finding into a standard/invariant so the *class* cannot silently recur (not a one-off fix left in a PR).
2. **An enforcement** — wire that standard as a machine-checkable CI gate (documented-but-unenforced does not count).
3. **A results readout** — a **six-POV SCRUM close-out** (PO · BE · FD · Design · QA · SRE/SDET · DevOps), evidence-cited (commits, run IDs, ticket IDs), persisted where the team and the next review can cite it.

Two rules make the returned results *trustable*, not merely present:

- **Negative-control before trust.** A checker's teeth must be proven on a known-bad input before its results are believed. (The regex-desync that made the first artifact-integrity detector return zero flags on genuinely broken source is the standing cautionary tale.)
- **Earned, not asserted.** Only negative-controlled, enforced findings re-enter the brain as fact — satisfying CCR v3.0's evidence-based-verification rule by construction.

Notable inflections are tagged `flagpole` so the trajectory stays navigable; the return arrow, once closed, is what lets CCR keep trusting flywheel results after they return to the brain.

## Alternatives Considered

### Alternative A: Forward-only (fix + green check, no return)

Close work when the code merges and CI is green; capture nothing back to the brain.

**Rejected because:** knowledge evaporates at the PR boundary. Every review restarts from zero, the same defect classes recur, and "green" repeatedly turns out not to mean "true." This is the status quo the test by fire disproved.

### Alternative B: Documentation-only reflection

Write findings into a doc after the fact, but do not enforce them or require a structured readout.

**Rejected because:** un-enforced docs drift out of agreement with the code, and un-negative-controlled claims are not trustable input. A brain that records intentions it does not enforce is worse than silence — it manufactures false confidence.

### Alternative C: Per-repo, ad-hoc reconciliation

Let each spoke decide its own close-out ritual.

**Rejected because:** it does not compound and is not inheritable. The whole value is that each finding raises the floor the *next* review starts from, fleet-wide. A spoke-local habit re-enters as drift through the other spokes (per `OCR_STANDARD_knowledgeHomes.md`).

## Consequences

### Positive

- **It compounds.** Each finding hardens the brain, raising the floor the next review starts from. A maintained system holds a line; this one moves the line — the brain gets smarter with use.
- **Trust is earned by construction.** Negative-control + enforcement mean results re-enter as fact, so CCR loops can cite prior results instead of re-deriving them — reviews get faster and more confident over time.
- **The trajectory is referenceable.** The `flagpole` label + the *Reconciliation Loop — Flagpole Index* give a navigable history to narrate the process from.

### Negative

- **It requires ongoing discipline.** The readout, the standard-promotion, the flagpole tag, and the negative-control step must be habitual. The paradigm decays the moment it is treated as automatic and any of these is skipped — the leg quietly re-weakens.
- **It adds a close-out cost.** Every substantive close-out now owes a brain artifact + enforcement + readout, not just a merge.

### Neutral

- More brain documents and standards accrue over time; this is intended (the brain growing), but it raises the bar on keeping the index (`standards-index.md`, ADR README) reconciled.
- The six-POV readout formalizes what CLAUDE.md §3 / The Loop step 8 already asked for; it is a ritualization, not a new obligation.

## Implementation Notes

- **Affected repos:** all product repos (fleet-wide paradigm; each spoke inherits the close-out obligation).
- **Exemplar standard:** `OCR-docs/docs/standards/OCR_STANDARD_artifactIntegrityChecks.md` (the first full turn) — PR #99.
- **Return-arrow mechanism:** the six-POV SCRUM close-out readout (persisted as a Linear project status update; post-merge also `CLAUDE.md §3` role states).
- **History surface:** the `flagpole` workspace label + the *Reconciliation Loop — Flagpole Index* Linear document.
- **Composes with:** `OCR_STANDARD_perStoryTestPyramid.md` (the pyramid stage) and `OCR_STANDARD_knowledgeHomes.md` (reconciliation's third leg — promote shared truths into the brain).

## References

- Linear document: *Reconciliation as the Process Paradigm — the results→brain leg (test by fire, 2026-08-25)* (the team-facing reflection this ADR canonizes).
- The test by fire: OSE-1003 (bug) → OSE-1005/OSE-1006 (generalized checkers) → OSE-554 (honest gate) → main `663eae8` (PR #395).
- CCR protocol (`skills/ccr-protocol.knowledge.md`) — evidence-based verification; this ADR is how CCR keeps trusting results after they return to the brain.
- Builds on ADR-003 (self-checking infrastructure) and ADR-006 (free-forever as a structural property) — same "make the intention machine-enforced, not documented" spirit.

## Revisit Criteria

No expected revisit; the decision is foundational. Revisit only if the loop's stages themselves change (e.g. a new stage is inserted), or if a materially lighter-weight return mechanism is proven to keep results equally trustable without the full readout ritual.
