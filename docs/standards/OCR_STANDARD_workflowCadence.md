# OCR_STANDARD_workflowCadence

**Status:** 🚧 DRAFT — PROPOSAL, awaiting owner ratification · **Owner:** Matt · **Proposed:** 2026-09-07

> ⚠️ This is a DRAFT. It is not active doctrine until the owner flips Status → ACTIVE and merges.
> Until then, nothing here is binding; it is a reviewable proposal.

> **This is how decisions are made and Linear stories are written here — codified.** Not a new
> framework: it names the method the owner already works in and points at the **skills that already
> run it**. A decision needs making → **`/ccr`** attacks the approach from every angle, early,
> together → the best approach emerges → it is **written up as a classified Linear story** (`/story`
> + `work-intake` + [[OCR_STANDARD_storyClassification]]) → **`/sync`** tracks and reconciles it each
> run → the **outcome policy** (§7) advances on green, punts on red.
>
> It adds only the two things that weren't already skills: the persisted per-run **readout gauge**
> (§5–6) and the **green-advances / red-escalates outcome policy** (§7) — the "human on the loop, not
> in it" rule. Everyday name: **sync** (`/sync`).

## 0. The skills it composes (this standard is the method; the skills are the instances)
- **Decide** → **`/ccr`** — the Critical · Conservative · Recursive scrum-team review. *Already a
  skill.* This is **how a decision gets made** (§3): attack the approach from all angles, early, to
  the 95% gate.
- **Write the story** → **`/story`** + the **`work-intake`** four-field contract (Stated Problem ·
  DoD · Verification · Formatting) + [[OCR_STANDARD_storyClassification]] (classify it). This is
  **how a decision becomes tracked work** — a well-formed, classified Linear story.
- **Run / reconcile** → **`/sync`** = [[OCR_STANDARD_reconciliationLoop]] (verify-first,
  sync-every-surface, file-a-story, churn-bounded).
- **Judge health** → the kaizen doctrine: health is a **derivative** (trend + direction), never a
  level (green).

## 1. What counts as a run
A run fires on either trigger; both are required:
- **Session close-out** — a human/agent finishes a chunk of work → runs `/sync` before stopping.
- **Scheduled sweep** — the cron → runs the unattended pass.

## 2. The everyday loop (in order, every run)
1. **Classify at intake** — new/touched tickets get a class (queue items must; reservoir may wait).
2. **Sync, verify-first** — drive drift to zero across the surfaces; every Done-flip cites a SHA.
3. **Read out** — emit the fixed readout (§5).
4. **Persist** — append the readout to the run log (§6) — *the gauge*.
5. **Read the trend** — judge the derivative, not the snapshot.
6. **Apply the outcome policy** (§7) — green advances; red or indeterminate punts to a human.

## 3. CCR's role — early, collaborative, all-angles approach-selection (NOT late gatekeeping)
The optimism a review must counter lives in the **initial interpretation** — the story as first
written, the plan on first read, the "this looks fine." **CCR is the antidote to that optimism.**

CCR is a **team of professionals attacking the work from every angle, as early and as fast as
possible, while the approach is still soft** — so the story converges on its *best* approach
**together, before any code hardens.** It is a **design-time** activity, not a final inspection:

- **Early is the point.** It is cheap to change the approach before it is built and expensive after.
  Run the CCR **before** building, so every professional angle is applied while changing direction
  is still free. (Worked example: OSE-714 — the CCR ran pre-build, the panel attacked the plan from
  four angles at once, caught a false-green test *and* a three-weeks-stale premise, and the better
  approach emerged collaboratively before a line of code was written.)
- **The team is the check on the team.** The guard against a weak/optimistic review is not a higher
  authority overruling it — it is the **diversity of the scrum roles** (incl. the Dr. of Cyber
  Security and the Technical Writer) plus the **recursion** (loops until the 95% gate). Four
  professionals attacking from four angles is what stops any single optimistic read from carrying;
  the loops are the check on the round.
- **Extended team, always.** Security and documentation are first-class lenses, not add-ons.

## 4. The three-layer trust structure
Trust to advance is earned by **three independent stringent layers, each able to say _no_,** so no
single lie survives — each guards the others (separation of duties at the system level):

| Layer | Question it answers | Failure it catches that the others can't |
|-------|---------------------|------------------------------------------|
| **CCR (scrum team, §3)** | Is this the *right approach*, built the right way? | A vacuous test; a stale premise; a blind spot the automation can't see. |
| **Automated tests / pyramid** | Does the *implementation* do what it must? | A regression in covered behaviour; enforced mechanically, born-red. |
| **Shared brain** | Does the *whole* cohere across every surface — safe to move? | Cross-surface drift; an over-optimistic round; the read-and-react. |

CCR picks the right thing to build; the tests prove it was built; the brain decides it is safe to move.

## 5. The readout template (fixed, light — emitted every run)
```
## Workflow readout — <date>   Trigger: /sync (manual) | scheduled
| Process           | Expected                    | Actual (found/did/skipped) | Drift filed |
| Governance        | invariants enforced         | ...                        | ID / -      |
| Memory-sync       | memory <-> brain <-> Linear = 0 | ...                    | ...         |
| Process-sync      | chain green end-to-end      | ...                        | ...         |
| Documentation     | one source of truth, found  | ...                        | ...         |
| Tickets (queue)   | classified, no mis-lane     | gate: N violations         | ...         |

Signals: recurrence=<n> - new-drift=<n> - time-to-detect=<...>
Trend (vs last runs): recurrence up/down - drift-per-run up/down
Verdict: healthy-derivative | watch | ANDON
```
Rules: **expected-vs-actual, never a bare pass/fail.** One line per process. If it takes more than a
few minutes it is too heavy — cut it, don't skip it.

## 6. The gauge (persist + trend)
- **Persist** every readout to one durable run log (the sync run log).
- **Grade the slope, not the snapshot** — recurrence→0, drift-per-run↓, MTTD↓. A green run whose
  drift-per-run is climbing is *failing*, not passing.
- **Bound the log** — keep the last N runs inline; archive older to Linear history (churn control).

## 7. The outcome policy — green advances, red escalates (human on the loop, not in it)
On each run, after the pyramid + CCR + the brain's evaluation of the results:

- **Full green through every layer** → the brain is cleared to **continue the commit / merge process**
  without a human hand on each step. This is the purpose of the whole apparatus.
- **Any red — or any _indeterminate_** (a check that errored, didn't run, or can't be resolved) →
  **the brain pulls the andon and punts to the human for investigation. Fail-closed. Silence is not
  green.** An undetermined result is treated as red, never as pass.

Two rules govern *when* the brain may hold this authority:

1. **Stringency scales with authority.** A gate that only *advises* may be loose — a human catches
   its mistakes. A gate allowed to *merge* must be the strictest of all, because there is no human
   downstream to catch it. The more you trust the green, the more the green must be able to refuse.
2. **A gate earns merge authority; it is not assumed.** The brain may auto-advance to commit/merge
   **only through a gate that is un-gameable and born-red-proven** — derived not self-narrated,
   observed red on an injected failure, measurer separate from measured. This is a deliberate
   evolution of [[feedback-agent-never-controls-authorization]] ("the human controls every merge"):
   the brain *earns* the keys by holding a gate that cannot lie. Grant it **phased** — lowest-risk
   changes first, widening as the trend proves the gate. Until the gate is proven, the human holds
   the merge, and the outcome policy's "green" means "green, ready for a human to merge."

## 8. Prove it's alive (andon drill)
Once a cycle, inject a known drift (a mislabeled ticket, a stale doc, a removed guard) and confirm
the run goes red and punts. A gate never observed red — especially one that may auto-merge — is
decoration, and must not hold merge authority.

## 9. The rule that governs the rest
**Assess produces a graded register; it never applies changes.** Mutation is a separate phase behind
a gate (human, or a proven auto-merge gate per §7). The 5-loop CCR that produced this standard is the
worked example — it found the gaps and changed no code. See [[feedback-assess-first-decide-then-apply]].

## Provenance
Drafted 2026-09-07 from the governance thread that produced [[OCR_STANDARD_storyClassification]] +
the `/sync` skill. Composes the reconciliation loop, story-classification, CCR protocol, and kaizen
health doctrines; adds the per-run readout gauge (was missing) and the green-advances/red-escalates
outcome policy. Open for owner ratification: the outcome policy §7 (esp. the phased grant of merge
authority) and the readout row set §5.
