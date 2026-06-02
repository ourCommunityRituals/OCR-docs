# ADR-002: Key architectural invariants to identity profile, not product-ID lists

**Status:** Accepted — implementation pending
**Date:** 2026-05-21
**Deciders:** mzdan + Co-Architect
**Scope:** Fleet-wide

> **Provenance.** Drafted then hardened twice on 2026-05-21. A 5-loop CCR run
> (Critical · Conservative · Recursive) caught that the first draft keyed
> contracts to one whole-product field — which fails for any multi-surface
> product. Founder direction then expanded the model to the full three-rung
> identity choice — `identified` / `anonymous` / `untracked` — and named its
> purpose: **the invariant set is choice infrastructure.** See References.
>
> **Accepted 2026-05-22.** CCR-verified at ~96%; the founder delegated the
> acceptance call to the Co-Architect (the ADR's two deciders). The decision
> is committed — the four-phase migration in Implementation Notes is the
> roadmap, not a maybe. Status is `Accepted — implementation pending` rather
> than plain `Accepted` because the code, gates, and brain contracts are not
> yet live; the status promotes to `Accepted` when Phase 4 lands. Phase 3 is
> Legal-gated (the `explicit_identity` consent-record contract — BIPA / COPPA
> adjacent) and is not scheduled until that human review is complete.
>
> **Renumbered 2026-06-01.** Per this ADR's own "Invariant numbers are
> indicative — assigned at implementation per the brain's write-time
> numbering rule" note, the proposed invariant numbers shift: #14
> `explicit_identity` becomes #15 throughout this ADR; #15
> `exit_always_available` becomes #16. The number #14 was claimed by
> `mobile_workability` (encoded in `architectural-invariants.yaml`
> 2026-06-01 to resolve a phantom referenced by
> `OCR_STANDARD_mobileWorkability.md` since 2026-05-16 — second
> phantom-resolution after #13 brain_enforcement_location encoded
> 2026-05-21). Tracked in Linear OCR-74.

## Context

Today's market gives a person one real choice about their identity: hand over
personal data — opt-in-by-default — or don't use the product. Surveillance or
leave. The OCR product line exists to offer the genuine alternative: identity
is a **choice with three honest rungs, and the participant picks**.

For that promise to be real and not marketing copy, it must be **enforced in
code**. A value that CI does not gate is a slogan. The governance brain's
architectural invariants are how the choice is made load-bearing — this ADR is
about keying them so they actually carry that weight. This is the flag in the
sand, planted through code.

The mechanical trigger is the WKRP brain-conformance work (ourWKRP PR #26).
The brain currently binds each invariant to products via a hand-maintained
`applies_to` product-ID list, which has three structural failures:

1. **The opt-out hole.** The way a product "passes" an identity invariant it
   does not match is by being *absent from a list*. Absence-by-design and
   absence-by-omission are indistinguishable — a forgotten product looks
   identical to an exempt one. For identity, silent omission is the worst
   failure mode, and the schema makes it the default.
2. **One invariant cannot carry the choices.** The invariant *is* one rule.
   It cannot express that identity-correctness has *different correct
   answers* — one per rung of the choice ladder.
3. **`applies_to` restates the registry by hand and drifts.** The product
   registry already declares identity; `applies_to` re-encodes it across a
   dozen lists that can silently disagree.

And the `applies_to` model cannot express the actual shape of the line:
**identity is a property of a surface, not of a whole product.** A product is
a set of surfaces. ourWKRP has a non-anonymous *presenter* surface (the
contributor / DJ who plants a flag) and an anonymous *attendee* surface (the
Fist-of-Five QR voters) at the same time. ourSharedRecords and ourAirwaves
have the identical split. A single per-product key is structurally wrong.

## Decision

**Architectural invariants are keyed to identity profile and resolved per
identity surface from the product registry — and the invariant set is
designed, named, and enforced as choice infrastructure.**

### 1. Invariant vs. contract

Separate the **invariant** (the named architectural concern — stable,
numbered, never renamed, never deleted) from the **contract** (the concrete,
testable rule — a `test_file` + an `enforces` statement). An invariant owns
one or more contracts.

### 2. Three identity profiles — the choice ladder

A participant's identity is one of three profiles, most-exposed to least:

| Profile | Meaning |
|---|---|
| `identified` | The person's identity is on the record, captured **only** behind an explicit opt-in ("plant a flag"). A consent record is persisted; retention is bounded. |
| `anonymous` | The person is counted and correlated through an anonymous token — **never** linkable to PII. |
| `untracked` | No token, no record, no correlation. The system retains nothing about the participant. |

`untracked` is not a stronger `anonymous`: `anonymous` mints a correlation
token, `untracked` mints nothing. They are different rungs.

### 3. Surfaces — canonical roles, a set of offered profiles

A product declares its `identity_surfaces` in `product-registry.yaml`. Each
surface has a `role` and an `offers` set — the identity profiles a
participant may choose on that surface:

```yaml
# product-registry.yaml
- product_id: ose
  identity_surfaces:
    - role: attendee
      offers: [anonymous, untracked]
- product_id: ow                       # ourWKRP
  identity_surfaces:
    - role: presenter
      offers: [identified]
    - role: attendee
      offers: [anonymous, untracked]
- product_id: osm                      # ourSharedMagnets — Postman tooling
  identity_surfaces: []                # no participant surface; not identity-governed
```

`presenter` and `attendee` are the **canonical surface roles** — the line's
grammar. To present is to be identified (`offers: [identified]`); an attendee
chooses their rung (`offers: [anonymous, untracked]`). The role set is
extensible, but these two cover the fleet today.

### 4. Every invariant declares a `scope`

| `scope` | Meaning |
|---|---|
| `universal` | One `contract`. Applies to every product that has code. |
| `profile-exclusive` | One `profile` + one `contract`. Applies to surfaces that `offers` that profile; resolves to a computed `not-applicable` for the rest. |
| `identity-keyed` | A `contracts` map with an entry for **every** profile — a real contract or an explicit `{status: not-applicable, reason}`. |

### 5. Membership is resolved per surface, never declared

`applies_to` is **removed**. The resolver (`check_brain_contract.py`) computes,
for every product: read `identity_surfaces`; for each surface, for each profile
in `offers`, resolve the profile-scoped invariant's contract. A surface that
offers `[anonymous, untracked]` must satisfy *both* the `anonymous` contract
and whatever governs `untracked`. Membership is exhaustively computed — there
is no list to be absent from.

### 6. The invariant set as choice infrastructure

| # | Name | Scope | Enforces |
|---|---|---|---|
| 1 | `anonymous_id` *(exists)* | `profile-exclusive: anonymous` | Zero-PII; correlation only via an anonymous token. |
| 15 | `explicit_identity` *(new)* | `profile-exclusive: identified` | Identity captured only behind an explicit opt-in gate; consent record persisted; bounded retention; no surface copy claiming anonymity. |
| 16 | `exit_always_available` *(new)* | `universal` | **Every product MUST offer a participation path on the `untracked` profile, and that path MUST capture nothing** — no token minted, no identifying row written, no correlation key. CI fails the build if every surface of a product forces `identified` or `anonymous`. |

`untracked` has no dedicated `profile-exclusive` invariant: `anonymous` and
`identified` are *active* capture modes that each need a rich contract;
`untracked` is the *absence* of capture, enforced once — universally — as
**`exit_always_available`**. That invariant is the flag in the sand: the line
the market crosses by making capture mandatory, and the line OCR's code
refuses to cross. (Invariant numbers are indicative — assigned at
implementation per the brain's write-time numbering rule.)

### 7. Canonical vocabulary — consistent through documentation and code

These terms are **canonical** and appear verbatim everywhere — no synonyms:

- Profiles: `identified`, `anonymous`, `untracked` — never `non-anonymous`,
  `individual`, `personal`, `opt-out`, `ghost`.
- Surface roles: `presenter`, `attendee`.
- The model's name: **choice infrastructure**.

They must read identically in `product-registry.yaml`,
`architectural-invariants.yaml`, `check_brain_contract.py`, every
`*.invariant.spec.ts` filename and `describe` block, and each product's
`CLAUDE.md`. Documentation and code share one vocabulary; drift in language is
drift, and the brain exists to stop drift.

### 8. The load-bearing rules

- **No silent skip.** The resolver produces an explicit result — a contract to
  enforce or a reasoned `not-applicable` — for every `(surface × offered
  profile × identity-scoped invariant)` triple. An unresolved triple, an
  unknown profile, or an `identity-keyed` map missing a profile fails CI.
- **Code implies surfaces.** A product with application code
  (`code_present` not false) must declare a non-empty `identity_surfaces`.
  Code with no declared surface fails conformance — closing the pre-tech
  transition gap.
- **Invariant names are immutable.** `name` is referenced by
  `enrichment_history`, PACT assertions, and `*.invariant.spec.ts` filenames.
  Invariant #1 stays `anonymous_id`; the new rungs are appended as new
  invariants, never renames.

### 9. Orthogonal to lifecycle phase

This decision does not touch `pipeline_present`, `code_present`, or
`pipeline_activation_phase` — those answer "is the mechanism built yet?"
Identity profile answers "which rung is correct once it is built?"

## Alternatives Considered

### Alternative A: Keep `applies_to`; add a new non-anonymous invariant

**Rejected because:** it patches today's products without fixing the mechanism
— absence still equals exemption, the registry still drifts, and it still
cannot express a three-rung choice.

### Alternative B: Per-product invariant files

**Rejected because:** it explodes the brain into N copies, destroys
cross-product comparability, and guarantees universal concerns drift apart.

### Alternative C: Boolean governed/not-governed matrix

**Rejected because:** a boolean says "governed / not" — not *which rung*. It
records the gap without closing it.

### Alternative D: Resolve from a single whole-product `identity_layer`

*(This ADR's first draft.)* **Rejected because:** a product is not monolithic
in identity. ourWKRP is presenter + attendee simultaneously; a single key
forces it wholly into one contract and leaves the other surface ungoverned —
reproducing the opt-out hole. Caught by the CCR run.

### Alternative E: A two-profile model (`identified` / `anonymous` only)

*(This ADR's second draft.)* **Rejected because:** it omits `untracked` — and
`untracked` is the thesis. A model with only "tracked one way or tracked
another way" is not choice infrastructure; it is the market's menu with two
items instead of one. The third rung, and `exit_always_available` enforcing
it, are the point.

## Consequences

### Positive

- **Choice infrastructure becomes load-bearing.** The three-rung choice is
  enforced by CI, not asserted by a privacy page. `exit_always_available`
  fails the build if any product makes capture mandatory.
- **The opt-out hole is closed per surface.** Every surface resolves, every
  run, to an explicit contract or a reasoned `not-applicable`.
- **The product line's real shape is expressible** — presenter/attendee
  hybrids (ourWKRP, ourSharedRecords, ourAirwaves) are first-class.
- **One source of truth.** `product-registry.yaml` `identity_surfaces` is
  authoritative; the invariant file consumes it and never restates it.
- **One vocabulary** across documentation and code (§7).

### Negative

- **Registry schema change.** Scalar `identity_layer` becomes the
  `identity_surfaces` list; `non-anonymous` → `identified`. The
  `identity_layer_contract` conformance check is rewritten to read surfaces.
- **Brain migration touches four pyramid levels** — `level2_schema.py`,
  `level5_boundary.py`, `level7_contract.py`, `level8_pact.py` — plus
  `check_brain_contract.py` and `architectural-invariants.yaml`.
- **Net-new invariants + contracts.** #15 `explicit_identity` and #16
  `exit_always_available`, each with a `*.invariant.spec.ts` per product, are
  real engineering.
- **#15 is Legal-gated.** Its consent-record and retention terms are BIPA
  (Illinois) and COPPA adjacent. Legal is human-only in the operating model —
  #15's contract content must be Legal-reviewed before it is authored.

### Neutral

- Most of the 14 existing invariants become `universal`; only #1 changes shape
  (`profile-exclusive`), and #15/#16 are appended. Numbers and names preserved.
- ourSharedMagnets (Postman tooling), OCR-docs, and ocr-platform-tests declare
  `identity_surfaces: []` — not identity-governed. OurOpenTable and
  OurSharedPulse are shelved/pre-tech; surfaces deferred until they have code.

## Implementation Notes

Phased migration — each phase a focused PR:

- **Phase 1 — brain schema.** `architectural-invariants.yaml` →
  `schema_version: 2.0.0`: add `scope`, `profile`, `contract`/`contracts`;
  remove `applies_to`. `level2_schema.py`: drop `applies_to` from
  `INV_REQUIRED`, validate the new shape, require `identity-keyed` maps to
  enumerate every profile. Append an `enrichment_history` entry.
- **Phase 2 — resolver + pyramid.** `check_brain_contract.py`: per-surface,
  per-offered-profile resolver. `level5_boundary.py` + `level7_contract.py`:
  replace the `applies_to`-ID checks with surface/profile validity checks.
  `level8_pact.py`: membership assertions resolve via profile/surface.
- **Phase 3 — registry + contracts.** Migrate `identity_layer` →
  `identity_surfaces` for every product (map below). Author #15
  `explicit_identity` and #16 `exit_always_available` and their
  `*.invariant.spec.ts` for each governed product. **Legal sign-off on the
  #15 contract is a pre-condition of this phase.**
- **Phase 4 — PACT.** Confirm consumer-driven assertions resolve through the
  new model.

Product map → registry `identity_surfaces`:

| Product | Surfaces |
|---|---|
| ourSharedEvents | attendee |
| ourWKRP · ourSharedRecords · ourAirwaves | presenter + attendee |
| OurSharedGames | attendee *(currently defaults to the anonymous model)* |
| ourSharedMagnets | none — Postman tooling, not identity-governed |
| OurOpenTable · OurSharedPulse | shelved / pre-tech — deferred until they have code |

- **Pre-condition:** Legal review of invariant #15's contract before Phase 3.
- **Review gate:** the Phase-3 commit authoring the #15 contract requires
  Legal sign-off.

## References

- **Founder direction, 2026-05-21** — the three-rung choice ladder
  (`identified` / `anonymous` / `untracked`), the choice-infrastructure
  framing, the presenter/attendee product map, and the doc↔code vocabulary
  mandate.
- **CCR run, 2026-05-21 (5-loop)** — caught the whole-product `identity_layer`
  flaw (Alternative D), the incomplete migration file list, an invariant
  rename, and the missing Legal gate. CCR protocol:
  `OCR-docs/docs/standards/OCR_STANDARD_agentOperatingModel.md`.
- Trigger: WKRP brain-conformance work — ourWKRP PR #26.
- Builds on: ADR-001 — the identity taxonomy in its Revisit Criteria.
- Brain contracts: `architectural-invariants.yaml`,
  `scripts/check_brain_contract.py`, `tests/level2_schema.py`,
  `tests/level5_boundary.py`, `tests/level7_contract.py`,
  `tests/level8_pact.py`.
- Doctrine memory: `project_privacy_boundary.md` ("the individual chooses the
  tracking level"); `project_fist_of_five.md` (the anonymous attendee surface).

## Revisit Criteria

- If a fourth identity rung is introduced, the `profile` enum and the
  `identity-keyed` `contracts` map gain a key — confirm the resolver and
  `level2_schema.py` enumerate it.
- If a surface needs more than a flat list of offered profiles — e.g.
  per-region rules on one surface — the surface shape needs enrichment,
  warranting a superseding ADR.
- If a new surface role beyond `presenter` / `attendee` recurs across
  products, canonicalise it in §3.
