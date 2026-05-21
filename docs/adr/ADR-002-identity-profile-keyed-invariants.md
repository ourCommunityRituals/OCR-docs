# ADR-002: Key architectural invariants to identity profile, not product-ID lists

**Status:** Proposed
**Date:** 2026-05-21
**Deciders:** mzdan + Co-Architect
**Scope:** Fleet-wide

> **Revision note (2026-05-21):** This ADR was hardened by a 5-loop CCR run
> (Critical · Conservative · Recursive) before being put forward. The first
> draft resolved a product to one identity contract via a single
> whole-product `identity_layer` field. CCR Loop 2 caught that WKRP has
> **two** identity surfaces at once — non-anonymous contributors *and* an
> anonymous Fist-of-Five QR-voting surface — so a single key would force
> WKRP wholly into the non-anonymous contract and leave its anonymous
> surface ungoverned, reproducing the very hole this ADR closes. The
> Decision below resolves contracts **per identity surface**, not per
> product. CCR also corrected the migration file list and removed an
> invariant rename. See References.

## Context

The governance brain (`OCR-docs/ocr-docs-brain/architectural-invariants.yaml`)
binds each architectural invariant to the products it governs through a
hand-maintained `applies_to` list of product IDs. Invariant #1 `anonymous_id`
carries `applies_to: [ose, osm]`; #10 `deprecation_lock` carries
`applies_to: [ose, osm, wkrp, oaw]`; and so on. `check_brain_contract.py`,
and four levels of the brain test pyramid, read that list to decide whether a
given invariant gates a given product.

This model was sufficient while every product shared one identity model. It
no longer is. The fleet now spans two end-user identity models — and, as the
CCR run found, a single product can present **both at once**:

- **Anonymous-identity surfaces** — OSE (`ourSharedEvents`), OSM
  (`ourSharedMagnets`), and WKRP's Fist-of-Five QR voting. The promise is
  "you're part of the group, anonymously": zero-PII, no correlation of a
  record back to a person; the only correlation key is an anonymous token.
- **Non-anonymous-identity surfaces** — WKRP (`ourWKRP`) contributors, OAW
  (`ourAirwaves`) DJs. The promise is the opposite by design: a person
  *deliberately* plants a flag — "I want my name on this" — authenticates,
  and their identity is on the record.

Identity is therefore a property of a **surface**, not of a whole product. A
product is a *set* of surfaces. OSE has one (anonymous). WKRP has two.

The trigger for this ADR is the WKRP brain-conformance work (ourWKRP PR #26,
OCR-docs branch `claude/wkrp-conformance-phase-gate`). Bringing WKRP under the
brain surfaced three structural failures in the `applies_to` model:

1. **The opt-out hole.** WKRP is correctly absent from `anonymous_id`'s
   `applies_to` list. But the brain has *no* positive identity invariant for
   non-anonymous surfaces. The way a non-anonymous product "passes" identity
   governance today is by being *absent from a list*. Absence-by-design and
   absence-by-omission are indistinguishable: a product that should be
   governed but was forgotten looks byte-identical to one correctly exempt.
   For the most load-bearing concern in the fleet — how a product handles a
   human's identity — silent omission is the worst failure mode, and the
   schema makes it the *default* one.

2. **One invariant cannot carry two correct answers.** The invariant *is* the
   anonymous rule. There is no way to express identity-correctness as a
   concern whose correct implementation *differs* by surface. Non-anonymous
   surfaces do not need a relaxed `anonymous_id`; they need a *different*
   contract — explicit opt-in, a consent record, bounded retention, honest
   copy.

3. **`applies_to` restates the registry, by hand, and drifts.**
   `product-registry.yaml` already declares identity per product. The
   invariant file re-encodes that fact, by hand, across a dozen `applies_to`
   lists. Every new product and every reclassification means editing N
   lists. The two files can — and will — silently disagree.

## Decision

**Architectural invariants are keyed to identity profile and resolved per
identity surface from the product registry — not to hand-maintained
product-ID lists.**

### 1. Invariant vs. contract

Separate the **invariant** (the named architectural concern — stable,
numbered, never renamed, never deleted) from the **contract** (the concrete,
testable rule — a `test_file` + an `enforces` statement). An invariant owns
one or more contracts.

### 2. A product declares its identity surfaces

`product-registry.yaml` replaces the scalar `identity_layer` with
`identity_surfaces` — a list of `{name, profile}`:

```yaml
# product-registry.yaml
- product_id: ose
  identity_surfaces:
    - name: public
      profile: anonymous
- product_id: wkrp
  identity_surfaces:
    - name: contributor       # the deliberate "plant a flag" opt-in
      profile: non-anonymous
    - name: tourney_voting    # Fist of Five — anonymous QR / button votes
      profile: anonymous
```

`profile` is `anonymous` or `non-anonymous`. Governance/CI repos (OCR-docs,
ocr-platform-tests) declare `identity_surfaces: []` — no end-user surface.
Pre-tech products declare `[]` until they have code.

**Load-bearing registry rule:** a product with application code
(`code_present` is not false) **must** declare a non-empty `identity_surfaces`.
Code with no declared surface fails conformance. This closes the pre-tech
transition gap — a product cannot acquire code while its identity model is
still unstated.

### 3. Every invariant declares a `scope`

| `scope`            | Meaning |
|--------------------|---------|
| `universal`        | One `contract`. Applies to every product that has code, regardless of identity. (`deprecation_lock`, `tenant_isolation`, the runner invariants.) |
| `profile-exclusive`| Declares one `profile` and one `contract`. Applies to a product's surfaces whose profile matches; resolves to `not-applicable` for the others — **computed**, not hand-written. |
| `identity-keyed`   | Declares a `contracts` map with an entry for **every** profile — a real contract or an explicit `{status: not-applicable, reason}`. For the rare invariant whose correct rule genuinely differs by profile. |

```yaml
# #1 — name UNCHANGED (invariant names are stable identity — see §5)
- id: 1
  name: anonymous_id
  title: Anonymous ID
  scope: profile-exclusive
  profile: anonymous
  contract:
    test_file: anonymous-id.invariant.spec.ts
    enforces: Zero-PII. No record correlates to identifiable PII; the only
      sanctioned correlation key is an anonymous token. (OSE realises this
      as the DB/FORMS_DB split + the ose_anon cookie.)

# #13 — NEW invariant, appended (never renumber; numbers assigned at write)
- id: 13
  name: non_anonymous_identity
  title: Non-Anonymous Identity
  scope: profile-exclusive
  profile: non-anonymous
  contract:
    test_file: non-anonymous-identity.invariant.spec.ts
    enforces: Identity is captured only behind an explicit opt-in gate
      ("plant a flag"). A consent record is persisted. PII retention is
      bounded. No surface copy claims anonymity.

# #10 — universal
- id: 10
  name: deprecation_lock
  scope: universal
  contract:
    test_file: deprecation-lock.invariant.spec.ts
    enforces: A removed runtime/flow MUST NOT be re-introduced.

# #8 — genuine identity-keyed: the rule itself differs by profile
- id: 8
  name: bounded_pii_retention
  scope: identity-keyed
  contracts:
    anonymous:
      test_file: pii-retention.invariant.spec.ts
      enforces: Opt-in PII has a finite TTL; daily lifecycle cron purges it.
    non-anonymous:
      test_file: pii-retention-identity.invariant.spec.ts
      enforces: The identity record is retained only for the consent term;
        revocation purges it within the declared window.
```

### 4. Membership is resolved per surface, never declared

The `applies_to` product-ID list is **removed**. The resolver
(`check_brain_contract.py`) computes, for every product:

1. Read `identity_surfaces` from `product-registry.yaml`.
2. For each invariant:
   - `universal` → the single contract applies (subject to `code_present`).
   - `profile-exclusive` / `identity-keyed` → for **each** surface, resolve
     the contract for `surface.profile`. A surface whose profile does not
     match a `profile-exclusive` invariant resolves to a computed
     `not-applicable`.
3. Record an explicit result for every `(surface × identity-scoped
   invariant)` pair.

### 5. The load-bearing rules

- **No silent skip.** The resolver must produce an explicit result — a
  contract to enforce or a `not-applicable` with a reason — for every
  `(surface × identity-scoped invariant)` pair. An unresolved pair, an
  unknown profile, or an `identity-keyed` map missing a profile fails CI.
  There is no list to be absent from; membership is exhaustively *computed*.
- **Invariant names are immutable.** `name` is referenced by
  `enrichment_history`, by PACT assertions, and by `*.invariant.spec.ts`
  filenames. Invariant #1 stays `anonymous_id`; the non-anonymous rule is the
  **new** invariant #13, not a rename of #1. Invariants evolve in place
  (gain `scope` + `contract`/`contracts`); they are never renumbered,
  renamed, or deleted — per the existing brain doctrine.

### 6. Identity profile is orthogonal to lifecycle phase

This decision does not touch `pipeline_present`, `code_present`, or
`pipeline_activation_phase`. Those answer *"is the mechanism built yet?"*
Identity profile answers *"which rule is correct once it is built?"* The two
axes stay independent.

## Alternatives Considered

### Alternative A: Keep `applies_to`; add WKRP/OAW to a new non-anonymous invariant

**Rejected because:** it patches today's products without fixing the
mechanism. The next product still depends on a human editing a list; absence
still equals exemption; the registry still drifts. It treats the symptom.

### Alternative B: Per-product invariant files

**Rejected because:** it explodes the brain into N copies, destroys
cross-product comparability, and guarantees universal concerns drift apart.

### Alternative C: Boolean governed/not-governed matrix per invariant per product

**Rejected because:** a boolean says "governed / not governed" — not *which
rule*. It cannot express that a non-anonymous surface needs a different,
differently-strict contract. It records the gap without closing it.

### Alternative D: Auto-derive `applies_to` from identity, keep one rule per invariant

**Rejected because:** it closes the drift failure only. One invariant still
cannot carry two correct answers; non-anonymous surfaces still resolve to no
identity contract, now automatically.

### Alternative E: Resolve from a single whole-product `identity_layer`

Key each product to one identity profile and resolve one contract from it.
*(This was this ADR's own first draft.)*

**Rejected because:** a product is not monolithic in identity. WKRP has a
non-anonymous contributor surface **and** an anonymous Fist-of-Five
QR-voting surface simultaneously. A single key forces WKRP wholly into the
non-anonymous contract and leaves its anonymous voting surface with **zero**
anonymous-identity governance — reproducing, for that surface, the exact
opt-out hole this ADR exists to close. A "mixed-surface carve-out" exception
was also considered and rejected: it is a special case bolted onto a wrong
model. Identity belongs to a *surface*; a product is a set of surfaces; a
single-surface product is the degenerate case. Per-surface resolution is the
principled model — caught by the 5-loop CCR run before this ADR shipped.

## Consequences

### Positive

- **The opt-out hole is closed per surface.** Every surface of every product
  resolves, on every run, to an explicit identity contract or a reasoned
  `not-applicable`. A forgotten product or surface fails CI; nothing passes
  by omission.
- **WKRP is governed correctly.** Its contributor surface resolves invariant
  #13 (opt-in gate, consent record, bounded retention); its Fist-of-Five
  voting surface resolves invariant #1 (anonymity). Both, not one.
- **Non-anonymous surfaces gain real identity governance for the first
  time** — WKRP's "plant a flag" moment and OAW's DJ identity become
  brain-enforced contracts with test files.
- **`product-registry.yaml` is the single source of truth for identity.**
  The invariant file consumes `identity_surfaces` and never restates it.
- **Reclassifying a product is a registry edit.** Add a surface, change a
  profile; every invariant re-resolves automatically.

### Negative

- **Registry schema change.** Scalar `identity_layer` becomes the
  `identity_surfaces` list. The `identity_layer_contract` conformance check
  must be rewritten to read surfaces.
- **One-time brain migration touching four pyramid levels** —
  `level2_schema.py`, `level5_boundary.py`, `level7_contract.py`,
  `level8_pact.py` — plus `check_brain_contract.py` and
  `architectural-invariants.yaml`. (See Implementation Notes — this list is
  the CCR-corrected full surface; the first draft named only two of the four
  levels.)
- **Net-new invariant + contracts.** Invariant #13 and its
  `non-anonymous-identity.invariant.spec.ts` are real engineering. WKRP also
  needs an anonymous-surface test for `tourney_voting`.
- **The #13 contract is Legal-gated.** Its "consent record" and retention
  terms are BIPA (Illinois) and COPPA adjacent. Per the agent operating
  model, Legal is human-only — #13's contract content must be Legal-reviewed
  before it is authored.

### Neutral

- Most of the 12 existing invariants become `universal`. Only
  identity-sensitive ones change: #1 becomes `profile-exclusive`, #13 is
  added, #8 (and possibly #7 `aggregate_only_reporting`) become
  `identity-keyed`.
- Invariant numbers and names are preserved. The change is to entry *shape*,
  tracked in `enrichment_history` as past lean→rich transitions were.

## Implementation Notes

Phased migration — each phase a focused PR:

- **Phase 1 — brain schema.** `architectural-invariants.yaml` →
  `schema_version: 2.0.0`: add `scope`, `profile`, `contract`/`contracts`;
  remove `applies_to`. `level2_schema.py`: drop `applies_to` from
  `INV_REQUIRED`, validate the new shape, require `identity-keyed` maps to
  enumerate every profile. Append an `enrichment_history` entry.
- **Phase 2 — resolver + pyramid.** `check_brain_contract.py`: per-surface
  resolver keyed on `identity_surfaces`. `level5_boundary.py`: replace the
  `applies_to`-ID validity check with a surface/profile validity check.
  `level7_contract.py`: rewrite CONTRACT 5 (currently asserts `applies_to`
  product IDs are valid) against surfaces. `level8_pact.py`: the membership
  assertions (`'ose' in applies_to`, `'wkrp' in applies_to`, …) resolve via
  profile/surface instead.
- **Phase 3 — registry + contracts.** Migrate every product's
  `identity_layer` to `identity_surfaces`. Author invariant #13 and
  `non-anonymous-identity.invariant.spec.ts` for WKRP and OAW; author WKRP's
  anonymous-surface test for `tourney_voting`. **Legal sign-off on the #13
  contract is a pre-condition of this phase.**
- **Phase 4 — PACT.** Confirm consumer-driven assertions resolve through the
  new model.

- **Affected repos:** OCR-docs (brain, scripts, four pyramid levels),
  ourWKRP, ourAirwaves. OSE/OSM: their `anonymous` contract is the current
  `anonymous_id` rule with the same `test_file` — unchanged.
- **Pre-condition:** Legal review of invariant #13's contract before Phase 3.
- **Review gate:** the Phase-3 commit that authors the #13 contract requires
  Legal sign-off.

## References

- **CCR run, 2026-05-21 (5-loop, Critical·Conservative·Recursive)** — caught
  the whole-product `identity_layer` flaw (Alternative E), the incomplete
  migration file list, an invariant rename, and the missing Legal gate. This
  revision is that run's output. CCR protocol:
  `OCR-docs/docs/standards/OCR_STANDARD_agentOperatingModel.md`.
- Trigger: WKRP brain-conformance work — ourWKRP PR #26, OCR-docs branch
  `claude/wkrp-conformance-phase-gate`.
- Builds on: ADR-001 — the `identity_layer` field and the anon/non-anon
  taxonomy referenced in ADR-001's Revisit Criteria.
- Brain contracts codifying enforcement: `architectural-invariants.yaml`,
  `scripts/check_brain_contract.py`, `tests/level2_schema.py`,
  `tests/level5_boundary.py`, `tests/level7_contract.py`,
  `tests/level8_pact.py`.
- Doctrine memory: `project_privacy_boundary.md` (WKRP non-anonymous opted-in;
  OSE anonymous; the individual chooses the tracking level);
  `project_fist_of_five.md` (the anonymous QR-voting surface).
- Standard: `OCR-docs/docs/standards/OCR_STANDARD_brainEnforcementLocation.md`.

## Revisit Criteria

- If a third end-user identity profile is introduced beyond `anonymous` /
  `non-anonymous`, the `profile` enum and the `identity-keyed` `contracts`
  map gain a key — confirm the resolver and `level2_schema.py` enumerate it.
- If a single surface needs more than a flat profile — e.g. per-region
  identity rules on one surface — the `{name, profile}` surface shape needs a
  richer profile object, warranting a superseding ADR.
- If the fleet ever collapses to a single identity model across every
  surface, the two-level invariant/contract model becomes overhead and could
  fold back to flat invariants.
