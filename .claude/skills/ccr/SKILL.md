---
name: ccr
description: Run a Critical · Conservative · Recursive review on a target (PR, ADR, code change, design doc, Linear story). Produces structured findings per loop, identifies holds, surfaces blind spots. Matt's documented review protocol, codified.
allowed-tools: Read Grep Glob Bash WebFetch
argument-hint: "<target — file path, PR URL, Linear issue ID, or 'last commit'>"
---

# CCR Review — Critical · Conservative · Recursive

Apply the OCR review protocol to **$ARGUMENTS**.

Source doctrine: `feedback_ccr_review.md` in the OCR memory layer.

## Resolve the target

- File path → read it
- PR URL → `gh pr view <number> --json files,body,title,additions,deletions` + fetch the diff
- Linear issue ID (`OCR-NNN`, `OW-NNN`, `OSE-NNN`) → fetch via Linear MCP
- "last commit" → `git show HEAD`
- "branch" → `git diff main...HEAD`

If the target is ambiguous, ASK before proceeding.

## Loop 1 — Critical pass

Ask: *what would break this?*

Surface concerns in every category that applies:

- **Edge cases** the author didn't address.
- **Failure modes** — silent failures, cascading failures, race conditions, partial deploys.
- **Assumptions that don't hold** under load, under hostile input, under split-brain, under network partition.
- **Drift from doctrine** — does this violate an architectural invariant, an ADR, or a standards doc?
- **Security** — PII handling, authn/authz, secret leakage, injection vectors, identity-surface confusion.
- **Performance / scalability** — quadratic loops, unbounded retention, missing indexes, N+1 queries.

Output: a numbered list of concerns, each tagged severity (**High** / **Medium** / **Low**).

## Loop 2 — Conservative pass

Ask: *what is the smallest version of this that still ships value?*

- Can scope be reduced without losing the core benefit?
- Are there over-engineered pieces (premature abstractions, speculative flexibility)?
- What can be **deferred** to a sibling Story without blocking this one?
- What's the deferral cost vs. the landing cost?

Output: a numbered list of scope-reduction suggestions, each tagged **keep / defer / cut**.

## Loop 3 — Recursive pass

Ask: *what does this imply we should also do — that we haven't?*

- Tests that should exist for behaviors this touches but doesn't currently cover.
- Documentation that goes stale because of this change (READMEs, standards, vendored `.ocr-standards/`, ADRs).
- Other surfaces, products, or contracts affected by this change.
- Sibling Linear stories that should be filed.
- Invariants that might need to be enriched, added, or whose enforcement layer this surfaces a gap in.

Output: a numbered list of follow-on items, each tagged **required / recommended / nice-to-have**.

## Final synthesis

After all three loops:

- **Verdict** — `PASS` / `HELD` / `FAILED`, with one-sentence rationale.
- **Top three concerns** across all loops.
- **Top three follow-on items** across all loops.
- **Holds** — explicit list of items that MUST resolve before this can pass; empty if PASS, non-empty if HELD.

The verdict is discrete. `HELD-80%` and similar percentages are NOT acceptable terminal states without an explicit hold list naming what would convert HELD → PASS.

## Anti-patterns

- **Don't restate what the change does** — assume the reader knows.
- **Don't be polite at the cost of being useful** — surfacing a real concern IS the job.
- **Don't pile on cosmetic nits in Loop 1** — reserve Critical for substance; cosmetic goes in Loop 3 as nice-to-have.
- **Don't repeat the same point across loops** — one loop owns each finding.
- **Don't end without a verdict** — every CCR run produces PASS, HELD, or FAILED.

## When to call this

Per the doctrine: *"on every significant work."* That includes:

- Every architectural decision before it lands as an ADR.
- Every Initiative-level Linear Project before its first Epic ships.
- Every PR that touches the brain, an invariant, a standards doc, or a CI gate.
- Every "I should ship this" instinct on a non-trivial change.

The pattern is: *don't ship significant work without it.*
