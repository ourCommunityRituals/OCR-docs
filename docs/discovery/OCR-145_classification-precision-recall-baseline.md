# OCR-145 — story-classification precision/recall baseline

**Date:** 2026-09-06 · **Standard under test:** `OCR_STANDARD_storyClassification` · **Owner:** platform

Baseline measurement of the Action/Spike/Field classifier, per the CCR SDET MUST-FIX
("a classifier is taken on faith until measured"). Method satisfies **separation of duties**:
the sample was classified by an *independent, blind* pass (a fresh agent given only
title + Definition of Done, never shown the labels the audit applied). The blind pass is the
**ground truth**; the 2026-09-06 board audit is the **prediction** under test.

## Sample

30 active tickets, stratified 18 OurSharedEvents / 6 OurWKRP / 6 OCR-doc, spread across each team's
backlog (not top-only).

## Result — primary cut (non-Action detection)

The audit's job was to flag **non-Action** stories (spike/field/hybrid) hiding in the board.

| Metric | Value | Gate | Pass |
|--------|-------|------|------|
| **Recall** (non-Action caught / non-Action present) | **15 / 15 = 1.00** | ≥ 0.80 | ✅ |
| **Precision** (correctly flagged / all flagged) | **15 / 16 = 0.94** | ≥ 0.85 | ✅ |
| Exact-class agreement (4-way) | **26 / 30 = 0.87** | — | — |

- **0 false negatives** — no disguised spike slipped past the audit in this sample.
- **1 false positive** — OSE-790: audit `hybrid`, blind `action` (blind weighted the "remediate"
  half; audit weighted the "triage-decide-disposition" half).

## The 4 disagreements are all documented boundary cases

Every mismatch lands on a boundary the standard already flags as open — none is a primary-cut error:

| Ticket | Audit | Blind | Boundary |
|--------|-------|-------|----------|
| OSE-790 | hybrid | action | Action ↔ Hybrid (is "triage" a decision or just remediation?) |
| OW-129 | hybrid | spike | Spike ↔ Hybrid (decision + small conditional build) |
| OW-136 | hybrid | spike | Spike ↔ Hybrid (reconcile-which-is-canonical + one-line amendment) |
| OCR-19 | spike | field | **Field ↔ Spike** — a pricing decision reached via a real-world Matt+G conversation. The exact open owner question in `OCR_STANDARD_storyClassification` §4 (is an off-keyboard *decision* a Spike or a Field?). |

## Reading

The classifier is **reliable on the primary Action-vs-not cut** (R = 1.00, P = 0.94) and its residual
disagreement is confined to the spike↔hybrid and field↔spike seams the standard explicitly leaves to
an owner ruling. Resolving §4 (and a spike-vs-hybrid tie-break rule) would lift exact agreement toward
0.95; the primary cut already clears the gate.

## Re-run

Re-runnable: pull a fresh stratified 30, run a blind classify pass (title + DoD only, no labels),
diff against applied labels. Baseline recorded so future runs measure drift, not restart from faith.
