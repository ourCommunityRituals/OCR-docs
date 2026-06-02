# ADR-003: Self-Checking Infrastructure — Invariants as the Core Framework

**Status:** Accepted — implementation in flight
**Date:** 2026-06-01
**Deciders:** Matt (Co-Architect convener)
**Supersedes:** None — co-equal with ADR-002, builds on ADR-001
**Cross-refs:** ADR-001 (Docs-as-Code Scaffold), ADR-002 (Identity-Profile-Keyed Invariants)

---

## Context

The OCR product line has grown an *implicit* invariant framework: thirteen
architectural invariants live in `ocr-docs-brain/architectural-invariants.yaml`;
a conformance check (`scripts/check_brain_contract.py`) parses them; every
product's CI is supposed to honor them; standards documents reference them by
number; agents (Red Team Agent, future onboarding agents) coordinate against
them.

That framework works — until it doesn't, in instructive ways:

- **Phantom invariants** — `OCR_STANDARD_brainEnforcementLocation.md`
  referenced "#13" before it was encoded; `OCR_STANDARD_mobileWorkability.md`
  references "#14" today, also unencoded; ADR-002 claims "#14" for its own
  proposals. Numbers get reserved before they're real.
- **Glob-presence-only conformance** — the check verifies a file matching the
  invariant's `test_file` glob exists somewhere. It does not verify the file
  lives in a canonical location, nor that any CI workflow actually invokes
  it. A guard never invoked is theater.
- **Standards propagation in name only** — `OCR_STANDARD_mobileWorkability.md`
  declares it propagates to every product's `.ocr-standards/`; today the
  propagator isn't verified to run, and there's no drift check on the
  receiving side.
- **Project descriptions name wrong invariant numbers** — OCR-H3 claims to
  "introduce Invariant #10" but #10 is `deprecation_lock`; OCR-RedTeamAgent
  claims to "implement Invariant #12" but #12 is
  `runner_pool_readiness_probe`. The numbers spread mis-attributions
  downstream.
- **No single banner** — the framework is implicit in six existing Linear
  Projects. Nobody can point at a single artifact and say *"this is what
  invariants ARE."*

The CCR review of the codebase-organization layer in 2026-05 held the brain
at HELD-80% pending exactly these fixes. The work to fix them was scattered
across Projects with no umbrella.

This ADR is the umbrella.

---

## Decision

**Architectural invariants in `ocr-docs-brain` are the core framework by
which the OCR infrastructure self-checks itself, layer by layer, with
continuous improvement.**

That is the commitment. The rest of this document operationalizes it.

### The six-layer model

| L | Name | Function |
| - | --- | --- |
| **L0** | Brain — canonical truth | `architectural-invariants.yaml`, `product-registry.yaml`, ADRs. Numbers assigned at write time; never reserved. Schema evolves via append-only `enrichment_history`. |
| **L1** | Conformance check — machinery | `check_brain_contract.py` resolves invariants **per surface** (per ADR-002), validates each `test_file` lives at canonical location AND is reachable from an active CI workflow, fails the build on drift. Has its own self-tests. |
| **L2** | Pyramid per product — proof per layer | Each product runs L0 static gates + L0 invariant specs at the canonical path + L1 integration + T3 Newman + T4 functional. Per-PR + push-to-main gating. |
| **L3** | Standards propagation — downstream cohesion | OCR-docs canonical `docs/standards/*.md` → vendored `.ocr-standards/*` in every product. Verified propagator runs on every canonical change; per-product drift check fails CI on divergence. |
| **L4** | Adversarial validation — continuous probing | Red Team Agent harness validates every invariant through contract-only briefings. Produces evidence per invariant per release, not testimony. |
| **L5** | Self-improvement loop — framework learns | Auto-drift tickets file themselves. Framework-readiness telemetry emits continuously. A documented onboarding flow exists for new products. A quarterly cadence drives lean → rich enrichment, phantom retrospective, and new-invariant proposals. |

### The six success criteria — "load-bearing, not theater"

The framework is load-bearing if and only if:

1. **Every invariant in the registry has a CI gate that actually runs** —
   not glob-presence-only, not unreachable from any workflow.
2. **Every product's vendored `.ocr-standards/` matches canonical** — no
   silent drift.
3. **A change that would violate an invariant fails CI before merge** —
   proved by self-tests on the conformance check.
4. **When something drifts, a Linear ticket files itself** — operators
   don't have to notice.
5. **A new product joins the framework by following a documented
   onboarding flow** — not by tribal knowledge.
6. **The framework's own health is measurable** — framework-readiness
   KPI emitted continuously.

The day all six are true is the day "invariants are the core framework"
stops being aspirational.

### Cadence

- **New invariants** — encoded at the YAML edit, never reserved in advance
  by a standards doc or ADR. The conformance check (L1) fails CI when a
  standards doc references a number not present in the registry.
- **Lean → rich** — driven by load-bearing weight, not registry order;
  selected at the quarterly review.
- **Phantom catches** — automatic; the L1 standards-doc scanner fails on
  detection.
- **Adversarial validation** — every release; Red Team Agent runs per
  invariant against deployed evidence.
- **Drift detection** — continuous; the L5 auto-ticket pipeline files
  Linear stories on every detection.
- **Framework-readiness review** — quarterly checkpoint; reviews the six
  success criteria against current telemetry; produces a short note in
  `OCR-docs/docs/framework-reviews/YYYY-QN.md`.

### Onboarding a new product

When a new OCR product joins (OurRecordStories, OurAirwaves, future
white-label instances), it is "in the framework" when:

1. Registered in `product-registry.yaml`.
2. Surfaces declared per ADR-002 (identity profile + surface role).
3. Vendored standards populated from canonical via the propagator.
4. Conformance check (`check_brain_contract.py`) reports clean for it.
5. Invariant pyramid wired — for every invariant whose per-surface
   resolution includes the new product, a test spec lives at the
   canonical path and is reachable from a real CI workflow.
6. Drift tickets auto-route to the new product's Linear team.

The documented runbook lives at `OCR-docs/docs/ONBOARD_NEW_PRODUCT.md`
(owned by the L5 Per-Product Framework Onboarding Epic).

---

## Consequences

### Positive

- **Single banner** for invariant work. Every Epic that touches the
  framework links to the Self-Checking Infrastructure Initiative; future
  agents see the umbrella before they see the parts.
- **Phantom-creation loophole closes** — the L1 conformance check catches
  unencoded number references at PR time, not at quarterly review.
- **New products inherit the framework by procedure**, not by Matt
  remembering to apply it.
- **Framework health becomes a number** — measurable, trended,
  reviewable.
- **The doctrine survives staff turnover** — read this ADR, read ADR-002,
  read the brain registry; you know how the system thinks about itself.

### Negative / trade-offs

- **More machinery to maintain** — the L1 check grows; the L5 telemetry
  emits; the auto-drift pipeline needs `LINEAR_API_KEY` rotation hygiene.
  The Brain Ops Project owns this maintenance load.
- **Cadence has a cost** — quarterly reviews take preparation time. If
  they get skipped, the doctrine drifts from practice; the ADR-003
  self-review in §6 of the cadence catches that.
- **Slows down "just add an invariant"** — the "numbers assigned at write
  time" rule prevents pre-naming, which feels like friction for an Epic
  author who wants to claim authority. That friction is the point;
  reserving numbers is what created the phantoms in the first place.

### Neutral / explicit

- This ADR does NOT decide which invariants exist. The registry is the
  source of truth for that; this ADR decides how the framework around
  the registry works.
- This ADR does NOT supersede ADR-002. ADR-002 is the data model layer
  (per-surface keys instead of `applies_to` lists); ADR-003 is the
  operational layer (how the framework is run, reviewed, measured).
  They are co-equal and mutually reinforcing.

---

## Implementation — Linear Initiative + Projects

**Initiative:** *Self-Checking Infrastructure — Invariants as the Core
Framework* (created 2026-06-01; first Linear Initiative in the
workspace).

**Projects under the Initiative:**

| Project | Layer | Purpose |
| --- | --- | --- |
| ADR-002 implementation — identity choice infrastructure | L0, L1 | Schema v2.0.0 + per-surface resolver |
| Brain invariant hygiene | L1, L2, L3 | Canonical test home; tightened conformance check; standards propagation; phantom #14 resolution |
| Brain Ops & Maintenance | L5 | Lean → rich enrichment; ops/rotations |
| OCR-Enforcement — Partial Invariant Enforcement Completion | L2 | Bring #2, #5, #7, #9 from partial → live |
| OCR-RedTeamAgent — Adversarial Validation Harness | L4 | Per-invariant adversarial validation |
| OCR-H3 — H3/DGGS Geospatial Substrate Adoption | L0 (enrichment of #2) | H3 indexing as the substrate of `hyperlocal_geo_resolution` |
| L5 — Auto-emit drift tickets | L5 | Detection → Linear ticket pipeline |
| L5 — Per-product framework onboarding | L5 | Turnkey new-product flow |
| L5 — Framework-readiness telemetry | L5 | The six KPIs, emitted, trended, dashboarded |
| L5 — Continuous-improvement cadence | L5 | Quarterly review heartbeat |

Each Project's own description carries its Layer assignment and links
back to this ADR.

---

## Validation

This ADR is itself subject to the framework it defines:

- **Layer assignment:** ADR-003 is L0 doctrine.
- **Conformance check:** the L1 check should (and the OCR-53 hardening
  will) verify that every Project linked to this Initiative declares a
  Layer in its description.
- **Quarterly review:** §"Cadence" point 6 — *"has the doctrine itself
  drifted from practice?"* — is the self-review hook.
- **Adversarial validation:** the Red Team Agent's contract-only briefings
  should include this ADR's six success criteria as a target — if an
  agent operating from this ADR alone cannot identify the L1 mechanism
  by name, the doctrine isn't load-bearing yet.

---

## Open questions

- **Who owns the propagator?** The mobileWorkability standard names it
  but doesn't link it. Tracked in Brain invariant hygiene Epic
  (OCR-75 — Cross-product standards propagation).
- **Initiative-vs-Project nomenclature.** Linear's terms (Initiative,
  Project, Issue) don't perfectly map to OCR's terms (Initiative, Epic,
  Feature, Story). For this ADR: Linear Initiative ≡ OCR Initiative,
  Linear Project ≡ OCR Epic, Linear parent Issue ≡ OCR Feature, Linear
  sub-Issue ≡ OCR Story. Documented here so future agents reading
  Project descriptions don't get confused.
- **Cross-product / cross-org scope.** OCR is the parent org; OSE / WKRP
  / OSM / etc. are products. The framework applies to all OCR products;
  whether external partners (e.g., white-label deployments via
  ourAirwaves) are in scope is a question for the first quarterly
  review.

---

## References

- ADR-001 — Docs-as-Code Scaffold (this repo's foundational decision)
- ADR-002 — Identity-Profile-Keyed Invariants (the L0 data model
  evolution)
- `ocr-docs-brain/architectural-invariants.yaml` — the registry
- `ocr-docs-brain/scripts/check_brain_contract.py` — the L1 conformance
  check
- `OCR-docs/docs/standards/OCR_STANDARD_brainEnforcementLocation.md` —
  the brain-location standard (encoded as invariant #13)
- `OCR-docs/docs/standards/OCR_STANDARD_mobileWorkability.md` — the
  surface-quality standard (phantom #14, pending OCR-74 resolution)
- Linear Initiative: *Self-Checking Infrastructure — Invariants as the
  Core Framework*
