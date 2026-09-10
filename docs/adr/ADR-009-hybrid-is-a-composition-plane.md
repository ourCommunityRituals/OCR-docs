# ADR-009: The hybrid OSE+OW product is a composition plane (OurAirwaves + OurSharedMagnets), not a fused product

**Status:** Proposed
**Date:** 2026-09-09
**Deciders:** Matt (PO / Co-Architect convener)
**Scope:** Fleet-wide (product composition + deployment topology)
**Supersedes:** None
**Cross-refs:** ADR-008 (Consolidate OSE+OW workers into the hub monorepo — the *source-topology* half this ADR assumes and does not re-decide); ADR-002 (Identity-Profile-Keyed Invariants — the anon/identified boundary kept unfused); ADR-003 (Self-Checking Infrastructure — why each regime keeps its own gates); OSE-local ADR-010 (Templates = Breadth, Tiers = Depth — the rule deployment profiles obey); OSE-local ADR-017 (report-depth one-gate doctrine — the rule the seam invariant obeys)

---

## Context

We want a **hybrid build** that presents OurSharedEvents (OSE) and OurWKRP (OW)
as one deployed product experience, from where each repo is today (2026-09-09).
The prompting question was whether that hybrid should be a new combined
repository — an `OSE/OW` repo whose two products' source is merged.

Two things frame the answer:

1. **The two products' invariants are contradictory *by design*, and that
   contradiction is the product.** OSE is anonymous-first: its load-bearing,
   CI-gated invariants are two-DB isolation (`DB` = anonymous public surface,
   `FORMS_DB` = identified), a runtime-LLM-free hot path, and a cost metric that
   is aggregate-only / never-who. OW is identity-first (the named, non-anonymized
   counterpart). The anonymized ↔ identified boundary is **architectural**
   (ADR-002), not tidiness. A tree that fuses the two regimes forces every gate
   to ask "which regime am I in?" per path, whose only outcomes are **duplicate**
   the gate suites (they drift) or **weaken** them to a common denominator
   (the isolation guarantee — the whole point — is lost).

2. **Source co-location is already decided separately, and it is NOT a fusion.**
   ADR-008 (proposed) consolidates the OSE and OW *workers* into the hub
   monorepo as workspace packages **after** the launch window, explicitly
   *"keeping databases, workers, deployments, wrangler configs and the identity
   boundary strictly separate … two workers, two database pairs, two domains,
   two identity models."* So "one repo" for source is on the table — but as
   per-package isolation, never as a merged product. ADR-008 governs **where
   source lives**. It does **not** describe **how a hybrid runtime is assembled
   and shipped to a client**. That is the gap this ADR fills.

There is live evidence that the *how* matters and that copy-based convergence is
the wrong mechanism: `scripts/pw-guarded.sh` was propagated byte-identical from
OSE (PR #423 / OSE-852) into OW, OSE then evolved it twice (Gate 0b, OSE-1170;
Gate 0c, OSE-834), and OW's frozen copy never knew — the inverse drift OW-141's
integrity gate documents it cannot catch. ADR-008's Phase 0 ("spokes stop
vendoring shared packages and consume the hub's canonical copies") is the
structural fix; this ADR adopts the same principle for the composition plane.

We also already own the layers this needs. **OurAirwaves (OA)** is the
*deployment / white-label layer, client fork template* — operated as the
**custom backend suite**. **OurSharedMagnets (OSM)** is the *developer /
franchise layer — API and white-label support*, where solution architecting
(docs-as-code `.md`) and Bruno API contract tests already run on top of the
existing API testing.

## Decision

**The hybrid OSE+OW product is a *composition plane*, not a fused product.
OurAirwaves owns composition + deployment: it pins OSE and OW as versioned
artifacts, wires them into one custom backend, and enforces the cross-product
boundary at the seam. OurSharedMagnets owns the design + contract that the
composition is tested against. No new `OSE/OW` product that fuses the
anonymous/identified regimes is created; where the *source* physically lives is
ADR-008's decision (hub packages, boundaries preserved), orthogonal to this
one. Shared tooling converges via versioned `@ocr/*` packages consumed from the
hub, never by source propagation.**

This gives a four-layer product-line scaffold — **regimes own invariants; the
seam owns composition:**

```
OSM   → architect + contract-test   (md solution design + Bruno API contracts;
          │                           developer / franchise layer)
          │  contracts flow down
OSE ──┐   OW ──┐   ← two product backends; each OWNS its invariant regime
      └───┬────┘     (OSE anonymous / OW identified) — co-located per ADR-008,
          │           never fused
          │  pinned as versioned artifacts
OA    → compose + deploy            (uniform / custom / OW-template profiles;
                                     the cross-product seam invariant lives here)
```

- **OSM** defines and proves the contract: docs-as-code architecting and the
  Bruno collections that gate "what the composed API must do." It is the home of
  the cross-product / third-tier contract both products are tested against.
- **OSE and OW** implement the contract and hold their inviolable, CI-gated
  invariants. Unchanged by this ADR; co-located (or not) per ADR-008.
- **OA** composes the pinned artifacts and deploys them. Clients select a
  **deployment profile — uniform, custom, or OW-template-specific (DJ page,
  artist page, venue page, …)**. Per OSE-local ADR-010 a profile is a
  **breadth / presentation** choice: it never alters either product's invariant
  regime; templates never gate, tiers gate depth.
- **The one new invariant this creates** is the seam guarantee, owned by OA:
  *identified OW data never crosses onto the OSE anonymous surface.* It is a
  fresh third-tier assertion at the composition point — **not** a merge of the
  two products' invariants — and, per ADR-017's one-gate doctrine, it is
  enforced in exactly one place (the seam), never duplicated into either product.

**Answer to the prompting question:** No new merged `OSE/OW` repo. Source
topology is ADR-008's call; the hybrid is a composition owned by OA and
contracted by OSM; in neither case are the anonymous/identified regimes fused.
The fleet rule, shared with ADR-008, is: **co-locate freely; never fuse
invariant regimes.**

## Consequences

- **Each product keeps its own invariant regime and gate history intact** —
  whether the source sits in two spokes or one hub (ADR-008). No gate decides
  "which regime am I in"; no suite is duplicated or diluted.
- **Easier:** shipping a hybrid (OA pins + composes), onboarding client variants
  (deployment profiles are breadth/config), and reasoning about the
  anon/identified boundary (one seam invariant, one place).
- **Harder / net-new work:** OA gains composition machinery — artifact pinning,
  the gateway/routing, and the seam-invariant test. OSM hosts the cross-product
  Bruno contract. Both bounded.
- **Must be maintained:** the line between *tooling convergence* (allowed — via
  versioned `@ocr/*` packages consumed from the hub, per ADR-008 Phase 0) and
  *product-invariant convergence* (forbidden). Shared CI guards, `@ocr/ui`,
  `@ocr/flags`, the CCR harness ride packages; product invariants never leave
  their home package.
- **Retires an anti-pattern:** copy-propagation with sha-pinning (as used for
  `pw-guarded.sh`) is a stopgap, not the target. The target is hub-canonical
  `@ocr/*` consumption (ADR-008 Phase 0); the OW-141 pin is the small-scale
  lesson that motivates it.
- **Risks accepted:** OA becomes a real backend surface with its own release
  cadence and one invariant to keep green; a deployment profile misconfigured in
  OA is now a place the boundary *could* be violated — which is exactly why the
  seam invariant is mandatory and gated there.

## Open follow-ons (not decided here)

- Whether OA is literally the composition host or a distinct thin composition
  target consuming OA's fork-template — recommendation: OA, since it already is
  the deployment/fork-template layer. Either way it pins artifacts, never merges
  regimes.
- Promoting the seam guarantee (identified-never-on-anon-surface) into a
  machine-readable Brain invariant (`ocr-docs-brain/*.yaml`) so it gates the OA
  pipeline, per ADR-003.
- Standing up hub-canonical `@ocr/*` consumption to replace `pw-guarded.sh`
  copy-propagation (ADR-008 Phase 0), and re-propagating OSE's Gate 0b/0c into
  OW as a separate, Playwright-wiring-verified change (OW-141 boundary).
