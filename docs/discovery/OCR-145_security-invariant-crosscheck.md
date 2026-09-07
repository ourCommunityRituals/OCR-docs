# OCR-145 — security-invariant cross-check of the classification labels

**Date:** 2026-09-06 · **Lens:** Dr. of Cyber Security (CCR S1) · **Owner:** platform

The CCR Security lens raised: a `spike`/`field` label on a **security enforcement gate** signals
"investigation, no urgency" and can silently de-prioritize it. This artifact confirms that did not
happen, and states the standing rule that keeps it from happening.

## Method

Intersect the 2026-09-06 classification labels (`spike`/`field`/`hybrid`, ~45 flagged of ~1,006) with
the security surface: tickets carrying `SEC`, and the known security **enforcement gates** (born-red
invariant tests, k-anon/covenant floors, integrity gates). For each, confirm (a) it is *correctly*
classed by deliverable, and (b) its priority/lane was **not changed**.

## Finding 1 — no security enforcement gate was labeled

The security *enforcement* gates — e.g. k-anon floor (OSE-683), depth-gate runtime enforcement
(OSE-714), privacy/equity red-team (OSE-662), the vacuous-gate / Gate-0b family — are **Actions** and
were **left unlabeled** (correctly: their deliverable is shipped enforcement code). None received a
`spike`/`field`/`hybrid` label. There is no gate whose apparent urgency a label could have lowered.

## Finding 2 — the security-*relevant* labeled tickets are correctly classed, priority intact

The labeled tickets that touch security are **decisions or real-world/legal items**, not enforcement
code — correctly classed, and every one **retains its original priority + `SEC` label** (no lane/priority
was changed by this exercise):

| Ticket | Label | Why correctly non-Action | Priority (unchanged) |
|--------|-------|--------------------------|----------------------|
| OSE-892 | spike | *verify* a rate-limit control functions (deliverable = a verification answer) | Medium |
| OSE-1175 | spike | per-flow security *ledger* artifact (a map, not enforcement) | High |
| OSE-1149 | spike | *decide* warehouse floor-at-read vs write (privacy schema decision) | Urgent |
| OSE-805 | spike | ADR *decision* on unit-of-publication + dominance rule | Urgent |
| OSE-715 | spike | PO *ratify* count policy (exact vs floored) | High |
| OSE-1151 | spike | invariant constitution reconciliation (drift *map* + decisions) | High |
| OSE-790 | hybrid | Dependabot *triage-decision* + remediation (the remediation half stays an Action) | Medium |
| OW-129 | hybrid | pseudonymity *decision* (safety-relevant) then conditional build | Urgent |
| OW-136 | hybrid | reconcile-which-is-canonical + one-line binding amendment | High |
| OCR-138 | hybrid | the #27 article-numbering *decision* + ratify (registry collision) | High |
| OCR-18 · OSE-356/357 | field | external legal opinion (BIPA/HIPAA) — real-world engagement | Urgent/High |

None is an enforcement gate; each keeps its urgency and `SEC` tag. A reader filtering `label:spike`
does **not** find a demoted security control — they find security-relevant *decisions* that still carry
Urgent/High priority.

## Standing rule (into the standard)

`OCR_STANDARD_storyClassification` §3 forbids labeling an enforcement gate as anything but its true
class, and the mislabel **tripwire** (once built) fires when a `spike`/`field` story sits at Urgent/High
without a linked Action — which is exactly the shape a mislabeled security gate would take. Priority is
never changed by classification; classification and prioritization are orthogonal axes.

## Residual

The tripwire is not yet built (tracked in OCR-145). Until it is, this cross-check is a point-in-time
manual assertion, not a standing gate — stated honestly.
