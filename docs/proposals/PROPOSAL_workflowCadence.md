# PROPOSAL — Workflow outcome policy (green advances / red escalates)

**Status:** 🔒 INERT PROPOSAL — blocked on **OCR-146** · not doctrine · lives in `docs/proposals/`
(NOT `docs/standards/`) so it does not propagate to spokes · **Proposed:** 2026-09-07 · **Owner:** Matt

> Disposition of the closed PR #119 (`OCR_STANDARD_workflowCadence`, CCR-rejected 2/5 as a standalone
> standard). The readout gauge folded into [[OCR_STANDARD_reconciliationLoop]] §6.1. **This file holds
> the one genuinely-new, un-decided piece: the outcome policy — the rule for when the brain may advance
> autonomously vs. punt to a human.** It is an *authorization-doctrine* change and gets its own review.

## The policy (the target — see the INERT gate below before acting on it)
After a run passes the three independent stringent layers — **CCR** (scrum team attacks the approach,
early, all-angles) · **automated tests / pyramid** · **shared-brain evaluation of the results**:

- **Full green through every layer** → the change is cleared to move forward.
- **Any red — or any _indeterminate_** (a check that errored, didn't run, or wasn't produced by a gate
  the brain does not control) → **andon: punt to a human. Fail-closed. Silence is not green;** an
  undetermined result is treated as red.

## 🔒 What "cleared to move forward" means TODAY (the inert gate)
> **The brain does NOT merge.** Today, and until OCR-146 lands, *"cleared to move forward" means
> "green — surface to a human; the human executes the commit/merge."* The brain prepares and presents;
> it never merges. This is the standing hard boundary [[feedback-agent-never-controls-authorization]],
> unchanged.

## The evolution this proposes (NOT active — the un-decided part)
That the brain could one day **hold merge authority** on full-green — the "human on the loop, not in
it" end-state — governed by two rules:

1. **Stringency scales with authority.** A gate that only advises may be loose; a gate that may *merge*
   must be the strictest of all, because no human is downstream to catch it. The more you trust the
   green, the more the green must be able to refuse.
2. **A gate earns merge authority; it is never assumed.** Merge authority is granted **only** to a gate
   that is **un-gameable + born-red-proven** — every signal *derived* (not self-narrated), the measurer
   *separate* from the measured, and *observed* red on an injected failure. Granted **phased** (lowest
   risk first) with an **explicit human ratification at each phase boundary** — never self-activating on
   "the trend looks ready."

## Why INERT (the blocker)
The readout today is **self-graded** (measurer = measured) — a mirror that can't reliably say *no*
(the CCR's finding). A policy that grants merge authority through a gate that can lie is "green is
rented" inverted: authority before the gate that earns it. **This proposal cannot leave INERT until
OCR-146** (un-gameable derived readout + separate-measurer + born-red) **is DONE.** Even then, it moves
to *review*, not to *doctrine* — and merge authority is granted phased, per §2 above, by explicit owner
ratification, not by this file.

## Provenance
From PR #119's CCR disposition (2026-09-07): standalone standard closed; gauge → reconciliationLoop §6.1;
outcome policy → here (inert). Blocked on OCR-146. Graduates to a standard (or an amendment to
[[feedback-agent-never-controls-authorization]]) only after ratification.
